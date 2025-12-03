#!/usr/bin/env python3
"""
ADJUST BFORBANK PIPELINE
Lance uniquement les clients Bforbank

Usage: python3 adjust_bforbank.py
"""

import pandas as pd
import re
import json
from datetime import date, timedelta
import gspread

# Importe toutes les fonctions depuis adjust_to_gsheet
from adjust_to_gsheet import (
    get_gspread_client,
    pull_from_adjust,
    transform_data,
    push_to_gsheet,
    ADJUST_API_TOKEN
)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_SHEET_ID = "1-929N5tQOPWIrT9ocitxQFpD_ijAhL7WshgOyYrkQhI"
CONFIG_SHEET_NAME = "custom CPI"

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def extract_sheet_id_from_url(url: str) -> str:
    """Extrait le sheet_id depuis une URL Google Sheets"""
    if pd.isna(url) or url == "":
        return None
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None


def parse_custom_cpi(cpi_str: str) -> dict:
    """Parse la colonne custom_cpi"""
    if pd.isna(cpi_str) or cpi_str == "" or cpi_str == "{}":
        return {}
    try:
        cpi_str = cpi_str.replace("'", '"')
        return json.loads(cpi_str)
    except Exception as e:
        print(f"⚠️  Erreur parsing custom_cpi: {cpi_str} → {e}")
        return {}


def parse_agg_columns(agg_str: str) -> list:
    """Parse la colonne agg_columns"""
    if pd.isna(agg_str) or agg_str == "":
        return []
    cols = [c.strip() for c in agg_str.split(',')]
    return cols


def load_bforbank_configs(gc: gspread.Client) -> list:
    """
    Charge uniquement les configurations Bforbank depuis le Google Sheet.
    
    Returns:
        Liste de dictionnaires de configuration pour les clients Bforbank
    """
    print("📥 Chargement configuration Bforbank depuis Google Sheet...")
    
    try:
        wks = gc.open_by_key(CONFIG_SHEET_ID)
        sheet = wks.worksheet(CONFIG_SHEET_NAME)
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Filtre uniquement les clients Bforbank
        bforbank_df = df[df['client'].str.contains('Bforbank', case=False, na=False)]
        
        # Filtre les clients actifs (avec api_token et app_token)
        active_df = bforbank_df[
            (bforbank_df['api_token'].notna()) & 
            (bforbank_df['api_token'] != '') &
            (bforbank_df['app_token'].notna()) & 
            (bforbank_df['app_token'] != '')
        ]
        
        print(f"✅ {len(active_df)} clients Bforbank actifs trouvés")
        
        # Construit les configs
        configs = []
        for idx, row in active_df.iterrows():
            # Trouve l'URL Google Sheet
            sheet_url_col = None
            for col in row.index:
                if isinstance(row[col], str) and 'docs.google.com/spreadsheets' in row[col]:
                    sheet_url_col = col
                    break
            
            if not sheet_url_col:
                print(f"⚠️  Pas d'URL pour {row.get('client')}, skip")
                continue
            
            sheet_id = extract_sheet_id_from_url(row[sheet_url_col])
            if not sheet_id:
                print(f"⚠️  Sheet ID invalide pour {row.get('client')}, skip")
                continue
            
            # Parse custom_cpi
            custom_cpi = parse_custom_cpi(row.get('custom_cpi', '{}'))
            
            # Parse agg_columns
            agg_columns_str = row.get('agg_columns', '')  # ← CORRIGÉ
            if agg_columns_str and pd.notna(agg_columns_str) and str(agg_columns_str).strip() != '':
                agg_columns = parse_agg_columns(agg_columns_str)
            else:
                # Colonnes par défaut Bforbank
                agg_columns = [
                    "Day (date)",
                    "Country",
                    "Network (attribution)",
                    "Campaign (attribution)",
                    "Adgroup (attribution)",
                    "Creative (attribution)"
                ]
            
            config = {
                "client": row.get('client', 'Unknown'),
                "api_token": row.get('api_token', ''),
                "app_token": row.get('app_token', ''),
                "adjust_account_id": str(row.get('account_id', '')),
                "sheet_id": sheet_id,
                "sheet_name": row.get('sheet_name', 'Sheet1'),
                "start_date": row.get('start_date', '2025-01-01'),
                "custom_cpi": custom_cpi,
                "agg_columns": agg_columns,
                "repush_all": False,
                "group_by_most_spending_campaign": False,
                "compute_ctr": False
            }
            
            configs.append(config)
        
        return configs
        
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        raise


