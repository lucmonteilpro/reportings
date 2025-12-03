#!/usr/bin/env python3
"""
ADJUST MULTI-CLIENTS PIPELINE
Lit la configuration depuis Google Sheet et lance le pipeline pour chaque client

Google Sheet Config: https://docs.google.com/spreadsheets/d/1-929N5tQOPWIrT9ocitxQFpD_ijAhL7WshgOyYrkQhI
"""

import pandas as pd
import requests
import io
import re
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread
from gspread_dataframe import set_with_dataframe
import os
import pickle

# Importe les fonctions depuis adjust_to_gsheet.py
from adjust_to_gsheet import (
    get_gspread_client,
    pull_from_adjust,
    transform_data,
    push_to_gsheet
)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_SHEET_ID = "1-929N5tQOPWIrT9ocitxQFpD_ijAhL7WshgOyYrkQhI"
CONFIG_SHEET_NAME = "custom CPI"  # Nom de l'onglet du Google Sheet config

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def extract_sheet_id_from_url(url: str) -> str:
    """
    Extrait le sheet_id depuis une URL Google Sheets.
    
    Exemples:
    https://docs.google.com/spreadsheets/d/1slh8klvy5KfgUGxJz7yLJ5YKZmRPBMe59ViqsGEOU_Q/edit?gid=0#gid=0
    → 1slh8klvy5KfgUGxJz7yLJ5YKZmRPBMe59ViqsGEOU_Q
    """
    if pd.isna(url) or url == "":
        return None
    
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None


def parse_custom_cpi(cpi_str: str) -> dict:
    """
    Parse la colonne custom_cpi depuis le format string du Google Sheet.
    
    Exemples:
    "{'France': 7.0, 'Germany': 5.0}" → {"France": 7.0, "Germany": 5.0}
    "{}" → {}
    "" → {}
    """
    if pd.isna(cpi_str) or cpi_str == "" or cpi_str == "{}":
        return {}
    
    try:
        # Remplace les quotes simples par doubles pour JSON
        cpi_str = cpi_str.replace("'", '"')
        return json.loads(cpi_str)
    except Exception as e:
        print(f"⚠️  Erreur parsing custom_cpi: {cpi_str} → {e}")
        return {}


def parse_agg_columns(agg_str: str) -> list:
    """
    Parse la colonne agg_columns depuis le format string du Google Sheet.
    
    Exemples:
    "App,Month (date),Week (date),Day (date)" → ["App", "Month (date)", "Week (date)", "Day (date)"]
    """
    if pd.isna(agg_str) or agg_str == "":
        return []
    
    # Split par virgules et strip les espaces
    cols = [c.strip() for c in agg_str.split(',')]
    return cols


def load_config_from_sheet(gc: gspread.Client) -> pd.DataFrame:
    """
    Charge la configuration depuis le Google Sheet.
    
    Returns:
        DataFrame avec les colonnes:
        - client
        - sheet_url (colonne C)
        - api_token
        - app_token
        - account_id
        - sheet_name
        - start_date
        - custom_cpi
        - force_currency
        - group_by_most_agg_columns
    """
    print("📥 Chargement de la configuration depuis Google Sheet...")
    
    try:
        wks = gc.open_by_key(CONFIG_SHEET_ID)
        sheet = wks.worksheet(CONFIG_SHEET_NAME)
        
        # Lit toutes les données
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        print(f"✅ Configuration chargée: {len(df)} clients trouvés")
        print(f"   Colonnes: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        raise


def build_client_config(row: pd.Series) -> dict:
    """
    Construit un dictionnaire de configuration pour un client
    depuis une ligne du Google Sheet.
    
    Args:
        row: Ligne du DataFrame de configuration
        
    Returns:
        dict compatible avec run_pipeline()
    """
    # Extrait le sheet_id depuis l'URL (colonne C ou colonne nommée différemment)
    # On cherche la colonne qui contient des URLs Google Sheets
    sheet_url_col = None
    for col in row.index:
        if isinstance(row[col], str) and 'docs.google.com/spreadsheets' in row[col]:
            sheet_url_col = col
            break
    
    if sheet_url_col is None:
        print(f"⚠️  Pas d'URL Google Sheet trouvée pour {row.get('client', 'Unknown')}")
        return None
    
    sheet_id = extract_sheet_id_from_url(row[sheet_url_col])
    if not sheet_id:
        print(f"⚠️  Impossible d'extraire sheet_id depuis {row[sheet_url_col]}")
        return None
    
    # Parse custom_cpi
    custom_cpi = parse_custom_cpi(row.get('custom_cpi', '{}'))
    
    # Parse agg_columns
    agg_columns_str = row.get('group_by_most_agg_columns', '')
    if agg_columns_str and agg_columns_str != '':
        agg_columns = parse_agg_columns(agg_columns_str)
    else:
        # Colonnes par défaut selon le client
        if 'Lalalab' in row.get('client', ''):
            agg_columns = [
                "App",
                "Month (date)",
                "Week (date)",
                "Day (date)",
                "Network (attribution)",
                "Country",
                "Campaign (attribution)",
                "Adgroup (attribution)",
                "Creative (attribution)"
            ]
        else:
            agg_columns = [
                "Day (date)",
                "Country",
                "Network (attribution)",
                "Campaign (attribution)",
                "Adgroup (attribution)",
                "Creative (attribution)"
            ]
    
    # Construit le dictionnaire de config
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
        "repush_all": 'Lalalab' in row.get('client', ''),  # Repush complet pour Lalalab
        "group_by_most_spending_campaign": False,
        "compute_ctr": False
    }
    
    return config


