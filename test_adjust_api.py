#!/usr/bin/env python3
"""
TEST RAPIDE - Vérifie que l'API Adjust fonctionne
Lance ce script sur ton Mac pour tester.
"""

import requests
import pandas as pd
import io

# ============================================
# CONFIGURATION
# ============================================
ADJUST_API_TOKEN = "ZsC1Hdhycvn5CDXCW6dc"  # ✅ Token BFORBANK qui fonctionne

# App Tokens
APP_TOKENS = {
    "BFORBANK": "30kmesrwq3nk",
    "LALALAB iOS": "vmu6fbf5yprt",
    "LALALAB Android": "qsgs7cex2f7k"
}

# ============================================
# TEST
# ============================================
def test_adjust_api(app_name: str, app_token: str):
    print(f"\n{'='*50}")
    print(f"🧪 TEST: {app_name}")
    print(f"   App Token: {app_token}")
    print(f"{'='*50}")
    
    params = {
        "date_period": "2025-11-01:2025-11-21",
        "dimensions": "day,country,network",
        "metrics": "installs,cost,all_revenue_total_d0,all_revenue_total_d7,all_revenue_total_d30,first purchase_events",
        "readable_names": "true",
        "utc_offset": "+02:00",
        "attribution_type": "all",
        "currency": "EUR",
        "app_token__in": app_token
    }
    
    headers = {
        "Authorization": f"Bearer {ADJUST_API_TOKEN}"
    }
    
    endpoint = "https://automate.adjust.com/reports-service/csv_report"
    
    print(f"\n📡 Appel API...")
    response = requests.get(endpoint, headers=headers, params=params)
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API OK!")
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(response.text))
        
        print(f"\n📊 Données reçues:")
        print(f"   Lignes: {len(df)}")
        print(f"   Colonnes: {list(df.columns)}")
        
        # Affiche les totaux
        print(f"\n💰 Totaux:")
        if 'Installs' in df.columns:
            print(f"   Installs: {df['Installs'].sum():,.0f}")
        if 'Cost' in df.columns:
            print(f"   Cost: {df['Cost'].sum():,.2f}€")
        
        # Cherche les colonnes revenue
        for col in df.columns:
            if 'revenue' in col.lower():
                print(f"   {col}: {df[col].sum():,.2f}€")
        
        # Sauvegarde CSV
        output_file = f"test_{app_name.replace(' ', '_')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n💾 Sauvegardé: {output_file}")
        
        return df
    else:
        print(f"❌ ERREUR!")
        print(response.text)
        return None


if __name__ == "__main__":
    print("🚀 TEST API ADJUST")
    print("=" * 50)
    
    # Test BFORBANK
    df = test_adjust_api("BFORBANK", APP_TOKENS["BFORBANK"])
    
    if df is not None:
        print("\n\n📋 APERÇU DES DONNÉES:")
        print(df.head(10).to_string())
