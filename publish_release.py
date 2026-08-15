"""
publish_release.py
Automatise entièrement la publication d'une nouvelle version :
1. Demande le nouveau numéro de version
2. Le met à jour dans config.py
3. Envoie le code sur GitHub (commit + push)
4. Crée et envoie un tag git (ex: v1.2.0)
   -> Ce tag déclenche automatiquement GitHub Actions, qui compile
      le .exe et publie la Release toute seule. Rien d'autre à faire.

Utilisation : double-clique sur publier_nouvelle_version.bat
"""

import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.py"


def lire_version_actuelle():
    contenu = CONFIG_PATH.read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', contenu)
    return match.group(1) if match else "inconnue"


def mettre_a_jour_version(nouvelle_version):
    contenu = CONFIG_PATH.read_text(encoding="utf-8")
    contenu_modifie = re.sub(
        r'APP_VERSION\s*=\s*"[^"]+"',
        f'APP_VERSION = "{nouvelle_version}"',
        contenu
    )
    CONFIG_PATH.write_text(contenu_modifie, encoding="utf-8")


def executer(commande):
    print(f"\n>>> {' '.join(commande)}")
    resultat = subprocess.run(commande, cwd=BASE_DIR, capture_output=True, text=True)
    if resultat.stdout.strip():
        print(resultat.stdout.strip())
    if resultat.returncode != 0:
        print(resultat.stderr.strip())
        return False
    return True


def main():
    print("=" * 60)
    print("  Publication d'une nouvelle version de Badringo for English")
    print("=" * 60)

    version_actuelle = lire_version_actuelle()
    print(f"\nVersion actuelle : {version_actuelle}")
    nouvelle_version = input("Nouvelle version (ex: 1.2.0, sans le 'v') : ").strip()

    if not re.match(r"^\d+\.\d+\.\d+$", nouvelle_version):
        print("\n❌ Format invalide. Utilise le format X.Y.Z, ex: 1.2.0")
        input("\nAppuie sur Entrée pour fermer...")
        sys.exit(1)

    tag = f"v{nouvelle_version}"

    print(f"\n1) Mise à jour de config.py -> {nouvelle_version}")
    mettre_a_jour_version(nouvelle_version)

    print("\n2) Envoi du code sur GitHub...")
    if not executer(["git", "add", "-A"]):
        sys.exit(1)
    executer(["git", "commit", "-m", f"Version {nouvelle_version}"])  # rien à commit -> pas grave
    if not executer(["git", "push", "origin", "main"]):
        print("\n❌ Échec de l'envoi du code. Vérifie ta connexion / tes identifiants GitHub.")
        input("\nAppuie sur Entrée pour fermer...")
        sys.exit(1)

    print(f"\n3) Création et envoi du tag {tag}...")
    if not executer(["git", "tag", tag]):
        print(f"\n❌ Le tag {tag} existe peut-être déjà.")
        input("\nAppuie sur Entrée pour fermer...")
        sys.exit(1)
    if not executer(["git", "push", "origin", tag]):
        input("\nAppuie sur Entrée pour fermer...")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"✅ Version {nouvelle_version} envoyée avec succès !")
    print("GitHub Actions va maintenant compiler le .exe automatiquement")
    print("(1 à 3 minutes). Suis la progression ici :")
    print("https://github.com/BadringoForEnglish/badringo-for-english/actions")
    print("=" * 60)
    input("\nAppuie sur Entrée pour fermer...")


if __name__ == "__main__":
    main()
