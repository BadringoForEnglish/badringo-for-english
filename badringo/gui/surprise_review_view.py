"""
gui/surprise_review_view.py
Affiche la session de révision surprise construite par
services/surprise_review.py : une suite de cartes mélangées (questions
de vocabulaire à choix multiples + rappels de règle/erreur), présentées
une par une. Les réponses aux questions de vocabulaire alimentent la
répétition espacée et la maîtrise par notion, exactement comme le Quiz
normal — une mauvaise réponse ici influence donc le Plan du jour de
demain (Phase 5), conformément à la demande.
"""

import tkinter as tk

from database import models
from services.surprise_review import construire_session_surprise


class SurpriseReviewView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")

        self.cartes = construire_session_surprise()

        if not self.cartes:
            self._afficher_message_insuffisant()
            return

        self.index_carte = 0
        self.score = 0
        self.total_questions = sum(1 for c in self.cartes if c["carte_type"] == "quiz")
        self.bouton_selectionne = None

        self._build_layout()
        self._afficher_carte()

    # ------------------------------------------------------------------
    def _afficher_message_insuffisant(self):
        tk.Label(self, text="Révision surprise", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )
        tk.Label(
            self,
            text="Pas encore assez de contenu ancien à réviser. Continue à utiliser l'application "
                 "(vocabulaire, grammaire, quiz) et reviens plus tard !",
            bg="white", font=("Segoe UI", 11), wraplength=600, justify="left"
        ).pack(anchor="w", padx=20)

    # ------------------------------------------------------------------
    def _build_layout(self):
        tk.Label(self, text="🎲 Révision surprise", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 5)
        )
        self.progression_label = tk.Label(self, bg="white", font=("Segoe UI", 10), fg="#666")
        self.progression_label.pack(anchor="w", padx=20)

        self.zone_carte = tk.Frame(self, bg="white")
        self.zone_carte.pack(fill="both", expand=True, padx=20, pady=20)

    # ------------------------------------------------------------------
    def _afficher_carte(self):
        for widget in self.zone_carte.winfo_children():
            widget.destroy()
        self.bouton_selectionne = None

        carte = self.cartes[self.index_carte]
        self.progression_label.config(text=f"Carte {self.index_carte + 1} / {len(self.cartes)}")

        if carte["carte_type"] == "quiz":
            self._afficher_carte_quiz(carte)
        elif carte["carte_type"] == "regle":
            self._afficher_carte_regle(carte)
        elif carte["carte_type"] == "erreur":
            self._afficher_carte_erreur(carte)

    def _carte_suivante(self):
        self.index_carte += 1
        if self.index_carte >= len(self.cartes):
            self._afficher_resultat_final()
        else:
            self._afficher_carte()

    # ------------------------------------------------------------------
    # CARTE QUIZ (question de vocabulaire à choix multiples)
    # ------------------------------------------------------------------
    def _afficher_carte_quiz(self, carte):
        tk.Label(
            self.zone_carte, text="Traduis ce mot en français :",
            bg="white", font=("Segoe UI", 11), fg="#555"
        ).pack(pady=(10, 5))
        tk.Label(
            self.zone_carte, text=carte["texte"], bg="white", font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 20))

        choix_frame = tk.Frame(self.zone_carte, bg="white")
        choix_frame.pack()
        self.boutons_choix = []
        for i, option in enumerate(carte["options"]):
            btn = tk.Button(
                choix_frame, text=option, font=("Segoe UI", 12), width=30, pady=12,
                relief="flat", bg="#f0f4ff",
                command=lambda i=i: self._repondre_quiz(i, carte)
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=8)
            self.boutons_choix.append(btn)

        self.feedback_label = tk.Label(self.zone_carte, text="", bg="white", font=("Segoe UI", 12, "bold"))
        self.feedback_label.pack(pady=10)

        self.bouton_suivant = tk.Button(
            self.zone_carte, text="Carte suivante →", font=("Segoe UI", 11),
            command=self._carte_suivante, state="disabled"
        )
        self.bouton_suivant.pack(pady=10)

    def _repondre_quiz(self, index_bouton, carte):
        if self.bouton_selectionne is not None:
            return
        self.bouton_selectionne = index_bouton

        option_choisie = carte["options"][index_bouton]
        correct = option_choisie == carte["reponse"]

        for i, btn in enumerate(self.boutons_choix):
            btn.config(state="disabled")
            if carte["options"][i] == carte["reponse"]:
                btn.config(bg="#bbf7d0")
            elif i == index_bouton:
                btn.config(bg="#fecaca")

        if correct:
            self.score += 1
            self.feedback_label.config(text="✔ Toujours dans le coin de ta tête !", fg="#16a34a")
        else:
            self.feedback_label.config(
                text=f"✘ La bonne réponse était : {carte['reponse']}", fg="#dc2626"
            )

        # Une erreur ici influence directement le Plan du jour de demain
        # (Phase 5), via les mêmes signaux que le Quiz normal.
        models.reviser_mot(carte["mot_id"], correct)
        models.mettre_a_jour_maitrise(carte["notion"], correct)

        self.bouton_suivant.config(state="normal")

    # ------------------------------------------------------------------
    # CARTE RAPPEL DE RÈGLE DE GRAMMAIRE
    # ------------------------------------------------------------------
    def _afficher_carte_regle(self, carte):
        tk.Label(
            self.zone_carte, text="📖 Petit rappel de grammaire", bg="white",
            font=("Segoe UI", 11), fg="#555"
        ).pack(pady=(10, 15))
        tk.Label(
            self.zone_carte, text=carte["titre"], bg="white", font=("Segoe UI", 16, "bold"),
            wraplength=700, justify="center"
        ).pack(pady=(0, 10))
        tk.Label(
            self.zone_carte, text=carte["explication"], bg="white", font=("Segoe UI", 11),
            wraplength=700, justify="center"
        ).pack(pady=(0, 10))
        if carte["exemples"]:
            tk.Label(
                self.zone_carte, text=f"Exemples : {carte['exemples']}", bg="white",
                fg="#666", font=("Segoe UI", 10), wraplength=700, justify="center"
            ).pack()

        tk.Button(
            self.zone_carte, text="J'ai révisé, continuer →", font=("Segoe UI", 11),
            command=self._carte_suivante
        ).pack(pady=20)

    # ------------------------------------------------------------------
    # CARTE RAPPEL D'ERREUR RÉCURRENTE
    # ------------------------------------------------------------------
    def _afficher_carte_erreur(self, carte):
        tk.Label(
            self.zone_carte, text="⚠ Attention à cette erreur récurrente", bg="white",
            font=("Segoe UI", 11), fg="#555"
        ).pack(pady=(10, 15))
        tk.Label(
            self.zone_carte, text=carte["notion"], bg="white", font=("Segoe UI", 16, "bold"),
            wraplength=700, justify="center"
        ).pack(pady=(0, 10))
        tk.Label(
            self.zone_carte, text=f"Tu as fait cette erreur {carte['frequence']} fois.",
            bg="white", fg="#888", font=("Segoe UI", 10)
        ).pack()

        tk.Button(
            self.zone_carte, text="Compris, continuer →", font=("Segoe UI", 11),
            command=self._carte_suivante
        ).pack(pady=20)

    # ------------------------------------------------------------------
    def _afficher_resultat_final(self):
        if self.total_questions > 0:
            models.enregistrer_session_quiz(self.score, self.total_questions)

        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Révision surprise terminée !", font=("Segoe UI", 20, "bold"), bg="white", pady=30).pack()

        if self.total_questions > 0:
            pourcentage = round(100 * self.score / self.total_questions)
            tk.Label(
                self, text=f"Score : {self.score} / {self.total_questions}  ({pourcentage}%)",
                font=("Segoe UI", 16), bg="white"
            ).pack(pady=10)
        else:
            tk.Label(self, text="Rappels passés en revue.", font=("Segoe UI", 14), bg="white").pack(pady=10)

        tk.Label(
            self, text="Reviens quand tu veux pour une nouvelle surprise !",
            bg="white", fg="#666", font=("Segoe UI", 10)
        ).pack(pady=5)
