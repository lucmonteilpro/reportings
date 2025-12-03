#!/usr/bin/env python3
"""
ADJUST → GOOGLE SHEETS PIPELINE
Script standalone pour Sharper Media

Auteur: Refactorisé pour reprise en main
Date: Novembre 2025
"""

import pandas as pd
import requests
import io
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import gspread
from gspread_dataframe import set_with_dataframe
import os
import pickle
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

ADJUST_API_TOKEN = "KmP1b4iXsW6YSWJxN43g"  # ✅ Token SA BFORBANK qui fonctionne

# Scopes pour Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Configuration SA BFORBANK / WEBANK iOS
BFORBANK_CONFIG = {
    "client": "SA BFORBANK Webank iOS",
    "app_token": "30kmesrwq3nk",  # ✅ App Token Webank iOS
    "adjust_account_id": "29151",  # ✅ Account ID SA BFORBANK - OBLIGATOIRE
    "sheet_id": "1ytoAiVBYn2QkqbiAAVnDicJCbjQLBM2aRZiTPo-dH8k",  # ✅ Google Sheet
    "sheet_name": "raw_ios",  # ✅ Nom de l'onglet
    "start_date": "2025-01-01",
    "custom_cpi": {},  # Pas de custom CPI - pas de cost disponible
    "agg_columns": [
        "Day (date)",
        "Country",
        "Network (attribution)",
        "Campaign (attribution)",
        "Adgroup (attribution)",
        "Creative (attribution)"
    ],
    "group_by_most_spending_campaign": False,
    "compute_ctr": False
}

# Configuration Lalalab Client Report iOS (pour plus tard)
LALALAB_IOS_CONFIG = {
    "client": "Lalalab Client Report ios",
    "app_token": "vmu6fbf5yprt",  # ✅ App Token confirmé depuis Adjust Dashboard
    "sheet_id": "16xYLvkEsLsLLMN6gCXrgEg7ruPC50U9gsFy32ePBVb4",
    "sheet_name": "ios",
    "start_date": "2025-01-01",
    "custom_cpi": {
        "France": 7.0,
        "Germany": 5.0
    },
    "agg_columns": [
        "App",
        "Month (date)",
        "Week (date)",
        "Day (date)",
        "Network (attribution)",
        "Country",
        "Campaign (attribution)",
        "Adgroup (attribution)",
        "Creative (attribution)"
    ],
    "group_by_most_spending_campaign": False,
    "compute_ctr": False
}


# =============================================================================
# FONCTIONS GOOGLE SHEETS AUTH
# =============================================================================

