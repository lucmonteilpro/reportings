# 👋 COMMENCE ICI

Bienvenue dans ton pipeline Adjust → Google Sheets autonome !

---

## 🎯 QUEL EST TON PROFIL ?

### Option A : "Je veux aller vite, dis-moi juste quoi faire"
→ Ouvre **QUICKSTART.md** (15 minutes chrono)

### Option B : "Je veux comprendre chaque étape en détail"
→ Ouvre **GUIDE_COMPLET.md** (30 minutes avec explications)

### Option C : "Je veux juste vérifier que tout fonctionne"
→ Lance dans Terminal :
```bash
python3 validate.py
```

---

## 📁 STRUCTURE DU PACKAGE

| Fichier | Description | Tu l'ouvres quand ? |
|---------|-------------|---------------------|
| **START_HERE.md** | Ce fichier - Point de départ | Maintenant ✅ |
| **QUICKSTART.md** | Guide rapide 15 min | Tu veux aller vite |
| **GUIDE_COMPLET.md** | Guide détaillé 30 min | Tu veux tout comprendre |
| **CHECKLIST.md** | Cases à cocher | Tu veux suivre ta progression |
| **README.md** | Vue d'ensemble technique | Tu cherches une info précise |
| `validate.py` | Vérifie ton installation | Premier script à lancer |
| `test_adjust_api.py` | Teste l'API Adjust | 2ème script à lancer |
| `adjust_to_gsheet.py` | Pipeline complet | 3ème script à lancer |
| `run_daily.sh` | Script cron quotidien | Pour l'automatisation |
| `requirements.txt` | Dépendances Python | Pour pip install |

---

## ⚡ DÉMARRAGE EXPRESS (3 commandes)

```bash
# 1. Installe les dépendances
pip3 install -r requirements.txt

# 2. Vérifie que tout est OK
python3 validate.py

# 3. Teste l'API Adjust
python3 test_adjust_api.py
```

Si les 3 commandes fonctionnent → Tu es à 50% du chemin !

Il te reste juste à :
- Créer le Service Account Google (7 min)
- Lancer le pipeline complet
- Automatiser avec cron

→ Ouvre **QUICKSTART.md** ou **GUIDE_COMPLET.md** pour la suite

---

## 🆘 PROBLÈME ?

1. Lance `python3 validate.py` pour identifier le blocage
2. Consulte la section Troubleshooting dans `GUIDE_COMPLET.md`
3. Copie-colle l'erreur et envoie-la moi

---

## ✅ CE QUI EST DÉJÀ FAIT

Tu n'as PAS besoin de :
- ❌ Chercher les API tokens → Déjà configurés
- ❌ Chercher les app tokens → Déjà configurés
- ❌ Chercher les IDs des Google Sheets → Déjà configurés
- ❌ Fixer les bugs du code → Déjà fixés
- ❌ Configurer les custom CPI → Déjà configurés

Tu dois SEULEMENT :
- ✅ Créer ton Service Account Google
- ✅ Tester que ça fonctionne
- ✅ Automatiser

**C'est tout !**

---

## 🚀 PRÊT ? GO !

→ **Ouvre QUICKSTART.md maintenant**

Ou si tu préfères le mode détaillé : **GUIDE_COMPLET.md**
