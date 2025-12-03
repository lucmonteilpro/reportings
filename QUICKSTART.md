# ⚡ QUICKSTART - 15 MINUTES CHRONO

**Objectif** : Avoir le pipeline qui tourne en 15 minutes top chrono.

---

## ÉTAPE 1 : Installation (2 min)

```bash
cd ~/Downloads/adjust_pipeline
pip3 install -r requirements.txt
python3 validate.py
```

✅ Si tu vois "✅ TOUT EST PRÊT !" → Passe à l'étape 2  
❌ Si erreurs → Installe ce qui manque et relance

---

## ÉTAPE 2 : Service Account Google (7 min)

1. Va sur https://console.cloud.google.com
2. Nouveau projet : "Sharper Media Reporting"
3. Menu ☰ → APIs & Services → Library
4. Cherche "Google Sheets API" → Enable
5. Menu ☰ → APIs & Services → Credentials
6. CREATE CREDENTIALS → Service account
7. Nom : `sharper-reporting` → CREATE AND CONTINUE
8. Rôle : Editor → CONTINUE → DONE
9. Clique sur le service account créé → Onglet KEYS
10. ADD KEY → Create new key → JSON → CREATE
11. Renomme le fichier téléchargé : `service_account.json`
12. Place-le dans `adjust_pipeline/`

```bash
# Ouvre le fichier et copie l'email
cat service_account.json | grep client_email
```

13. Ouvre https://docs.google.com/spreadsheets/d/16xYLvkEsLsLLMN6gCXrgEg7ruPC50U9gsFy32ePBVb4
14. Share → Colle l'email → Editor → Share

---

## ÉTAPE 3 : Test (3 min)

```bash
# Test API Adjust
python3 test_adjust_api.py

# Si ça marche, lance le pipeline complet
python3 adjust_to_gsheet.py
```

Tu dois voir :
```
✅ Auth via Service Account
✅ Push réussi: https://...
```

---

## ÉTAPE 4 : Automatisation (3 min)

```bash
chmod +x run_daily.sh
mkdir -p logs

# Ajoute au cron
crontab -e
```

Colle cette ligne :
```
0 6 * * * ~/Downloads/adjust_pipeline/run_daily.sh
```

Sauvegarde : `Esc` puis `:wq` puis `Entrée`

---

## ✅ TERMINÉ !

Le script tournera automatiquement tous les jours à 6h.

**Pour vérifier :**
```bash
# Voir les logs
ls -la logs/
cat logs/$(date +%Y-%m-%d).log

# Forcer une exécution manuelle
python3 adjust_to_gsheet.py
```

---

**Problème ?** → Voir `GUIDE_COMPLET.md` section Troubleshooting
