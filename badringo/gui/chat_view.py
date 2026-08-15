"""
gui/chat_view.py
Chat question-réponse avec l'IA : l'utilisateur écrit en anglais,
l'IA répond ET signale les erreurs, qui sont ajoutées automatiquement
au journal d'erreurs.
"""

import tkinter as tk

from database import models
from services.ai_service import demander_correction_et_reponse


class ChatView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self.conversation_id = models.creer_conversation("Pratique libre")
        self._build()

    def _build(self):
        tk.Label(self, text="Chat / Pratique d'écriture", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        self.zone_chat = tk.Text(self, wrap="word", state="disabled", bg="#fafafa", height=22)
        self.zone_chat.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.zone_chat.tag_config("utilisateur", foreground="#111", font=("Segoe UI", 10, "bold"))
        self.zone_chat.tag_config("ia", foreground="#2563eb")
        self.zone_chat.tag_config("erreur", foreground="#dc2626")

        bas = tk.Frame(self, bg="white")
        bas.pack(fill="x", padx=20, pady=(0, 20))

        self.entree = tk.Entry(bas, font=("Segoe UI", 11))
        self.entree.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entree.bind("<Return>", lambda e: self.envoyer())

        tk.Button(bas, text="Envoyer", command=self.envoyer).pack(side="left")

    def _ecrire(self, texte, tag=None):
        self.zone_chat.config(state="normal")
        self.zone_chat.insert("end", texte + "\n", tag)
        self.zone_chat.config(state="disabled")
        self.zone_chat.see("end")

    def envoyer(self):
        message = self.entree.get().strip()
        if not message:
            return
        self.entree.delete(0, tk.END)

        self._ecrire(f"Toi : {message}", "utilisateur")
        models.ajouter_message(self.conversation_id, "utilisateur", message)

        historique = models.lister_messages(self.conversation_id)
        resultat = demander_correction_et_reponse(message, historique)

        self._ecrire(f"IA : {resultat['reponse']}", "ia")

        for err in resultat.get("erreurs", []):
            self._ecrire(
                f"   ⚠ {err.get('original', '')} → {err.get('correction', '')} "
                f"({err.get('explication', '')})",
                "erreur"
            )
            models.ajouter_erreur(
                err.get("original", ""), err.get("correction", ""), err.get("explication", "")
            )

        models.ajouter_message(self.conversation_id, "ia", resultat["reponse"], resultat.get("erreurs"))
