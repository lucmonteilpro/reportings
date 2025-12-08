#!/usr/bin/env python3
"""
ADJUST LALALAB PIPELINE - VERSION REFACTORISÉE SIMPLIFIÉE
Push quotidien intelligent + Update revenues optionnel

Usage:
  python3 adjust_lalalab_simple.py                    # Push quotidien (hier)
  python3 adjust_lalalab_simple.py --date 2025-12-01  # Push date spécifique
  python3 adjust_lalalab_simple.py --update-revenues  # Update revenues 30j
"""

import pandas as pd
import re
import json
from datetime import date, timedelta
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import argparse

from adjust_to_gsheet import (
    get_gspread_client,
    pull_from_adjust,
    transform_data,
    ADJUST_API_TOKEN
)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_SHEET_ID = "1-929N5tQOPWIrT9ocitxQFpD_ijAhL7WshgOyYrkQhI"
CONFIG_SHEET_NAME = "custom CPI"

# =============================================================================
# UTILITAIRES
# =============================================================================

def extract_sheet_id_from_url(url: str) -> str:
    """Extrait le sheet_id depuis une URL Google Sheets"""
    if pd.isna(url) or url == "":
        return None
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None


def parse_custom_cpi(cpi_str: str) -> dict:
    """Parse la colonne custom_cpi"""
    if pd.isna(cpi_str) or cpi_str == "" or cpi_str == "{}":
        return {}
    try:
        return json.loads(cpi_str.replace("'", '"'))
    except Exception as e:
        print(f"⚠️  Erreur parsing custom_cpi: {e}")
        return {}


