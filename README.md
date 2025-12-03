# SA BFORBANK Webank iOS - Reporting Pipeline

Pipeline automatisé pour récupérer les données Adjust et les pousser vers Google Sheets.

## 🎯 Configuration

- **Compte Adjust**: SA BFORBANK (Account ID: 29151)
- **App**: Webank iOS (Token: 30kmesrwq3nk)
- **Métriques**: Installs, Clicks, Impressions
- **Filtres**: Network = Sharper, Installs > 0
- **Google Sheet**: [raw_ios](https://docs.google.com/spreadsheets/d/1ytoAiVBYn2QkqbiAAVnDicJCbjQLBM2aRZiTPo-dH8k)

## 📦 Installation
```bash
# Clone le repo
git clone https://github.com/lucmonteilpro/reportings.git
cd reportings

# Installe les dépendances
pip3 install -r requirements.txt

# Configure les credentials OAuth Google
# Place le fichier credentials.json téléchargé depuis Google Cloud Console
```

## 🚀 Utilisation

### Exécution manuelle
```bash
python3 adjust_to_gsheet.py
```

### Automatisation quotidienne (cron)
```bash
# Rendre le script exécutable
chmod +x run_daily.sh

# Ajouter au crontab
crontab -e

# Ajouter cette ligne :
0 6 * * * /Users/lucmonteil/Downloads/adjust_pipeline/run_daily.sh
```

## 📊 Logs

Les logs sont sauvegardés dans `logs/YYYY-MM-DD.log`
```bash
# Voir les logs du jour
cat logs/$(date +%Y-%m-%d).log
```

## 🔐 Sécurité

**IMPORTANT**: Les fichiers suivants contiennent des informations sensibles et ne doivent JAMAIS être commités :
- `credentials.json` (OAuth Google)
- `token.json` (Token généré après authentification)
- `service_account.json` (si utilisé)

Ces fichiers sont exclus via `.gitignore`.

## 🛠️ Développé par

Sharper Media - Luc Monteil
