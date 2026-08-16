"""
gui/chat_view.py
Chat question-réponse avec l'IA : l'utilisateur écrit en anglais,
l'IA répond ET signale les erreurs, qui sont ajoutées automatiquement
au journal d'erreurs.

- La conversation est persistante : elle reprend là où tu l'as laissée
  à chaque ouverture de l'onglet ou redémarrage de l'app.
- Bouton "Nouvelle conversation" pour repartir de zéro (l'historique
  précédent reste conservé en base, juste plus affiché à l'écran).
- Police et taille du texte personnalisables.
- L'appel à l'IA tourne dans un thread séparé pour ne jamais geler
  l'interface.
"""

import threading
import tkinter as tk
from tkinter import ttk

from database import models
from services.ai_service import demander_correction_et_reponse
from config import load_settings, save_settings

TAILLES_DISPONIBLES = [10, 11, 12, 14, 16, 18, 20]
POLICES_DISPONIBLES = ["Segoe UI", "Arial", "Calibri", "Consolas", "Georgia", "Verdana"]


class ChatView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self.settings = load_settings()
        self.en_attente = False

        self.conversation_id = self._recuperer_ou_creer_conversation()
        self._build()
        self._charger_historique()

    # ------------------------------------------------------------------
    def _recuperer_ou_creer_conversation(self):
        conv_id = self.settings.get("conversation_active_id")
        if conv_id and models.conversation_existe(conv_id):
            return conv_id
        return self._creer_nouvelle_conversation_et_sauver()

    def _creer_nouvelle_conversation_et_sauver(self):
        conv_id = models.creer_conversation("Pratique libre")
        self.settings["conversation_active_id"] = conv_id
        save_settings(self.settings)
        return conv_id

    # ------------------------------------------------------------------
    def _build(self):
        entete = tk.Frame(self, bg="white")
        entete.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(entete, text="Chat / Pratique d'écriture", font=("Segoe UI", 16, "bold"), bg="white").pack(
            side="left"
        )

        tk.Button(
            entete, text="🔄 Nouvelle conversation", font=("Segoe UI", 9),
            command=self._nouvelle_conversation
        ).pack(side="right")

        # --- Réglages de police ---
        reglages = tk.Frame(self, bg="white")
        reglages.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(reglages, text="Police :", bg="white", font=("Segoe UI", 9)).pack(side="left")
        self.police_var = tk.StringVar(value=self.settings.get("chat_font_family", "Segoe UI"))
        combo_police = ttk.Combobox(
            reglages, textvariable=self.police_var, values=POLICES_DISPONIBLES,
            width=15, state="readonly"
        )
        combo_police.pack(side="left", padx=(5, 15))
        combo_police.bind("<<ComboboxSelected>>", lambda e: self._appliquer_police())

        tk.Label(reglages, text="Taille :", bg="white", font=("Segoe UI", 9)).pack(side="left")
        self.taille_var = tk.IntVar(value=self.settings.get("chat_font_size", 12))
        combo_taille = ttk.Combobox(
            reglages, textvariable=self.taille_var, values=TAILLES_DISPONIBLES,
            width=5, state="readonly"
        )
        combo_taille.pack(side="left", padx=5)
        combo_taille.bind("<<ComboboxSelected>>", lambda e: self._appliquer_police())

        # --- Zone de conversation ---
        self.zone_chat = tk.Text(self, wrap="word", state="disabled", bg="#fafafa", height=20)
        self.zone_chat.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._appliquer_police()

        self.zone_chat.tag_config("utilisateur", foreground="#111", font=self._police(gras=True))
        self.zone_chat.tag_config("ia", foreground="#2563eb", font=self._police(gras=True))
        self.zone_chat.tag_config("texte", font=self._police())
        self.zone_chat.tag_config("erreur", foreground="#dc2626", font=self._police())
        self.zone_chat.tag_config("statut", foreground="#999", font=self._police(italique=True))

        bas = tk.Frame(self, bg="white")
        bas.pack(fill="x", padx=20, pady=(0, 20))

        self.entree = tk.Entry(bas, font=self._police())
        self.entree.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entree.bind("<Return>", lambda e: self.envoyer())

        self.bouton_envoyer = tk.Button(bas, text="Envoyer", command=self.envoyer)
        self.bouton_envoyer.pack(side="left")

    # ------------------------------------------------------------------
    def _police(self, gras=False, italique=False):
        style = []
        if gras:
            style.append("bold")
        if italique:
            style.append("italic")
        famille = self.police_var.get() if hasattr(self, "police_var") else self.settings.get("chat_font_family", "Segoe UI")
        taille = self.taille_var.get() if hasattr(self, "taille_var") else self.settings.get("chat_font_size", 12)
        return (famille, taille, " ".join(style)) if style else (famille, taille)

    def _appliquer_police(self):
        self.settings["chat_font_family"] = self.police_var.get()
        self.settings["chat_font_size"] = self.taille_var.get()
        save_settings(self.settings)

        if hasattr(self, "zone_chat"):
            self.zone_chat.config(font=self._police())
            self.zone_chat.tag_config("utilisateur", font=self._police(gras=True))
            self.zone_chat.tag_config("ia", font=self._police(gras=True))
            self.zone_chat.tag_config("texte", font=self._police())
            self.zone_chat.tag_config("erreur", font=self._police())
            self.zone_chat.tag_config("statut", font=self._police(italique=True))
        if hasattr(self, "entree"):
            self.entree.config(font=self._police())

    # ------------------------------------------------------------------
    def _ecrire_message(self, expediteur, texte, tag_nom):
        """Affiche un message avec l'expéditeur sur sa propre ligne, puis le
        texte en dessous — pour un affichage clair, jamais 'collé' l'un à
        l'autre."""
        self.zone_chat.config(state="normal")
        self.zone_chat.insert("end", f"{expediteur}\n", tag_nom)
        self.zone_chat.insert("end", f"{texte}\n\n", "texte")
        self.zone_chat.config(state="disabled")
        self.zone_chat.see("end")

    def _ecrire_erreur(self, texte):
        self.zone_chat.config(state="normal")
        self.zone_chat.insert("end", f"   ⚠ {texte}\n", "erreur")
        self.zone_chat.config(state="disabled")
        self.zone_chat.see("end")

    def _ecrire_statut(self, texte):
        self.zone_chat.config(state="normal")
        self.zone_chat.insert("end", f"{texte}\n\n", "statut")
        self.zone_chat.config(state="disabled")
        self.zone_chat.see("end")

    # ------------------------------------------------------------------
    def _charger_historique(self):
        messages = models.lister_messages(self.conversation_id)
        for m in messages:
            if m["expediteur"] == "utilisateur":
                self._ecrire_message("Toi", m["contenu"], "utilisateur")
            else:
                self._ecrire_message("IA", m["contenu"], "ia")
                if m["erreurs_detectees"]:
                    import json
                    try:
                        erreurs = json.loads(m["erreurs_detectees"])
                        for err in erreurs:
                            self._ecrire_erreur(
                                f"{err.get('original', '')} → {err.get('correction', '')} "
                                f"({err.get('explication', '')})"
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

    def _nouvelle_conversation(self):
        self.conversation_id = self._creer_nouvelle_conversation_et_sauver()
        self.zone_chat.config(state="normal")
        self.zone_chat.delete("1.0", "end")
        self.zone_chat.config(state="disabled")

    # ------------------------------------------------------------------
    def envoyer(self):
        if self.en_attente:
            return  # une réponse est déjà en cours, on ignore les envois multiples

        message = self.entree.get().strip()
        if not message:
            return
        self.entree.delete(0, tk.END)

        self._ecrire_message("Toi", message, "utilisateur")
        models.ajouter_message(self.conversation_id, "utilisateur", message)
        historique = models.lister_messages(self.conversation_id)

        # Feedback immédiat pendant que l'IA travaille en arrière-plan
        self.en_attente = True
        self.bouton_envoyer.config(state="disabled", text="...")
        self._debut_indicateur_attente = self.zone_chat.index("end-1c")
        self._ecrire_statut("IA est en train d'écrire...")

        thread = threading.Thread(
            target=self._appeler_ia_en_arriere_plan,
            args=(message, historique),
            daemon=True
        )
        thread.start()

    def _appeler_ia_en_arriere_plan(self, message, historique):
        """Exécuté dans un thread séparé : ne touche jamais directement aux widgets Tk."""
        resultat = demander_correction_et_reponse(message, historique)
        self.after(0, self._traiter_reponse, resultat)

    def _traiter_reponse(self, resultat):
        if hasattr(self, "_debut_indicateur_attente"):
            self.zone_chat.config(state="normal")
            self.zone_chat.delete(self._debut_indicateur_attente, "end")
            self.zone_chat.config(state="disabled")

        self._ecrire_message("IA", resultat["reponse"], "ia")

        for err in resultat.get("erreurs", []):
            self._ecrire_erreur(
                f"{err.get('original', '')} → {err.get('correction', '')} "
                f"({err.get('explication', '')})"
            )
            models.ajouter_erreur(
                err.get("original", ""), err.get("correction", ""), err.get("explication", "")
            )

        models.ajouter_message(self.conversation_id, "ia", resultat["reponse"], resultat.get("erreurs"))

        self.en_attente = False
        self.bouton_envoyer.config(state="normal", text="Envoyer")
        self.entree.focus_set()