def load_lalalab_config(gc: gspread.Client, client_name: str) -> dict:
    """
    Charge la config Lalalab depuis le Google Sheet
    
    Args:
        client_name: "Android" ou "ios" pour filtrer le bon client
    """
    print(f"📥 Chargement config Lalalab {client_name}...")
    
    wks = gc.open_by_key(CONFIG_SHEET_ID)
    sheet = wks.worksheet(CONFIG_SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Filtre le client spécifique
    client_df = df[df['client'].str.contains(f'Lalalab.*{client_name}', case=False, na=False)]
    
    if len(client_df) == 0:
        raise ValueError(f"Client Lalalab {client_name} introuvable dans le config sheet")
    
    row = client_df.iloc[0]
    
    # Trouve l'URL du Google Sheet de données
    sheet_url_col = None
    for col in row.index:
        if isinstance(row[col], str) and 'docs.google.com/spreadsheets' in row[col]:
            sheet_url_col = col
            break
    
    if not sheet_url_col:
        raise ValueError(f"URL Google Sheet introuvable pour {client_name}")
    
    sheet_id = extract_sheet_id_from_url(row[sheet_url_col])
    
    config = {
        "client": row.get('client', 'Unknown'),
        "api_token": row.get('api_token', ''),
        "app_token": row.get('app_token', ''),
        "adjust_account_id": str(row.get('account_id', '')),
        "sheet_id": sheet_id,
        "sheet_name": row.get('sheet_name', 'raw_ios'),
        "custom_cpi": parse_custom_cpi(row.get('custom_cpi', '{}')),
        "countries": ['France', 'Germany', 'Italy'],
        "events": ['first purchase_events'],
        "agg_columns": [
            "App", "Month (date)", "Week (date)", "Day (date)",
            "Network (attribution)", "Country",
            "Campaign (attribution)", "Adgroup (attribution)", "Creative (attribution)"
        ]
    }
    
    print(f"✅ Config chargée: {config['client']}")
    return config


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def read_existing_sheet(config: dict, gc: gspread.Client) -> pd.DataFrame:
    """Lit le contenu actuel du Google Sheet"""
    try:
        wks = gc.open_by_key(config["sheet_id"])
        sheet = wks.worksheet(config["sheet_name"])
        df = get_as_dataframe(sheet, evaluate_formulas=True)
        
        # Supprime les lignes/colonnes vides
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if 'Day (date)' in df.columns:
            df['Day (date)'] = pd.to_datetime(df['Day (date)'])
        
        return df
    except Exception as e:
        print(f"⚠️  Sheet vide ou erreur lecture: {e}")
        return pd.DataFrame()


def smart_push_daily(df_new: pd.DataFrame, config: dict, gc: gspread.Client):
    """
    Push intelligent :
    - Si date existe déjà → Remplace UNIQUEMENT les revenues
    - Si date n'existe pas → Ajoute toute la ligne
    """
    print(f"📤 Push intelligent vers Google Sheet...")
    
    # 1. Lit le sheet existant
    df_existing = read_existing_sheet(config, gc)
    
    if df_existing.empty:
        # Sheet vide → push complet
        print("   📝 Sheet vide, push complet")
        wks = gc.open_by_key(config["sheet_id"])
        sheet = wks.worksheet(config["sheet_name"])
        sheet.clear()
        set_with_dataframe(sheet, df_new)
        print(f"✅ {len(df_new)} lignes ajoutées")
        return
    
    # 2. Convertir les dates (format YYYY-MM-DD sans heure)
    df_existing['Day (date)'] = pd.to_datetime(df_existing['Day (date)']).dt.strftime('%Y-%m-%d')
    df_new['Day (date)'] = pd.to_datetime(df_new['Day (date)']).dt.strftime('%Y-%m-%d')
    
    # 3. Clés de jointure (dimensions)
    join_keys = [
        'App', 'Month (date)', 'Week (date)', 'Day (date)',
        'Network (attribution)', 'Country',
        'Campaign (attribution)', 'Adgroup (attribution)', 'Creative (attribution)'
    ]
    join_keys = [k for k in join_keys if k in df_existing.columns and k in df_new.columns]
    
    # 4. Colonnes revenues à mettre à jour
    revenue_cols = ['0D All revenue total', '7D All revenue total', '30D All revenue total']
    revenue_cols = [c for c in revenue_cols if c in df_existing.columns and c in df_new.columns]
    
    print(f"   🔑 Clés de jointure: {', '.join(join_keys)}")
    print(f"   💰 Colonnes revenues: {', '.join(revenue_cols)}")
    
    # 5. Créer une clé unique pour le merge
    for df_temp in [df_existing, df_new]:
        df_temp['_merge_key'] = df_temp[join_keys].astype(str).agg('||'.join, axis=1)
    
    # 6. Identifier les lignes existantes vs nouvelles
    existing_keys = set(df_existing['_merge_key'])
    new_keys = set(df_new['_merge_key'])
    
    keys_to_update = existing_keys & new_keys  # Lignes à mettre à jour
    keys_to_add = new_keys - existing_keys      # Nouvelles lignes
    
    print(f"   🔄 Lignes à mettre à jour (revenues): {len(keys_to_update)}")
    print(f"   ➕ Nouvelles lignes à ajouter: {len(keys_to_add)}")
    
    # 7. Créer un dict des nouvelles revenues
    revenue_dict = {}
    for _, row in df_new.iterrows():
        key = row['_merge_key']
        revenue_dict[key] = {col: row[col] for col in revenue_cols}
    
    # 8. Mettre à jour les revenues dans df_existing
    updated_count = 0
    for idx, row in df_existing.iterrows():
        key = row['_merge_key']
        if key in keys_to_update:
            for col in revenue_cols:
                df_existing.at[idx, col] = revenue_dict[key][col]
            updated_count += 1
    
    print(f"   ✅ {updated_count} lignes mises à jour (revenues)")
    
    # 9. Ajouter les nouvelles lignes
    df_to_add = df_new[df_new['_merge_key'].isin(keys_to_add)].copy()
    
    if len(df_to_add) > 0:
        # Supprimer _merge_key avant d'ajouter
        df_to_add = df_to_add.drop('_merge_key', axis=1)
        df_existing = df_existing.drop('_merge_key', axis=1)
        
        df_final = pd.concat([df_existing, df_to_add], ignore_index=True)
        print(f"   ➕ {len(df_to_add)} nouvelles lignes ajoutées")
    else:
        df_existing = df_existing.drop('_merge_key', axis=1)
        df_final = df_existing
    
    # 10. Trier par date et push
    df_final = df_final.sort_values('Day (date)')
    
    wks = gc.open_by_key(config["sheet_id"])
    sheet = wks.worksheet(config["sheet_name"])
    sheet.clear()
    set_with_dataframe(sheet, df_final)
    
    print(f"✅ Push réussi: {len(df_final)} lignes totales")


def update_revenues_30d(config: dict, gc: gspread.Client):
    """
    Met à jour UNIQUEMENT les revenues pour les 30 derniers jours
    Ne touche à rien d'autre (CPI, Adspend, Installs, etc.)
    """
    print(f"💰 Update revenues 30 derniers jours...")
    
    # 1. Pull 30 derniers jours depuis Adjust
    today = date.today()
    begin_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"📥 Pull Adjust: {begin_date} → {end_date}")
    
    # Utilise l'API token du client
    import adjust_to_gsheet
    original_token = adjust_to_gsheet.ADJUST_API_TOKEN
    adjust_to_gsheet.ADJUST_API_TOKEN = config['api_token']
    
    df_new = pull_from_adjust(
        app_token=config["app_token"],
        begin_date=begin_date,
        end_date=end_date,
        adjust_account_id=config["adjust_account_id"],
        dimensions="app,month,week,day,country,network,campaign,creative,adgroup",
        include_revenue=True,
        events=config.get('events', [])
    )
    
    adjust_to_gsheet.ADJUST_API_TOKEN = original_token
    
    # 2. Transform (sans custom CPI pour ne pas recalculer Adspend)
    config_temp = config.copy()
    config_temp['custom_cpi'] = {}  # Skip CPI calculation
    df_new = transform_data(df_new, config_temp)
    
    print(f"   📊 {len(df_new)} lignes récupérées")
    
    # 3. Lit le sheet existant
    df_existing = read_existing_sheet(config, gc)
    
    if df_existing.empty:
        print("⚠️  Sheet vide, utilisez push quotidien d'abord")
        return
    
    # 4. Convertir les dates (format YYYY-MM-DD sans heure)
    df_existing['Day (date)'] = pd.to_datetime(df_existing['Day (date)']).dt.strftime('%Y-%m-%d')
    df_new['Day (date)'] = pd.to_datetime(df_new['Day (date)']).dt.strftime('%Y-%m-%d')
    
    # 5. Clés de jointure
    join_keys = [
        'App', 'Month (date)', 'Week (date)', 'Day (date)',
        'Network (attribution)', 'Country',
        'Campaign (attribution)', 'Adgroup (attribution)', 'Creative (attribution)'
    ]
    join_keys = [k for k in join_keys if k in df_existing.columns and k in df_new.columns]
    
    # 6. Colonnes revenues
    revenue_cols = ['0D All revenue total', '7D All revenue total', '30D All revenue total']
    revenue_cols = [c for c in revenue_cols if c in df_existing.columns and c in df_new.columns]
    
    print(f"   💰 Update colonnes: {', '.join(revenue_cols)}")
    
    # 7. Créer clés de merge
    for df_temp in [df_existing, df_new]:
        df_temp['_merge_key'] = df_temp[join_keys].astype(str).agg('||'.join, axis=1)
    
    # 8. Créer dict des revenues
    revenue_dict = {}
    for _, row in df_new.iterrows():
        key = row['_merge_key']
        revenue_dict[key] = {col: row[col] for col in revenue_cols}
    
    # 9. Update revenues dans df_existing
    updated_count = 0
    for idx, row in df_existing.iterrows():
        key = row['_merge_key']
        if key in revenue_dict:
            for col in revenue_cols:
                df_existing.at[idx, col] = revenue_dict[key][col]
            updated_count += 1
    
    print(f"   ✅ {updated_count} lignes mises à jour")
    
    # 10. Supprimer _merge_key et push
    df_existing = df_existing.drop('_merge_key', axis=1)
    df_existing = df_existing.sort_values('Day (date)')
    
    wks = gc.open_by_key(config["sheet_id"])
    sheet = wks.worksheet(config["sheet_name"])
    sheet.clear()
    set_with_dataframe(sheet, df_existing)
    
    print(f"✅ Update revenues réussi: {len(df_existing)} lignes totales")


