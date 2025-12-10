#!/usr/bin/env python3
"""
ADJUST FDJ LOTERIE PIPELINE
Push quotidien automatisé vers Google Sheets

Usage:
  python3 adjust_fdj_simple.py                    # Push hier
  python3 adjust_fdj_simple.py --date 2025-12-08  # Date spécifique
"""

import pandas as pd
from datetime import date, timedelta
import gspread
from gspread_dataframe import set_with_dataframe
import argparse

from adjust_to_gsheet import (
    get_gspread_client,
    pull_from_adjust,
    ADJUST_API_TOKEN
)

# =============================================================================
# CONFIGURATION FDJ
# =============================================================================
FDJ_CONFIG = {
    "client": "FDJ Loterie iOS",
    "app_token": "xyufp5gt730g",
    "store_id": "1222993561",
    "account_id": "259",  # ← ESSAIE avec l'account_id de Lalalab
    "sheet_id": "1vtEmMX6SvM5maojsTUOutDrCYPgzJl5gmFz6CZuvsxQ",
    "sheet_name": "raw_ios",
}

# Colonnes finales souhaitées (exactement comme dans l'API)
FDJ_COLUMNS = [
    "App",
    "Month (date)",
    "Week (date)", 
    "Day (date)",
    "Campaign name",
    "Ad name",
    "Ad spend",
    "Installs",
    "Clicks",
    "In-app revenue",
    "inscription_etape1_events",
    "inscription_etape2_events",
    "inscription_etape3_events",
    "inscription_etape5 (pi)_events",
    "inscription_etape6 (adresse)_events",
    "inscription_confirmation_events",
    "1er versement_events",
    "autre versement_events",
    "prise de jeu_events",
    "CPA",
    "Budget dépensé"
]

# Configuration CPA
FDJ_CPA = 27.0  # Euros


# =============================================================================
# TRANSFORMATION FDJ
# =============================================================================

