#!/bin/bash

# =============================================================================
# SCRIPT D'EXÉCUTION QUOTIDIENNE LALALAB
# Lance ce script tous les jours via cron pour mettre à jour les reportings
# =============================================================================

# Définit le répertoire de travail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Crée le dossier logs s'il n'existe pas
mkdir -p logs

# Date du jour pour le log
LOG_DATE=$(date +%Y-%m-%d)
LOG_FILE="logs/${LOG_DATE}.log"

# Lance le script Python et log la sortie
echo "=====================================================" >> "$LOG_FILE"
echo "Exécution: $(date)" >> "$LOG_FILE"
echo "=====================================================" >> "$LOG_FILE"

# Trouve le chemin vers python3
PYTHON_PATH=$(which python3)

# Lance le script
"$PYTHON_PATH" adjust_to_gsheet.py >> "$LOG_FILE" 2>&1

# Code de sortie
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "Fin: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Si erreur, envoie une notification (optionnel)
if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ ERREUR - Vérifier le log: $LOG_FILE"
fi

exit $EXIT_CODE
