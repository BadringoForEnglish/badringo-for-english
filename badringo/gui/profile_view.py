"""
gui/profile_view.py
Profil pédagogique de l'apprenant (Phase 2 — Learner Profile), avec
estimation automatique du niveau par compétence (Phase 7 — Skill
Assessment).

Le prénom, la langue maternelle et l'objectif général sont saisissables
manuellement. Le niveau estimé, lui, ne l'est jamais : il est recalculé
automatiquement à chaque ouverture de cet écran à partir des résultats
de quiz.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import models
from services.skill_assessment import evaluer_competences

OBJECTIFS_DISPONIBLES = [
    "General English",
    "Professional English",
    "Business English",
    "Pharmaceutical English",
    "Travel English",
    "Academic English",
    "Speaking",
    "Writing",
    "Vocabulary",
    "Grammar",
]


class ProfileView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Mon profil", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        # Recalcule le niveau global à chaque ouverture de l'écran, à partir
        # des résultats de quiz accumulés (Phase 7 — Skill Assessment).
        evaluation = evaluer_competences()
        if evaluation["niveau_global"]:
            models.mettre_a_jour_niveau_estime(evaluation["niveau_global"])

        profil = models.obtenir_profil()

        # --- Niveau estimé (lecture seule, jamais saisi à la main) ---
        carte_niveau = tk.Frame(self, bg="#f0f4ff", padx=20, pady=15)
        carte_niveau.pack(fill="x", padx=20, pady=(0, 10))

        niveau_affiche = profil["niveau_estime"] if profil and profil["niveau_estime"] else "Non évalué pour l'instant"
        tk.Label(carte_niveau, text="Niveau global estimé", bg="#f0f4ff", font=("Segoe UI", 10), fg="#555").pack(anchor="w")
        tk.Label(carte_niveau, text=niveau_affiche, bg="#f0f4ff", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(
            carte_niveau,
            text="Calculé à partir de tes résultats de quiz — une estimation, pas un vrai test de niveau.",
            bg="#f0f4ff", fg="#888", font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 0))

        # --- Détail par compétence ---
        detail = tk.Frame(self, bg="white")
        detail.pack(fill="x", padx=20, pady=(0, 20))

        self._afficher_ligne_competence(detail, "Vocabulary", evaluation["vocabulary"])
        self._afficher_ligne_competence(detail, "Grammar", evaluation["grammar"])

        for competence_non_evaluee in ["Reading", "Writing", "Listening", "Speaking", "Pronunciation"]:
            ligne = tk.Frame(detail, bg="#f9fafb", padx=12, pady=6)
            ligne.pack(fill="x", pady=2)
            tk.Label(ligne, text=competence_non_evaluee, bg="#f9fafb", width=15, anchor="w").pack(side="left")
            tk.Label(
                ligne, text="Non évalué — pas encore d'exercice pour cette compétence",
                bg="#f9fafb", fg="#aaa", font=("Segoe UI", 9)
            ).pack(side="left")

        # --- Formulaire ---
        form = tk.Frame(self, bg="white")
        form.pack(fill="x", padx=20)

        tk.Label(form, text="Prénom", bg="white").grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.entree_prenom = tk.Entry(form, width=30)
        self.entree_prenom.grid(row=1, column=0, sticky="w", padx=(0, 20), pady=(0, 15))

        tk.Label(form, text="Langue maternelle", bg="white").grid(row=0, column=1, sticky="w", pady=(0, 3))
        self.entree_langue = tk.Entry(form, width=30)
        self.entree_langue.grid(row=1, column=1, sticky="w", pady=(0, 15))

        tk.Label(form, text="Objectif général", bg="white").grid(row=2, column=0, sticky="w", pady=(0, 3))
        self.combo_objectif = ttk.Combobox(form, values=OBJECTIFS_DISPONIBLES, width=28, state="readonly")
        self.combo_objectif.grid(row=3, column=0, sticky="w", padx=(0, 20))

        if profil:
            self.entree_prenom.insert(0, profil["prenom"] or "")
            self.entree_langue.insert(0, profil["langue_maternelle"] or "Français")
            if profil["objectif_general"] in OBJECTIFS_DISPONIBLES:
                self.combo_objectif.set(profil["objectif_general"])
            if profil["date_debut"]:
                date_affichee = profil["date_debut"][:10]
                tk.Label(
                    self, text=f"Apprentissage débuté le {date_affichee}",
                    bg="white", fg="#888", font=("Segoe UI", 9)
                ).pack(anchor="w", padx=20, pady=(20, 0))

        tk.Button(self, text="Enregistrer", command=self._enregistrer).pack(anchor="w", padx=20, pady=20)

    def _enregistrer(self):
        prenom = self.entree_prenom.get().strip()
        langue = self.entree_langue.get().strip() or "Français"
        objectif = self.combo_objectif.get().strip()

        models.enregistrer_profil(prenom, langue, objectif)
        messagebox.showinfo("Profil", "Ton profil a été enregistré.")

    def _afficher_ligne_competence(self, parent, nom, evaluation):
        ligne = tk.Frame(parent, bg="#f0f4ff", padx=12, pady=6)
        ligne.pack(fill="x", pady=2)
        tk.Label(ligne, text=nom, bg="#f0f4ff", width=15, anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left")

        if evaluation["niveau"] is None:
            tk.Label(
                ligne, text="Non évalué — fais quelques quiz pour obtenir une première estimation",
                bg="#f0f4ff", fg="#888", font=("Segoe UI", 9)
            ).pack(side="left")
            return

        tk.Label(
            ligne, text=f"{evaluation['niveau']}  •  {evaluation['score']}%  •  confiance {evaluation['confiance']}%",
            bg="#f0f4ff", font=("Segoe UI", 10)
        ).pack(side="left")