def run_client_pipeline(config: dict, begin_date: str, end_date: str, gc: gspread.Client):
    """Lance le pipeline pour un client Bforbank"""
    client_name = config['client']
    
    print("\n" + "=" * 60)
    print(f"🚀 PIPELINE: {client_name}")
    print("=" * 60)
    print(f"📅 Période: {begin_date} → {end_date}")
    
    try:
        # 1. Pull Adjust
        dimensions = "day,country,network,campaign,creative,adgroup"
        include_revenue = False  # Bforbank n'a pas les revenues
        
        # Utilise l'API token spécifique
        import adjust_to_gsheet
        original_token = adjust_to_gsheet.ADJUST_API_TOKEN
        adjust_to_gsheet.ADJUST_API_TOKEN = config['api_token']
        
        df = pull_from_adjust(
            app_token=config["app_token"],
            begin_date=begin_date,
            end_date=end_date,
            adjust_account_id=config.get("adjust_account_id"),
            dimensions=dimensions,
            include_revenue=include_revenue
        )
        
        # Restaure le token
        adjust_to_gsheet.ADJUST_API_TOKEN = original_token
        
        # 2. Transform
        df = transform_data(df, config)
        
        # 3. Aperçu
        print("\n📊 Aperçu des données:")
        print(df.head(5).to_string())
        print(f"   Total: {len(df)} lignes")
        
        # 4. Push to GSheet
        push_to_gsheet(df, config, gc)
        
        # 5. Export CSV
        output_file = f"output_{client_name.replace(' ', '_')}_{end_date}.csv"
        df.to_csv(output_file, index=False)
        print(f"💾 Export local: {output_file}")
        
        print(f"✅ {client_name} - SUCCÈS")
        return True
        
    except Exception as e:
        print(f"❌ {client_name} - ÉCHEC: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal: lance uniquement les clients Bforbank"""
    print("=" * 60)
    print("🏦 ADJUST BFORBANK PIPELINE")
    print("=" * 60)
    
    # Dates: du 1er novembre 2025 à hier
    today = date.today()
    begin_date = "2025-11-01"
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"📅 Période: {begin_date} → {end_date}\n")
    
    # 1. Authentification Google
    gc = get_gspread_client()
    if not gc:
        print("❌ Impossible de s'authentifier à Google Sheets")
        return
    
    # 2. Charge les configs Bforbank
    configs = load_bforbank_configs(gc)
    
    if not configs:
        print("⚠️  Aucun client Bforbank actif trouvé")
        return
    
    print(f"\n📋 {len(configs)} clients Bforbank à traiter:")
    for config in configs:
        print(f"   - {config['client']}")
    
    # 3. Lance le pipeline pour chaque client
    results = {}
    
    for config in configs:
        client_name = config['client']
        success = run_client_pipeline(config, begin_date, end_date, gc)
        results[client_name] = success
    
    # 4. Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL")
    print("=" * 60)
    
    successes = sum(1 for v in results.values() if v)
    failures = sum(1 for v in results.values() if not v)
    
    print(f"✅ Succès: {successes}/{len(results)}")
    print(f"❌ Échecs: {failures}/{len(results)}")
    
    if failures > 0:
        print("\n❌ Clients en échec:")
        for client, success in results.items():
            if not success:
                print(f"   - {client}")
    
    print("\n🎉 Pipeline Bforbank terminé !")


if __name__ == "__main__":
    main()