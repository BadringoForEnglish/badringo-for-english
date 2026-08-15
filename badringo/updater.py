"""
updater.py
Système de mise à jour automatique pour Badringo for English.

Fonctionnement (100% automatisé, sans étape manuelle sur GitHub) :
1. L'app est publiée via des "Releases" GitHub (tag ex: v1.1.0). Publier
   une Release déclenche automatiquement le workflow GitHub Actions
   (.github/workflows/build-release.yml) qui compile le .exe sur les
   serveurs de GitHub et l'attache à la Release. Aucun PyCharm ni
   build_exe.bat nécessaire côté développeur.
2. check_for_updates() interroge directement l'API GitHub pour connaître
   la dernière Release publiée (pas de fichier version.json à maintenir).
3. Si une nouvelle version existe, download_update() télécharge le nouvel
   .exe (l'asset de la Release) dans un dossier temporaire.
4. apply_update() lance un petit script qui :
     - attend la fermeture de l'app actuelle
     - remplace l'ancien .exe par le nouveau
     - relance l'application

À CONFIGURER : remplace GITHUB_USER et GITHUB_REPO par ton propre dépôt.
"""

import os
import sys
import json
import subprocess
import tempfile
import urllib.request

from config import APP_VERSION, APP_NAME

GITHUB_USER = "BadringoForEnglish"
GITHUB_REPO = "badringo-for-english"

# API publique GitHub : renvoie toujours la dernière Release publiée,
# sans authentification nécessaire pour un dépôt public.
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


def _version_tuple(v):
    v = v.lstrip("vV")  # tolère les tags "v1.1.0" ou "1.1.0"
    return tuple(int(x) for x in v.split("."))


def check_for_updates():
    """
    Retourne un dict {"disponible": bool, "version": str, "notes": str, "exe_url": str}
    ou None en cas d'échec réseau. Lit directement la dernière Release GitHub,
    aucun fichier à maintenir manuellement.
    """
    try:
        request = urllib.request.Request(
            LATEST_RELEASE_API,
            headers={"Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        distante = data.get("tag_name", APP_VERSION)
        disponible = _version_tuple(distante) > _version_tuple(APP_VERSION)

        exe_url = ""
        for asset in data.get("assets", []):
            if asset.get("name", "").lower().endswith(".exe"):
                exe_url = asset.get("browser_download_url", "")
                break

        return {
            "disponible": disponible,
            "version": distante.lstrip("vV"),
            "notes": data.get("body", ""),
            "exe_url": exe_url
        }
    except Exception as e:
        print(f"[Updater] Vérification impossible : {e}")
        return None


def download_update(exe_url, progress_callback=None):
    """Télécharge le nouvel exécutable dans un dossier temporaire et retourne son chemin."""
    tmp_dir = tempfile.mkdtemp(prefix="badringo_update_")
    dest_path = os.path.join(tmp_dir, "BadringoForEnglish_new.exe")

    def _reporthook(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            pourcentage = min(100, int(block_num * block_size * 100 / total_size))
            progress_callback(pourcentage)

    urllib.request.urlretrieve(exe_url, dest_path, _reporthook)
    return dest_path


def apply_update(new_exe_path):
    """
    Remplace l'exécutable actuel par le nouveau et relance l'application.
    Ne fonctionne que sur l'app compilée (sys.frozen == True avec PyInstaller).
    """
    if not getattr(sys, "frozen", False):
        print("[Updater] apply_update() ne s'exécute que sur la version .exe compilée.")
        return

    current_exe = sys.executable
    current_dir = os.path.dirname(current_exe)
    bat_path = os.path.join(current_dir, "_update.bat")

    # Script batch : attend la fermeture de l'app, remplace le .exe, relance
    script = f"""@echo off
:wait
timeout /t 1 /nobreak > nul
tasklist | find /i "{os.path.basename(current_exe)}" > nul
if not errorlevel 1 goto wait
copy /Y "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(script)

    subprocess.Popen(["cmd", "/c", bat_path], shell=True)
    sys.exit(0)


if __name__ == "__main__":
    print(f"{APP_NAME} — vérification des mises à jour (version actuelle : {APP_VERSION})")
    result = check_for_updates()
    if result is None:
        print("Impossible de vérifier les mises à jour (pas de connexion ?).")
    elif result["disponible"]:
        print(f"Nouvelle version disponible : {result['version']}")
        print(f"Notes : {result['notes']}")
    else:
        print("Vous avez déjà la dernière version.")