def get_google_creds():
    """
    Authentification Google.
    Essaie d'abord le Service Account, sinon OAuth.
    """
    creds = None
    
    # Option 1: Service Account (recommandé - c'est ce que ton tech utilise)
    service_account_file = 'service_account.json'
    if os.path.exists(service_account_file):
        from google.oauth2.service_account import Credentials as ServiceCredentials
        creds = ServiceCredentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES
        )
        print("✅ Auth via Service Account")
        return creds
    
    # Option 2: OAuth (fallback)
    token_file = 'token.pickle'
    
    # Vérifie si on a déjà des credentials sauvegardés
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # Si pas de credentials valides, on fait l'auth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Tu dois avoir un fichier credentials.json (voir README)
            if not os.path.exists('credentials.json'):
                print("❌ ERREUR: Aucun fichier d'authentification trouvé!")
                print("   Place soit 'service_account.json' (recommandé)")
                print("   soit 'credentials.json' (OAuth) dans ce dossier.")
                print("   Voir le README pour plus de détails.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Sauvegarde pour la prochaine fois
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Auth via OAuth")
    return creds


def get_gspread_client():
    """Retourne un client gspread authentifié."""
    creds = get_google_creds()
    if creds is None:
        return None
    return gspread.authorize(creds)


# =============================================================================
# FONCTIONS ADJUST
# =============================================================================

def pull_from_adjust(
    app_token: str,
    begin_date: str,
    end_date: str,
    adjust_account_id: str = None,
    dimensions: str = "day,country,network,campaign,creative,adgroup",
    metrics: str = "installs,clicks,impressions"  # ✅ Seulement les métriques auxquelles tu as accès
) -> pd.DataFrame:
    """
    Pull les données depuis l'API Adjust.
    
    Args:
        app_token: Token de l'app Adjust (ex: "30kmesrwq3nk")
        begin_date: Date de début (format YYYY-MM-DD)
        end_date: Date de fin (format YYYY-MM-DD)
        adjust_account_id: ID du compte Adjust (REQUIS pour certains comptes)
        dimensions: Dimensions à récupérer
        metrics: Métriques à récupérer
    
    Returns:
        DataFrame avec les données Adjust
    """
    print(f"📥 Pull Adjust: {begin_date} → {end_date}")
    
    params = {
        "date_period": f"{begin_date}:{end_date}",
        "dimensions": dimensions,
        "metrics": metrics,
        "readable_names": True,
        "utc_offset": "+02:00",
        "attribution_type": "all",
        "currency": "EUR",
        "app_token__in": app_token
    }
    
    # CRITIQUE : Ajouter l'account ID si fourni
    if adjust_account_id:
        params['adjust_account_id'] = adjust_account_id
        print(f"   Account ID: {adjust_account_id}")
    
    headers = {
        "Authorization": f"Bearer {ADJUST_API_TOKEN}"
    }
    
    endpoint = "https://automate.adjust.com/reports-service/csv_report"
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        print("✅ Données récupérées avec succès")
        df = pd.read_csv(io.StringIO(response.text))
        df = df.sort_values('Day (date)')
        print(f"   {len(df)} lignes récupérées")
        return df
    else:
        print(f"❌ Erreur API: {response.status_code}")
        print(response.text)
        raise ValueError(f"Failed to retrieve data: {response.status_code}")


# =============================================================================
# FONCTIONS DE TRANSFORMATION
# =============================================================================

def transform_data(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Applique les transformations sur les données.
    
    BUGS FIXES:
    - Colonnes revenue ajoutées à l'exclusion du groupby
    - Filtre installs > 0 corrigé pour tous les clients Lalalab
    """
    print("🔄 Transformation des données...")
    
    tmp = df.copy()
    client = config["client"]
    
    # Filtre sur Network = Sharper
    if "Network (attribution)" in tmp.columns:
        tmp = tmp[tmp["Network (attribution)"] == "Sharper"]
        print(f"   Filtré sur Sharper: {len(tmp)} lignes")
    
    # Filtre date de début
    if config.get("start_date"):
        tmp = tmp[pd.to_datetime(tmp["Day (date)"]) >= pd.to_datetime(config["start_date"])]
        print(f"   Filtré depuis {config['start_date']}: {len(tmp)} lignes")
    
    # =========================================================================
    # BUG FIX #1: Filtre installs > 0
    # Le code original excluait seulement "Lalalab" exact, pas les variantes
    # =========================================================================
    CLIENTS_SANS_FILTRE_INSTALLS = [
        "Showroomprive.com - Ventes privées",
        "Lalalab",
        "Lalalab Android", 
        "Lalalab Client Report Android",
        "Lalalab Client Report ios",
        "Bforbank"
    ]
    
    if client not in CLIENTS_SANS_FILTRE_INSTALLS:
        before_count = len(tmp)
        tmp = tmp[tmp["Installs"] > 0]
        print(f"   Filtre installs > 0: {before_count} → {len(tmp)} lignes")
    else:
        print(f"   ⚠️  Pas de filtre installs > 0 pour {client}")
        tmp["Impressions"] = tmp["Impressions"].fillna(0)
    
    # =========================================================================
    # BUG FIX #2: Groupby avec colonnes revenue exclues
    # Le code original n'excluait pas les colonnes revenue du groupby
    # =========================================================================
    if config.get("group_by_most_spending_campaign"):
        print("   Grouping by most spending campaign...")
        # [Code de groupby ici si nécessaire]
        pass
    
    # Agrégation finale
    if config.get("agg_columns"):
        # Colonnes numériques à sommer (pas à utiliser comme clés de groupby)
        NUMERIC_COLS_TO_SUM = [
            "Impressions", "Clicks", "Installs",
            "0D All Revenue", "7D All Revenue", "30D All Revenue",
            "all_revenue_total_d0", "all_revenue_total_d7", "all_revenue_total_d30"
        ]
        
        # Colonnes d'agrégation présentes dans le DataFrame
        agg_cols = [c for c in config["agg_columns"] if c in tmp.columns]
        
        # Colonnes numériques présentes
        numeric_cols = [c for c in NUMERIC_COLS_TO_SUM if c in tmp.columns]
        
        print(f"   Agrégation sur: {agg_cols}")
        print(f"   Somme de: {numeric_cols}")
        
        # Groupby et somme
        tmp = tmp.groupby(agg_cols, as_index=False)[numeric_cols].sum()
        print(f"   Après agrégation: {len(tmp)} lignes")
    
    return tmp


# =============================================================================
# FONCTION PUSH GOOGLE SHEETS
# =============================================================================

def push_to_gsheet(df: pd.DataFrame, config: dict, gc: gspread.Client) -> str:
    """
    Push les données vers Google Sheets.
    
    Args:
        df: DataFrame à pusher
        config: Configuration du client
        gc: Client gspread authentifié
    
    Returns:
        URL du sheet
    """
    print(f"📤 Push vers Google Sheets...")
    
    sheet_id = config["sheet_id"]
    sheet_name = config["sheet_name"]
    
    try:
        wks = gc.open_by_key(sheet_id)
        sheet = wks.worksheet(sheet_name)
        
        # Clear et push toutes les données (pour Lalalab avec d7/d30 revenue)
        sheet.clear()
        set_with_dataframe(sheet, df)
        
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(f"✅ Push réussi: {url}")
        return url
        
    except Exception as e:
        print(f"❌ Erreur push: {e}")
        raise


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def run_pipeline(config: dict, begin_date: str = None, end_date: str = None):
    """
    Exécute le pipeline complet pour un client.
    
    Args:
        config: Configuration du client
        begin_date: Date de début (défaut: 1er du mois en cours)
        end_date: Date de fin (défaut: aujourd'hui)
    """
    print("=" * 60)
    print(f"🚀 PIPELINE: {config['client']}")
    print("=" * 60)
    
    # Dates par défaut
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if begin_date is None:
        begin_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    
    print(f"📅 Période: {begin_date} → {end_date}")
    
    # 1. Pull Adjust
    df = pull_from_adjust(
        app_token=config["app_token"],
        begin_date=begin_date,
        end_date=end_date,
        adjust_account_id=config.get("adjust_account_id")  # Passe l'account ID si présent dans la config
    )
    
    # 2. Transform
    df = transform_data(df, config)
    
    # 3. Affiche un aperçu
    print("\n📊 Aperçu des données:")
    print(df.head(10).to_string())
    
    # Affiche les totaux revenue
    revenue_cols = [c for c in df.columns if 'revenue' in c.lower() or 'Revenue' in c]
    if revenue_cols:
        print("\n💰 Totaux Revenue:")
        for col in revenue_cols:
            print(f"   {col}: {df[col].sum():,.2f}€")
    
    # 4. Push to GSheet
    gc = get_gspread_client()
    if gc:
        push_to_gsheet(df, config, gc)
    
    # 5. Export CSV local (pour vérification)
    output_file = f"output_{config['client'].replace(' ', '_')}_{end_date}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Export local: {output_file}")
    
    return df


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # =========================================================================
    # CONFIGURATION DES DATES
    # =========================================================================
    # Option 1: Dates automatiques (recommandé pour le cron)
    # Récupère du 1er du mois jusqu'à hier
    from datetime import date, timedelta
    today = date.today()
    begin_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Option 2: Dates manuelles (décommente pour tester une période spécifique)
    # begin_date = "2025-11-01"
    # end_date = "2025-11-21"
    
    # =========================================================================
    # EXÉCUTION - BFORBANK
    # =========================================================================
    df = run_pipeline(
        config=BFORBANK_CONFIG,
        begin_date=begin_date,
        end_date=end_date
    )
    
    # Pour lancer Lalalab plus tard, décommente ci-dessous:
    # df = run_pipeline(
    #     config=LALALAB_IOS_CONFIG,
    #     begin_date=begin_date,
    #     end_date=end_date
    # )
