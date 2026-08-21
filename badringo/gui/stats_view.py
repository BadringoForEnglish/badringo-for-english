"""
gui/stats_view.py
Tableau de bord : vue d'ensemble de la progression.
"""

import tkinter as tk

from database import models
from config import APP_NAME
from services.adaptive_learning import generer_plan_du_jour
from services.daily_dashboard import calculer_streak, calculer_progression_recente


class StatsView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        profil = models.obtenir_profil()
        prenom = profil["prenom"] if profil and profil["prenom"] else None
        salutation = f"👋 Bonjour {prenom} !" if prenom else f"Bienvenue sur {APP_NAME}"

        tk.Label(self, text=salutation, font=("Segoe UI", 18, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 5)
        )

        # --- Streak et tendance de progression ---
        streak = calculer_streak()
        progression = calculer_progression_recente()

        indicateurs = tk.Frame(self, bg="white")
        indicateurs.pack(anchor="w", padx=20, pady=(0, 15))

        if streak > 0:
            tk.Label(
                indicateurs, text=f"🔥 {streak} jour{'s' if streak > 1 else ''} d'affilée",
                bg="white", font=("Segoe UI", 10, "bold"), fg="#ea580c"
            ).pack(side="left", padx=(0, 20))

        if progression is not None:
            signe = "+" if progression >= 0 else ""
            couleur = "#16a34a" if progression >= 0 else "#dc2626"
            tk.Label(
                indicateurs, text=f"{signe}{progression}% cette semaine (vs la précédente)",
                bg="white", font=("Segoe UI", 10, "bold"), fg=couleur
            ).pack(side="left")

        # --- Plan du jour (moteur adaptatif, Phase 5) ---
        plan = generer_plan_du_jour()
        if plan:
            tk.Label(
                self, text="📋 Plan du jour", font=("Segoe UI", 14, "bold"), bg="white"
            ).pack(anchor="w", padx=20, pady=(0, 10))

            for recommandation in plan:
                carte = tk.Frame(self, bg="#eff6ff", padx=15, pady=10)
                carte.pack(fill="x", padx=20, pady=3)
                tk.Label(
                    carte, text=recommandation["titre"], bg="#eff6ff",
                    font=("Segoe UI", 11, "bold"), anchor="w"
                ).pack(anchor="w")
                tk.Label(
                    carte, text=recommandation["detail"], bg="#eff6ff",
                    fg="#555", font=("Segoe UI", 9), anchor="w", wraplength=800, justify="left"
                ).pack(anchor="w")

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

        # --- Notions à travailler en priorité ---
        notions_faibles = models.lister_maitrise_notions(limite=5, minimum_reponses=3)
        if notions_faibles:
            tk.Label(
                self, text="Notions à travailler", font=("Segoe UI", 13, "bold"), bg="white"
            ).pack(anchor="w", padx=20, pady=(25, 10))

            zone_notions = tk.Frame(self, bg="white")
            zone_notions.pack(anchor="w", padx=20, fill="x")

            for n in notions_faibles:
                score = n["score"]
                if score < 50:
                    pastille, couleur = "🔴", "#dc2626"
                elif score < 80:
                    pastille, couleur = "🟡", "#d97706"
                else:
                    pastille, couleur = "🟢", "#16a34a"

                ligne = tk.Frame(zone_notions, bg="#f9fafb", padx=15, pady=8)
                ligne.pack(fill="x", pady=2)
                tk.Label(ligne, text=f"{pastille} {n['notion']}", bg="#f9fafb", width=30, anchor="w").pack(side="left")
                tk.Label(
                    ligne,
                    text=f"{score:.0f}%  ({n['nb_correctes']}/{n['nb_reponses']})  •  {models.libelle_maitrise(score)}",
                    bg="#f9fafb", fg=couleur, font=("Segoe UI", 10, "bold")
                ).pack(side="left")
