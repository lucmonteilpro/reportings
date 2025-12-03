#!/usr/bin/env python3
"""
VALIDATION EXPRESS - Lance ce script en premier
Il vérifie que tout est en place avant de lancer le pipeline complet.
"""

import os
import sys

print("="*60)
print("🔍 VALIDATION DE L'INSTALLATION")
print("="*60)

errors = []
warnings = []
success = []

# 1. Vérifie Python
print("\n1️⃣  Python...")
try:
    import sys
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        success.append(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        errors.append(f"❌ Python version trop ancienne : {version.major}.{version.minor}")
except Exception as e:
    errors.append(f"❌ Python : {e}")

# 2. Vérifie les bibliothèques
print("2️⃣  Bibliothèques...")
required_libs = ['pandas', 'requests', 'gspread', 'google.auth']
for lib in required_libs:
    try:
        __import__(lib)
        success.append(f"✅ {lib}")
    except ImportError:
        errors.append(f"❌ {lib} manquant - Lance: pip3 install -r requirements.txt")

# 3. Vérifie les fichiers
print("3️⃣  Fichiers...")
required_files = ['adjust_to_gsheet.py', 'test_adjust_api.py', 'requirements.txt']
for file in required_files:
    if os.path.exists(file):
        success.append(f"✅ {file}")
    else:
        errors.append(f"❌ {file} manquant")

# 4. Vérifie le service account
print("4️⃣  Service Account Google...")
if os.path.exists('service_account.json'):
    try:
        import json
        with open('service_account.json') as f:
            sa = json.load(f)
        if 'client_email' in sa:
            success.append(f"✅ service_account.json (email: {sa['client_email']})")
            print(f"\n   📧 Email du service account: {sa['client_email']}")
            print(f"   ⚠️  As-tu partagé le Google Sheet avec cet email ?")
        else:
            errors.append("❌ service_account.json invalide")
    except Exception as e:
        errors.append(f"❌ service_account.json corrompu: {e}")
else:
    warnings.append("⚠️  service_account.json manquant - Suis le GUIDE_COMPLET.md Phase 2")

# 5. Affiche un résumé
print("\n" + "="*60)
print("📊 RÉSUMÉ")
print("="*60)

if errors:
    print("\n❌ ERREURS À CORRIGER:")
    for e in errors:
        print(f"   {e}")

if warnings:
    print("\n⚠️  AVERTISSEMENTS:")
    for w in warnings:
        print(f"   {w}")

if success:
    print("\n✅ OK:")
    for s in success:
        print(f"   {s}")

print("\n" + "="*60)

if errors:
    print("❌ Corrige les erreurs ci-dessus avant de continuer.")
    print("   Voir GUIDE_COMPLET.md pour les instructions.")
    sys.exit(1)
elif warnings:
    print("⚠️  Installation partiellement complète.")
    print("   Termine la Phase 2 du GUIDE_COMPLET.md (Service Account)")
    sys.exit(1)
else:
    print("✅ TOUT EST PRÊT !")
    print("\nProchaine étape:")
    print("   python3 test_adjust_api.py")
    sys.exit(0)
