"""
config.py
Configuration globale de l'application Badringo for English.
"""

import os
import json

APP_NAME = "Badringo for English"
APP_VERSION = "1.6.2"

# Dossiers
# En version .exe (PyInstaller --onefile), le programme s'exécute depuis un
# dossier temporaire qui change à chaque lancement : on ne peut donc PAS y
# stocker la base de données ou les réglages, sous peine de tout perdre à
# chaque redémarrage. On utilise donc systématiquement un dossier stable
# dans AppData (Windows) / le dossier utilisateur (autres systèmes).
import sys

if getattr(sys, "frozen", False):
    # Application compilée (.exe)
    DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "BadringoForEnglish")
else:
    # Mode développement (python main.py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

DB_PATH = os.path.join(DATA_DIR, "badringo.db")
CONFIG_PATH = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)

# Configuration par défaut (thème, langue, fenêtre, clé API...)
DEFAULT_SETTINGS = {
    "theme": "light",          # "light" ou "dark"
    "window_width": 1100,
    "window_height": 700,
    "ollama_url": "http://localhost:11434",   # adresse du serveur Ollama local
    "ollama_model": "llama3.2",               # modèle local à utiliser pour le chat
    "user_name": "Utilisateur",
    "last_update_check": "",
    "chat_font_family": "Segoe UI",           # police d'affichage du chat
    "chat_font_size": 12,                     # taille d'affichage du chat
    "conversation_active_id": None            # id de la conversation en cours (persistance)
}


def load_settings():
    """Charge les réglages, ou crée le fichier avec les valeurs par défaut."""
    if not os.path.exists(CONFIG_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        # Complète les clés manquantes si une nouvelle version ajoute des options
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