def run_daily_pipeline(config: dict, target_date: str, gc: gspread.Client):
    """
    Pipeline quotidien : pull une date spécifique et push intelligent
    """
    print("\n" + "=" * 60)
    print(f"🚀 PIPELINE QUOTIDIEN: {config['client']}")
    print("=" * 60)
    print(f"📅 Date: {target_date}")
    
    try:
        # 1. Pull Adjust pour la date
        import adjust_to_gsheet
        original_token = adjust_to_gsheet.ADJUST_API_TOKEN
        adjust_to_gsheet.ADJUST_API_TOKEN = config['api_token']
        
        df = pull_from_adjust(
            app_token=config["app_token"],
            begin_date=target_date,
            end_date=target_date,
            adjust_account_id=config["adjust_account_id"],
            dimensions="app,month,week,day,country,network,campaign,creative,adgroup",
            include_revenue=True,
            events=config.get('events', [])
        )
        
        adjust_to_gsheet.ADJUST_API_TOKEN = original_token
        
        # 2. Transform avec CPI du config
        df = transform_data(df, config)
        
        print(f"   📊 {len(df)} lignes transformées")
        
        # Affiche revenues
        revenue_cols = [c for c in df.columns if 'revenue' in c.lower()]
        if revenue_cols:
            print("   💰 Revenues:")
            for col in revenue_cols:
                print(f"      {col}: {df[col].sum():,.2f}€")
        
        # 3. Smart push
        smart_push_daily(df, config, gc)
        
        print(f"✅ {config['client']} - SUCCÈS")
        return True
        
    except Exception as e:
        print(f"❌ {config['client']} - ÉCHEC: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Lalalab Adjust Pipeline Simplifié')
    parser.add_argument('--date', help='Date spécifique (YYYY-MM-DD), défaut=hier')
    parser.add_argument('--update-revenues', action='store_true', 
                       help='Update revenues 30 derniers jours')
    parser.add_argument('--client', default='ios', choices=['ios', 'android'],
                       help='Client à traiter (défaut: ios)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📸 ADJUST LALALAB PIPELINE SIMPLIFIÉ")
    print("=" * 60)
    
    # Authentification
    gc = get_gspread_client()
    if not gc:
        print("❌ Impossible de s'authentifier")
        return
    
    # Charge la config
    config = load_lalalab_config(gc, args.client)
    
    if args.update_revenues:
        # Mode update revenues
        print("💰 MODE: Update revenues 30 derniers jours")
        update_revenues_30d(config, gc)
    else:
        # Mode quotidien
        target_date = args.date or (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"�� MODE: Push quotidien")
        run_daily_pipeline(config, target_date, gc)
    
    print("\n🎉 Pipeline terminé !")


if __name__ == "__main__":
    main()
