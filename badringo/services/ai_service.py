"""
services/ai_service.py
Gère les appels à Ollama (IA locale, gratuite, hors-ligne) pour :
- répondre en anglais dans la conversation (mode chat)
- détecter et corriger les erreurs du message de l'utilisateur

Ollama doit être installé et lancé sur la machine (https://ollama.com),
avec un modèle téléchargé (ex: "llama3.1" ou "mistral").
Aucune clé API, aucun compte, aucun coût.
"""

import json
import re
import urllib.request
import urllib.error

from config import load_settings

SYSTEM_PROMPT = """You are a patient, encouraging English teacher.
The user writes to you in English to practice. You must reply ONLY with
a valid JSON object, with no text before or after it, in exactly this form:

{
  "reponse": "your reply in English that continues the conversation naturally",
  "erreurs": [
    {"original": "faulty excerpt", "correction": "corrected version", "explication": "brief explanation in French"}
  ]
}

If the message has no errors, return "erreurs": [].
Stay friendly and adapt your language level to the user's."""


def _ollama_url():
    settings = load_settings()
    base = settings.get("ollama_url", "http://localhost:11434")
    return base.rstrip("/")


def _ollama_model():
    settings = load_settings()
    return settings.get("ollama_model", "llama3.2")


def ollama_est_disponible():
    """Vérifie rapidement si le serveur Ollama tourne en local."""
    try:
        urllib.request.urlopen(f"{_ollama_url()}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def demander_correction_et_reponse(message_utilisateur, historique=None):
    """
    Envoie le message de l'utilisateur à Ollama et renvoie un dict :
    {"reponse": str, "erreurs": [ {original, correction, explication}, ... ]}
    """
    if not ollama_est_disponible():
        return {
            "reponse": (
                "(Ollama n'est pas détecté. Vérifie qu'il est bien installé "
                "et lancé sur ton ordinateur — voir le README.)"
            ),
            "erreurs": []
        }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if historique:
        for m in historique:
            role = "assistant" if m["expediteur"] == "ia" else "user"
            messages.append({"role": role, "content": m["contenu"]})
    messages.append({"role": "user", "content": message_utilisateur})

    payload = json.dumps({
        "model": _ollama_model(),
        "messages": messages,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{_ollama_url()}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        texte = data.get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return {
            "reponse": (
                f"(Erreur Ollama {e.code} sur {_ollama_url()}/api/chat, "
                f"modèle demandé : '{_ollama_model()}'. Détail : {detail})"
            ),
            "erreurs": []
        }
    except urllib.error.URLError as e:
        return {"reponse": f"(Erreur de connexion à Ollama ({_ollama_url()}) : {e})", "erreurs": []}
    except Exception as e:
        return {"reponse": f"(Erreur lors de l'appel à Ollama : {e})", "erreurs": []}

    texte_propre = re.sub(r"^```json|```$", "", texte.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", texte_propre, flags=re.DOTALL)
    if match:
        texte_propre = match.group(0)

    try:
        resultat = json.loads(texte_propre)
        if "reponse" not in resultat:
            resultat["reponse"] = texte
        if "erreurs" not in resultat:
            resultat["erreurs"] = []
        return resultat
    except json.JSONDecodeError:
        return {"reponse": texte, "erreurs": []}
