# 🚀 GUIDE COMPLET - REPRISE EN MAIN TOTALE

**Objectif :** Tu seras autonome en 30 minutes chrono.

---

## ⚡ PHASE 1 : Installation (5 min)

### 1.1 Télécharge et dézippe

1. Télécharge `adjust_pipeline.zip`
2. Double-clic dessus pour dézapper
3. Ouvre Terminal
4. Navigue vers le dossier :
   ```bash
   cd ~/Downloads/adjust_pipeline
   ```

### 1.2 Installe Python et les dépendances

```bash
# Vérifie que Python 3 est installé
python3 --version

# Si pas installé, installe Homebrew puis Python
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# brew install python3

# Installe les bibliothèques nécessaires
pip3 install -r requirements.txt
```

**Attends que ça finisse** (1-2 minutes).

---

## 🔐 PHASE 2 : Créer ton Service Account Google (10 min)

### 2.1 Accède à Google Cloud Console

1. Va sur : https://console.cloud.google.com
2. Connecte-toi avec ton compte Google (celui qui a accès au Google Sheet Lalalab)

### 2.2 Crée un nouveau projet

1. Clique sur le menu déroulant en haut (à côté de "Google Cloud")
2. Clique "NEW PROJECT"
3. Nom du projet : `Sharper Media Reporting`
4. Clique "CREATE"
5. **Attends 30 secondes** que le projet soit créé
6. Sélectionne ce projet dans le menu déroulant

### 2.3 Active l'API Google Sheets

1. Dans le menu hamburger (☰) en haut à gauche
2. Va dans : **APIs & Services** > **Library**
3. Dans la barre de recherche, tape : `Google Sheets API`
4. Clique sur "Google Sheets API"
5. Clique le bouton bleu "ENABLE"
6. Attends 5 secondes

### 2.4 Crée le Service Account

1. Menu hamburger (☰) > **APIs & Services** > **Credentials**
2. En haut, clique "**+ CREATE CREDENTIALS**"
3. Sélectionne "**Service account**"
4. Remplis :
   - Service account name : `sharper-reporting`
   - Service account ID : (auto-généré)
5. Clique "CREATE AND CONTINUE"
6. Rôle : sélectionne "**Editor**" (tape "editor" dans la recherche)
7. Clique "CONTINUE"
8. Clique "DONE"

### 2.5 Télécharge le fichier JSON

1. Tu es maintenant dans la liste des credentials
2. Trouve ton service account `sharper-reporting@...`
3. Clique dessus
4. Va dans l'onglet "**KEYS**"
5. Clique "**ADD KEY**" > "Create new key"
6. Sélectionne "**JSON**"
7. Clique "CREATE"
8. Un fichier JSON se télécharge automatiquement

### 2.6 Installe le fichier JSON

1. Renomme le fichier téléchargé en : `service_account.json`
2. Déplace-le dans le dossier `adjust_pipeline/`
   ```bash
   # Si le fichier est dans Downloads
   mv ~/Downloads/sharper-media-reporting-*.json ~/Downloads/adjust_pipeline/service_account.json
   ```

### 2.7 Donne accès au Google Sheet

**TRÈS IMPORTANT** : Ouvre le fichier `service_account.json` et copie l'email dedans.
Il ressemble à : `sharper-reporting@sharper-media-reporting-xxxxx.iam.gserviceaccount.com`

Ensuite :
1. Ouvre le Google Sheet Lalalab : https://docs.google.com/spreadsheets/d/16xYLvkEsLsLLMN6gCXrgEg7ruPC50U9gsFy32ePBVb4
2. Clique "Share" (en haut à droite)
3. Colle l'email du service account
4. Donne-lui les droits "**Editor**"
5. Déselectionne "Notify people" (pas besoin)
6. Clique "Share"

✅ **C'est fait ! Le service account peut maintenant écrire dans ton Sheet.**

---

## 🧪 PHASE 3 : Premier test (2 min)

```bash
cd ~/Downloads/adjust_pipeline

# Test 1 : Vérifie que l'API Adjust fonctionne
python3 test_adjust_api.py
```

**Tu dois voir :**
```
🧪 TEST: LALALAB iOS
✅ API OK!
📊 Données reçues:
   Lignes: 63
   Colonnes: [...]
💰 Totaux:
   Installs: 3,456
   Cost: 15,234.56€
   all_revenue_total_d0: 5,355.76€
   all_revenue_total_d7: 7,120.23€
```

**Si ça marche :** ✅ Ton API Token Adjust est OK !

**Si erreur :** Copie-moi l'erreur exacte.

---

## 🚀 PHASE 4 : Push vers Google Sheets (5 min)

### 4.1 Active le push dans le script

Ouvre le fichier `adjust_to_gsheet.py` dans un éditeur (TextEdit, VS Code, Sublime...)