def run_client_pipeline(config: dict, begin_date: str, end_date: str, gc: gspread.Client):
    """
    Lance le pipeline pour un client spécifique.
    
    Args:
        config: Configuration du client
        begin_date: Date de début
        end_date: Date de fin
        gc: Client gspread authentifié
        
    Returns:
        True si succès, False si échec
    """
    client_name = config['client']
    
    print("\n" + "=" * 60)
    print(f"🚀 PIPELINE: {client_name}")
    print("=" * 60)
    print(f"📅 Période: {begin_date} → {end_date}")
    
    try:
        # 1. Pull Adjust
        include_revenue = "Lalalab" in client_name
        
        # Dimensions spécifiques pour LALALAB
        if "Lalalab" in client_name:
            dimensions = "app,month,week,day,country,network,campaign,creative,adgroup"
        else:
            dimensions = "day,country,network,campaign,creative,adgroup"
        
        # Utilise l'API token spécifique du client
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
        
        # Restaure le token original
        adjust_to_gsheet.ADJUST_API_TOKEN = original_token
        
        # 2. Transform
        df = transform_data(df, config)
        
        # 3. Affiche un aperçu
        print("\n📊 Aperçu des données:")
        print(df.head(5).to_string())
        print(f"   Total: {len(df)} lignes")
        
        # 4. Push to GSheet
        push_to_gsheet(df, config, gc)
        
        # 5. Export CSV local
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
    """
    Point d'entrée principal: lit la config et lance tous les clients.
    """
    print("=" * 60)
    print("🌐 ADJUST MULTI-CLIENTS PIPELINE")
    print("=" * 60)
    
    # Dates automatiques: du 1er novembre 2025 à hier
    from datetime import date, timedelta
    today = date.today()
    begin_date = "2025-11-01"  # ✅ Changé du 1er du mois au 1er novembre
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"📅 Période globale: {begin_date} → {end_date}\n")
    
    # 1. Authentification Google Sheets
    gc = get_gspread_client()
    if not gc:
        print("❌ Impossible de s'authentifier à Google Sheets")
        return
    
    # 2. Charge la configuration
    config_df = load_config_from_sheet(gc)
    
    # 3. Filtre les clients actifs (ceux qui ont un api_token et app_token)
    active_clients = config_df[
        (config_df['api_token'].notna()) & 
        (config_df['api_token'] != '') &
        (config_df['app_token'].notna()) & 
        (config_df['app_token'] != '')
    ]
    
    print(f"\n📋 Clients actifs: {len(active_clients)}")
    for idx, row in active_clients.iterrows():
        print(f"   - {row.get('client', 'Unknown')}")
    
    # 4. Lance le pipeline pour chaque client
    results = {}
    
    for idx, row in active_clients.iterrows():
        client_name = row.get('client', f'Client_{idx}')
        
        # Construit la config
        config = build_client_config(row)
        if not config:
            print(f"⚠️  Configuration invalide pour {client_name}, skip")
            results[client_name] = False
            continue
        
        # Lance le pipeline
        success = run_client_pipeline(config, begin_date, end_date, gc)
        results[client_name] = success
    
    # 5. Rapport final
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
    
    print("\n🎉 Pipeline multi-clients terminé !")


if __name__ == "__main__":
    main()