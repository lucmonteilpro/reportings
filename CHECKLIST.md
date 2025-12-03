# ✅ CHECKLIST - VALIDATION ÉTAPE PAR ÉTAPE

Coche chaque case au fur et à mesure.

## Installation
- [ ] Fichier `adjust_pipeline.zip` téléchargé et dézippé
- [ ] Terminal ouvert dans le dossier `adjust_pipeline/`
- [ ] Python 3 installé (`python3 --version` fonctionne)
- [ ] Dépendances installées (`pip3 install -r requirements.txt`)

## Service Account Google
- [ ] Projet Google Cloud créé (`Sharper Media Reporting`)
- [ ] Google Sheets API activée
- [ ] Service Account créé (`sharper-reporting`)
- [ ] Fichier JSON téléchargé et renommé en `service_account.json`
- [ ] Fichier `service_account.json` dans le dossier `adjust_pipeline/`
- [ ] Email du service account copié (format: `xxx@xxx.iam.gserviceaccount.com`)
- [ ] Google Sheet Lalalab partagé avec cet email en "Editor"

## Test API Adjust
- [ ] Commande `python3 test_adjust_api.py` lancée
- [ ] Message "✅ API OK!" affiché
- [ ] Fichier `test_LALALAB_iOS.csv` créé
- [ ] Revenues visibles dans le CSV (pas à 0)

## Push Google Sheets
- [ ] Lignes décommentées dans `adjust_to_gsheet.py` (section "Push to GSheet")
- [ ] Commande `python3 adjust_to_gsheet.py` lancée
- [ ] Message "✅ Auth via Service Account" affiché
- [ ] Message "✅ Push réussi" affiché
- [ ] Google Sheet mis à jour avec les nouvelles données
- [ ] Revenues correctes dans le Sheet

## Automatisation
- [ ] Script `run_daily.sh` créé
- [ ] Dossier `logs/` créé
- [ ] Dates automatiques ajoutées dans `adjust_to_gsheet.py`
- [ ] Cron configuré (`crontab -e`)
- [ ] Cron vérifié (`crontab -l`)
- [ ] Test manuel du script (`./run_daily.sh`)
- [ ] Log créé et lisible

---

## 🎯 QUAND TOUT EST COCHÉ

**Félicitations ! Tu es autonome.**

Le script tournera automatiquement tous les jours à 6h du matin.

Pour vérifier les logs :
```bash
ls -la ~/Downloads/adjust_pipeline/logs/
cat ~/Downloads/adjust_pipeline/logs/2025-11-28.log
```

Pour forcer une exécution manuelle :
```bash
cd ~/Downloads/adjust_pipeline
python3 adjust_to_gsheet.py
```