Trouve ces lignes (vers la ligne 240) :
```python
# 4. Push to GSheet (optionnel - décommente quand prêt)
# gc = get_gspread_client()
# if gc:
#     push_to_gsheet(df, config, gc)
```

Enlève les `#` pour avoir :
```python
# 4. Push to GSheet
gc = get_gspread_client()
if gc:
    push_to_gsheet(df, config, gc)
```

Sauvegarde le fichier.

### 4.2 Lance le pipeline complet

```bash
python3 adjust_to_gsheet.py
```

**Tu dois voir :**
```
🚀 PIPELINE: Lalalab Client Report ios
📅 Période: 2025-11-01 → 2025-11-21
📥 Pull Adjust: 2025-11-01 → 2025-11-21
✅ Données récupérées avec succès
   63 lignes récupérées
🔄 Transformation des données...
   Filtré sur Sharper: 63 lignes
   Custom CPI France: 7.0€
   Custom CPI Germany: 5.0€
   ⚠️  Pas de filtre installs > 0 pour Lalalab Client Report ios
📤 Push vers Google Sheets...
✅ Auth via Service Account
✅ Push réussi: https://docs.google.com/spreadsheets/d/16xYLvkEsLsLLMN6gCXrgEg7ruPC50U9gsFy32ePBVb4
```

### 4.3 Vérifie le Google Sheet

Ouvre : https://docs.google.com/spreadsheets/d/16xYLvkEsLsLLMN6gCXrgEg7ruPC50U9gsFy32ePBVb4/edit#gid=1809357019

**Tu dois voir :**
- Les colonnes correctes
- Les revenues qui remontent (pas à 0)
- Les données de novembre 2025

---

## ⏰ PHASE 5 : Automatisation quotidienne (8 min)

### 5.1 Crée le script d'exécution quotidienne

```bash
cd ~/Downloads/adjust_pipeline

# Crée le script
cat > run_daily.sh << 'EOF'
#!/bin/bash
cd ~/Downloads/adjust_pipeline
/usr/local/bin/python3 adjust_to_gsheet.py >> logs/$(date +\%Y-\%m-\%d).log 2>&1
EOF

# Rends-le exécutable
chmod +x run_daily.sh

# Crée le dossier logs
mkdir -p logs
```

### 5.2 Modifie le script pour dates automatiques

Ouvre `adjust_to_gsheet.py` et change la fin :

**Avant :**
```python
if __name__ == "__main__":
    df = run_pipeline(
        config=LALALAB_IOS_CONFIG,
        begin_date="2025-11-01",
        end_date="2025-11-21"
    )
```

**Après :**
```python
if __name__ == "__main__":
    # Dates automatiques : du 1er du mois à hier
    from datetime import date, timedelta
    today = date.today()
    begin_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    df = run_pipeline(
        config=LALALAB_IOS_CONFIG,
        begin_date=begin_date,
        end_date=end_date
    )
```

### 5.3 Configure le cron

```bash
# Ouvre l'éditeur cron
crontab -e
```

Appuie sur `i` pour passer en mode insertion, puis colle :

```bash
# Lalalab reporting - tous les jours à 6h du matin
0 6 * * * ~/Downloads/adjust_pipeline/run_daily.sh
```

Appuie sur `Esc`, puis tape `:wq` et `Entrée`.

**Vérifie :**
```bash
crontab -l
```

Tu dois voir ta ligne.

### 5.4 Test manuel

```bash
# Teste le script d'exécution
./run_daily.sh

# Vérifie le log
cat logs/$(date +%Y-%m-%d).log
```

---

## ✅ RÉCAPITULATIF

Tu as maintenant :

- ✅ **Accès autonome** à l'API Adjust
- ✅ **Service Account Google** pour écrire dans les Sheets
- ✅ **Script fonctionnel** avec les bugs fixés
- ✅ **Automatisation quotidienne** à 6h du matin
- ✅ **Logs** pour suivre les exécutions

**Tu n'as plus besoin de ton tech.**

---

## 🆘 TROUBLESHOOTING

### Erreur "Permission denied" sur le service account
→ Retourne au Google Sheet, clique Share, et vérifie que l'email du service account a bien les droits Editor

### Erreur "API Token invalid"
→ Vérifie ton API Token dans le fichier : `ADJUST_API_TOKEN = "yUFH42Wz_8VXFQ51nyA9"`

### Erreur "App Token not found"
→ Vérifie que `"app_token": "vmu6fbf5yprt"` est bien dans la config

### Le cron ne se lance pas
→ Vérifie le chemin complet vers python3 :
```bash
which python3
# Utilise ce chemin dans run_daily.sh
```

### Les revenues sont toujours à 0
→ Envoie-moi une capture du terminal quand tu lances `python3 test_adjust_api.py`

---

## 📞 PROCHAINES ÉTAPES

1. Lance `python3 test_adjust_api.py` maintenant
2. Copie-moi la sortie complète
3. Je te confirme que tout est OK
4. Tu passes à la Phase 4
