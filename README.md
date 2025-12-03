# 📋 ADJUST LALALAB PIPELINE - VERSION FINALE

## ✅ Modifications appliquées

### 1️⃣ Attribution First (au lieu de Dynamic)
**Fichier:** `adjust_to_gsheet.py` ligne 217
```python
"attribution_source": "first",  # ✅ First attribution
```

**Résultat:** Les First Purchase correspondent maintenant exactement au dashboard Adjust (405 pour France).

---

### 2️⃣ Repush 30 derniers jours
**Fichier:** `adjust_lalalab.py` lignes 256-258
```python
today = date.today()
begin_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")  # 30 jours
end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")     # Hier
```

**Raison:** Les revenues d7 et d30 changent chaque jour. Il faut repusher les 30 derniers jours pour avoir les revenues à jour.

---

### 3️⃣ Préservation des CPI manuels
**Fichier:** `adjust_to_gsheet.py` fonction `push_to_gsheet()` lignes 322-360

**Logique:**
1. Avant de pusher, le script lit les CPI existants dans le Google Sheet
2. Créer une clé unique basée sur: Day + Country + Campaign + Adgroup + Creative
3. Si un CPI manuel existe pour une ligne, il est **préservé**
4. Sinon, le CPI auto (custom CPI) est utilisé

**Exemple:**
- Tu modifies manuellement le CPI France de 7.0 à 8.5 dans le sheet
- Le lendemain, le script repush les données
- Le CPI 8.5 est **préservé**, les autres lignes ont leur CPI auto

---

## 🚀 Utilisation

```bash
python3 adjust_lalalab.py
```

---

## 📊 Ce qui est pushé

### Données repushées:
- 30 derniers jours complets
- Revenues d7/d30 mis à jour quotidiennement
- First Purchase events inclus
- Filtre pays: France, Germany, Italy uniquement

### Colonnes dans le Google Sheet:
```
App
Month (date)
Week (date)
Day (date)
Network (attribution)
Country
Campaign (attribution)
Adgroup (attribution)
Creative (attribution)
Ad spend
Installs
Impressions
Clicks
In-app revenue
0D All revenue total
7D All revenue total
30D All revenue total
CPI                        ← ✅ Préservé si modifié manuellement
First Purchase_events      ← ✅ Nouvelle colonne
```

---

## ⚠️ Points d'attention

### CPI manuels préservés SI:
- La ligne existe déjà dans le sheet
- La clé (Day + Country + Campaign + Adgroup + Creative) est identique

### CPI manuels NON préservés SI:
- Tu changes le nom d'une campagne dans le sheet manuellement
- La ligne n'existait pas avant (nouvelle campagne)

**→ C'est normal et attendu**

---

## 🔧 Configuration

Configuration centralisée dans:
```
Google Sheet ID: 1-929N5tQOPWIrT9ocitxQFpD_ijAhL7WshgOyYrkQhI
Onglet: "custom CPI"
```

### Paramètres configurables par client:
- `custom_cpi`: CPI par pays (France: 7€, Germany: 5€)
- `countries`: Pays à filtrer (France, Germany, Italy)
- `events`: Événements à remonter (first purchase_events)
- `agg_columns`: Colonnes d'agrégation

---

## 📅 Fréquence recommandée

**Cron quotidien:**
```bash
0 6 * * * cd /Users/lucmonteil/reportings && python3 adjust_lalalab.py
```

Exécution recommandée: 6h du matin (après mise à jour Adjust)

---

## 🐛 Troubleshooting

### Problème: CPI manuel perdu
**Cause:** Nom de campagne/adgroup/creative modifié dans le sheet
**Solution:** Normal, le merge ne peut pas matcher. Réappliquer le CPI manuellement.

### Problème: First Purchase = 0
**Cause:** Événement mal nommé dans config
**Solution:** Vérifier que `events: ['first purchase_events']` correspond au nom exact dans Adjust

### Problème: Revenues d7/d30 ne changent pas
**Cause:** Date de début trop ancienne ou pas de repush
**Solution:** Vérifier que `begin_date = (today - timedelta(days=30))`

---

## 📞 Support

Questions? Contacte ACH.31 ou vérifie les logs d'exécution.