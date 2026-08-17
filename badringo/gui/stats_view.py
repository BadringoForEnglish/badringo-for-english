"""
gui/stats_view.py
Tableau de bord : vue d'ensemble de la progression.
"""

import tkinter as tk

from database import models
from config import APP_NAME


class StatsView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text=f"Bienvenue sur {APP_NAME}", font=("Segoe UI", 18, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 20)
        )

        stats = models.statistiques()

        cartes = [
            ("Mots enregistrés", stats["total_mots"]),
            ("Mots maîtrisés", stats["mots_maitrises"]),
            ("À réviser aujourd'hui", stats["mots_a_reviser"]),
            ("Règles de grammaire", stats["total_regles"]),
            ("Erreurs journalisées", stats["total_erreurs"]),
            ("Conversations", stats["total_conversations"]),
        ]

        grille = tk.Frame(self, bg="white")
        grille.pack(padx=20, fill="x")

        for i, (label, valeur) in enumerate(cartes):
            carte = tk.Frame(grille, bg="#f0f4ff", padx=20, pady=20)
            carte.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
            tk.Label(carte, text=str(valeur), font=("Segoe UI", 22, "bold"), bg="#f0f4ff", fg="#2563eb").pack()
            tk.Label(carte, text=label, bg="#f0f4ff").pack()

        for c in range(3):
            grille.columnconfigure(c, weight=1)

        # --- Historique des derniers quiz ---
        sessions = models.lister_sessions_quiz(limite=5)
        if sessions:
            tk.Label(
                self, text="Derniers quiz", font=("Segoe UI", 13, "bold"), bg="white"
            ).pack(anchor="w", padx=20, pady=(25, 10))

            historique = tk.Frame(self, bg="white")
            historique.pack(anchor="w", padx=20, fill="x")

            for s in sessions:
                pourcentage = round(100 * s["score"] / s["total"]) if s["total"] else 0
                date_affichee = s["date_session"][:16].replace("T", " ")
                ligne = tk.Frame(historique, bg="#f9fafb", padx=15, pady=8)
                ligne.pack(fill="x", pady=2)
                tk.Label(ligne, text=date_affichee, bg="#f9fafb", fg="#666", width=18, anchor="w").pack(side="left")
                tk.Label(
                    ligne, text=f"{s['score']} / {s['total']}  ({pourcentage}%)",
                    bg="#f9fafb", font=("Segoe UI", 10, "bold")
                ).pack(side="left")
