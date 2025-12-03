# SA BFORBANK Webank iOS - Reporting Pipeline

Pipeline automatisé Adjust → Google Sheets

## Installation
```bash
pip3 install -r requirements.txt
```

## Utilisation
```bash
python3 adjust_to_gsheet.py
```

## Automatisation
```bash
chmod +x run_daily.sh
crontab -e
# Ajouter : 0 6 * * * /Users/lucmonteil/Downloads/adjust_pipeline/run_daily.sh
```