def transform_fdj_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transformation simple pour FDJ
    """
    print("🔄 Transformation FDJ...")
    
    tmp = df.copy()
    
    # Mapping des colonnes Adjust vers colonnes FDJ
    column_mapping = {
        'Network (attribution)': 'Network',
        'Campaign (attribution)': 'Campaign name',
        'Creative (attribution)': 'Ad name',
        'Adspend': 'Ad spend',
        'In-app revenue': 'In-app revenue'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in tmp.columns:
            tmp.rename(columns={old_col: new_col}, inplace=True)
    
    # Garde uniquement les colonnes qui existent
    existing_cols = [col for col in FDJ_COLUMNS if col in tmp.columns]
    tmp = tmp[existing_cols]
    
    # Ajoute les colonnes calculées
    tmp['CPA'] = FDJ_CPA
    
    # Budget dépensé = CPA * inscription_confirmation_events
    if 'inscription_confirmation_events' in tmp.columns:
        tmp['Budget dépensé'] = tmp['CPA'] * tmp['inscription_confirmation_events']
    else:
        tmp['Budget dépensé'] = 0.0
    
    # Format dates sans timestamp
    for date_col in ['Day (date)', 'Week (date)', 'Month (date)']:
        if date_col in tmp.columns:
            tmp[date_col] = pd.to_datetime(tmp[date_col]).dt.strftime('%Y-%m-%d')
    
    print(f"   ✅ {len(tmp)} lignes transformées")
    
    # Aperçu
    if len(tmp) > 0:
        print(f"\n📊 Totaux:")
        if 'Installs' in tmp.columns:
            print(f"   📱 Installs: {tmp['Installs'].sum():,.0f}")
        if 'Clicks' in tmp.columns:
            print(f"   🖱️  Clicks: {tmp['Clicks'].sum():,.0f}")
        if 'Ad spend' in tmp.columns:
            print(f"   💸 Ad spend: {tmp['Ad spend'].sum():,.2f}€")
        if 'In-app revenue' in tmp.columns:
            print(f"   💰 Revenue: {tmp['In-app revenue'].sum():,.2f}€")
        if 'inscription_confirmation_events' in tmp.columns:
            print(f"   ✍️  Inscriptions confirmées: {tmp['inscription_confirmation_events'].sum():,.0f}")
        if 'prise de jeu_events' in tmp.columns:
            print(f"   🎲 Prises de jeu: {tmp['prise de jeu_events'].sum():,.0f}")
        if '1er versement_events' in tmp.columns:
            print(f"   💵 1er versement: {tmp['1er versement_events'].sum():,.0f}")
        if 'Budget dépensé' in tmp.columns:
            print(f"   💰 Budget dépensé (CPA×Inscriptions): {tmp['Budget dépensé'].sum():,.2f}€")
    
    return tmp


# =============================================================================
# SMART PUSH (COMME LALALAB)
# =============================================================================

def smart_push_fdj(df: pd.DataFrame, config: dict, gc: gspread.Client):
    """
    Push intelligent:
    - Si date existe déjà → écrase cette ligne
    - Si date n'existe pas → ajoute à la fin
    """
    print(f"📤 Push intelligent vers Google Sheet...")
    
    try:
        wks = gc.open_by_key(config["sheet_id"])
        sheet = wks.worksheet(config["sheet_name"])
        
        # Lit le sheet existant
        try:
            existing = pd.DataFrame(sheet.get_all_records())
            print(f"   📖 {len(existing)} lignes existantes")
        except:
            print(f"   📝 Sheet vide, push complet")
            existing = pd.DataFrame()
        
        if len(existing) == 0:
            # Sheet vide → push complet
            sheet.clear()
            set_with_dataframe(sheet, df)
            print(f"   ✅ {len(df)} lignes ajoutées")
        else:
            # Merge intelligent
            # Clés uniques: Day + Campaign name + Ad name
            key_cols = ['Day (date)', 'Campaign name', 'Ad name']
            
            # Vérifie que les colonnes clés existent
            if all(col in df.columns for col in key_cols):
                # Crée une clé composite
                df['_key'] = df[key_cols].astype(str).agg('_'.join, axis=1)
                existing['_key'] = existing[key_cols].astype(str).agg('_'.join, axis=1)
                
                # Supprime les lignes existantes qui matchent
                existing_clean = existing[~existing['_key'].isin(df['_key'])]
                
                # Combine
                result = pd.concat([existing_clean, df], ignore_index=True)
                
                # Retire la colonne temporaire
                result = result.drop(columns=['_key'])
                
                # Trie par date
                if 'Day (date)' in result.columns:
                    result = result.sort_values('Day (date)')
                
                # Push
                sheet.clear()
                set_with_dataframe(sheet, result)
                
                nb_updated = len(df[df['_key'].isin(existing['_key'])])
                nb_added = len(df) - nb_updated
                
                print(f"   🔄 {nb_updated} lignes mises à jour")
                print(f"   ➕ {nb_added} lignes ajoutées")
            else:
                # Fallback: append simple
                result = pd.concat([existing, df], ignore_index=True)
                sheet.clear()
                set_with_dataframe(sheet, result)
                print(f"   ➕ {len(df)} lignes ajoutées")
        
        url = f"https://docs.google.com/spreadsheets/d/{config['sheet_id']}"
        print(f"   ✅ Push réussi: {url}")
        
    except Exception as e:
        print(f"❌ Erreur push: {e}")
        raise


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def run_fdj_pipeline(target_date: str = None):
    """
    Lance le pipeline FDJ pour une date
    """
    print("=" * 60)
    print("🎰 FDJ LOTERIE PIPELINE")
    print("=" * 60)
    
    # Date par défaut = hier
    if target_date is None:
        target_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"📅 Date: {target_date}\n")
    
    try:
        # 1. Authentification
        gc = get_gspread_client()
        if not gc:
            print("❌ Impossible de s'authentifier")
            return False
        
        # 2. Pull Adjust
        print(f"📥 Pull Adjust: {target_date}")
        
        # Dimensions
        dimensions = "app,month,week,day,campaign,creative"
        
        # Métriques de base
        metrics = "installs,clicks,impressions,cost,revenue"
        
        # Récupère TOUS les événements (pas de filtre)
        df = pull_from_adjust(
            app_token=FDJ_CONFIG["app_token"],
            begin_date=target_date,
            end_date=target_date,
            adjust_account_id=FDJ_CONFIG.get("account_id"),  # Au lieu de None
            dimensions=dimensions,
            metrics=metrics,
            include_revenue=True,
            events=None,  # None = tous les événements
            store_id=FDJ_CONFIG["store_id"]  # ✅ Filtre iOS
        )
        
        if len(df) == 0:
            print("   ⚠️  Aucune donnée récupérée")
            return False
        
        print(f"   ✅ {len(df)} lignes récupérées")
        
        # 3. Transform
        df = transform_fdj_data(df)
        
        # 4. Push
        smart_push_fdj(df, FDJ_CONFIG, gc)
        
        print(f"\n✅ FDJ Pipeline - SUCCÈS")
        return True
        
    except Exception as e:
        print(f"\n❌ FDJ Pipeline - ÉCHEC: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='FDJ Adjust Pipeline')
    parser.add_argument('--date', help='Date spécifique (YYYY-MM-DD), défaut=hier')
    
    args = parser.parse_args()
    
    run_fdj_pipeline(target_date=args.date)
    
    print("\n🎉 Pipeline FDJ terminé !")


if __name__ == "__main__":
    main()