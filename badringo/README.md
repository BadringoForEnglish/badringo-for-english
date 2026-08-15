# Badringo for English

Application de suivi d'apprentissage de l'anglais : vocabulaire (révision
espacée), règles de grammaire/conjugaison, journal d'erreurs, et chat de
pratique avec IA.

## 1. Installation (mode développement)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

Au premier lancement, l'app crée automatiquement :
- `data/badringo.db` (base SQLite)
- `data/settings.json` (réglages : thème, taille de fenêtre, clé API...)

## 2. Configurer le chat (Ollama — 100% gratuit et local)

Le chat utilise **Ollama**, une IA qui tourne entièrement sur ta machine :
pas de clé API, pas de compte, pas de coût, et tes conversations restent
privées (aucune connexion internet nécessaire une fois le modèle téléchargé).

1. Télécharge et installe Ollama : https://ollama.com/download
2. Une fois installé, ouvre un terminal et télécharge un modèle (ex :
   Llama 3.1, environ 4-5 Go) :
   ```
   ollama pull llama3.1
   ```
3. Assure-toi qu'Ollama tourne (il se lance automatiquement en arrière-plan
   après l'installation ; sinon lance-le depuis le menu Démarrer).
4. Lance Badringo — le chat détecte automatiquement Ollama sur
   `http://localhost:11434`.

Sans Ollama installé/lancé, l'app fonctionne normalement (vocabulaire,
grammaire, erreurs) mais le chat affichera un message t'invitant à
l'installer.

Tu peux changer de modèle dans `data/settings.json` :
```json
"ollama_model": "llama3.1"
```
D'autres modèles gratuits possibles : `mistral`, `llama3.2`, `phi3` (plus
légers, adaptés si ton ordinateur a peu de RAM).

## 3. Compiler en .exe

Sur une machine Windows, avec l'environnement Python configuré :

```bash
build_exe.bat
```

Cela génère `dist/BadringoForEnglish.exe`, un exécutable autonome
(l'utilisateur final n'a pas besoin de Python installé).

## 4. Mettre en place les mises à jour automatiques

Le fichier `updater.py` vérifie une version distante hébergée sur GitHub :

1. Crée un dépôt GitHub (ex: `badringo-for-english`).
2. Ouvre `updater.py` et remplace `GITHUB_USER` par ton nom d'utilisateur.
3. À chaque nouvelle version :
   - Compile le nouvel `.exe` avec `build_exe.bat`
   - Crée une "Release" GitHub avec ce `.exe` en pièce jointe
   - Mets à jour le fichier `version.json` à la racine du dépôt (branche
     `main`) avec le nouveau numéro de version et le lien direct vers le
     `.exe` de la release (voir `version.json.example`)
4. L'application (ou un `Updater.exe` séparé compilé depuis `updater.py`)
   appelle `check_for_updates()` : si une version plus récente existe,
   elle propose de télécharger et d'installer automatiquement la mise à
   jour (remplacement de l'exécutable + relance).

Pour compiler l'updater comme exécutable séparé :

```bash
pyinstaller --onefile --console --name Updater updater.py
```

## 5. Structure du projet

```
badringo/
├── main.py                  # point d'entrée
├── config.py                 # configuration & réglages
├── updater.py                 # mise à jour automatique
├── version.json.example       # modèle du fichier de version distant
├── database/
│   ├── db.py                  # connexion + schéma SQLite
│   └── models.py               # fonctions CRUD (mots, règles, erreurs, chat)
├── services/
│   └── ai_service.py           # appels à l'API Claude pour le chat
└── gui/
    ├── app.py                   # fenêtre principale + navigation
    ├── stats_view.py             # tableau de bord
    ├── vocab_view.py              # vocabulaire + révision espacée
    ├── grammar_view.py             # règles de grammaire/conjugaison
    ├── errors_view.py               # journal d'erreurs
    └── chat_view.py                  # chat de pratique avec l'IA
```

## 6. Évolutions possibles

- Quiz auto-généré à partir du vocabulaire enregistré
- Export/import des données (JSON ou CSV)
- Mode sombre complet
- Statistiques graphiques (courbes de progression)
- Génération automatique du tableau de conjugaison d'un verbe
