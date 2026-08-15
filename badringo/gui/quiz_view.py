"""
gui/quiz_view.py
Quiz auto-généré à partir du vocabulaire enregistré : questions à choix
multiples (EN -> FR), avec score final et mise à jour de la révision
espacée selon les bonnes/mauvaises réponses.
"""

import random
import tkinter as tk
from tkinter import messagebox

from database import models

NB_QUESTIONS_MAX = 10
NB_CHOIX = 4


class QuizView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")

        self.mots = list(models.lister_mots())

        if len(self.mots) < NB_CHOIX:
            self._afficher_message_insuffisant()
            return

        self.questions = random.sample(self.mots, min(NB_QUESTIONS_MAX, len(self.mots)))
        self.index_question = 0
        self.score = 0
        self.bouton_selectionne = None

        self._build_layout()
        self._afficher_question()

    # ------------------------------------------------------------------
    def _afficher_message_insuffisant(self):
        tk.Label(
            self, text="Quiz", font=("Segoe UI", 16, "bold"), bg="white"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        tk.Label(
            self,
            text=f"Il faut au moins {NB_CHOIX} mots enregistrés dans le Vocabulaire "
                 f"pour générer un quiz. Ajoute quelques mots puis reviens ici !",
            bg="white", font=("Segoe UI", 11), wraplength=600, justify="left"
        ).pack(anchor="w", padx=20)

    # ------------------------------------------------------------------
    def _build_layout(self):
        self.entete = tk.Label(self, text="Quiz", font=("Segoe UI", 16, "bold"), bg="white")
        self.entete.pack(anchor="w", padx=20, pady=(20, 5))

        self.progression_label = tk.Label(self, bg="white", font=("Segoe UI", 10), fg="#666")
        self.progression_label.pack(anchor="w", padx=20)

        self.question_label = tk.Label(
            self, text="", bg="white", font=("Segoe UI", 20, "bold"), pady=30
        )
        self.question_label.pack(anchor="center")

        self.choix_frame = tk.Frame(self, bg="white")
        self.choix_frame.pack(pady=10)
        self.boutons_choix = []
        for i in range(NB_CHOIX):
            btn = tk.Button(
                self.choix_frame, text="", font=("Segoe UI", 12), width=30, pady=12,
                relief="flat", bg="#f0f4ff",
                command=lambda i=i: self._selectionner_reponse(i)
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=8)
            self.boutons_choix.append(btn)

        self.feedback_label = tk.Label(self, text="", bg="white", font=("Segoe UI", 12, "bold"))
        self.feedback_label.pack(pady=10)

        self.bouton_suivant = tk.Button(
            self, text="Question suivante →", font=("Segoe UI", 11),
            command=self._question_suivante, state="disabled"
        )
        self.bouton_suivant.pack(pady=10)

    # ------------------------------------------------------------------
    def _generer_options(self, mot_correct):
        """Renvoie une liste de NB_CHOIX traductions mélangées, dont la bonne."""
        autres = [m for m in self.mots if m["id"] != mot_correct["id"]]
        distracteurs = random.sample(autres, min(NB_CHOIX - 1, len(autres)))
        options = [mot_correct] + distracteurs
        random.shuffle(options)
        return options

    def _afficher_question(self):
        self.bouton_selectionne = None
        self.feedback_label.config(text="")
        self.bouton_suivant.config(state="disabled")

        mot = self.questions[self.index_question]
        self.mot_actuel = mot
        self.options_actuelles = self._generer_options(mot)

        self.progression_label.config(
            text=f"Question {self.index_question + 1} / {len(self.questions)}  •  Score : {self.score}"
        )
        self.question_label.config(text=mot["mot"])

        for btn, option in zip(self.boutons_choix, self.options_actuelles):
            btn.config(text=option["traduction"], bg="#f0f4ff", state="normal")

    def _selectionner_reponse(self, index_bouton):
        if self.bouton_selectionne is not None:
            return  # déjà répondu à cette question

        self.bouton_selectionne = index_bouton
        option_choisie = self.options_actuelles[index_bouton]
        correct = option_choisie["id"] == self.mot_actuel["id"]

        for i, btn in enumerate(self.boutons_choix):
            btn.config(state="disabled")
            if self.options_actuelles[i]["id"] == self.mot_actuel["id"]:
                btn.config(bg="#bbf7d0")  # bonne réponse en vert
            elif i == index_bouton:
                btn.config(bg="#fecaca")  # mauvaise réponse choisie en rouge

        if correct:
            self.score += 1
            self.feedback_label.config(text="✔ Bonne réponse !", fg="#16a34a")
        else:
            self.feedback_label.config(
                text=f"✘ La bonne réponse était : {self.mot_actuel['traduction']}", fg="#dc2626"
            )

        models.reviser_mot(self.mot_actuel["id"], correct)
        self.bouton_suivant.config(state="normal")

    def _question_suivante(self):
        self.index_question += 1
        if self.index_question >= len(self.questions):
            self._afficher_resultat_final()
        else:
            self._afficher_question()

    def _afficher_resultat_final(self):
        for widget in self.winfo_children():
            widget.destroy()

        total = len(self.questions)
        pourcentage = round(100 * self.score / total)

        tk.Label(self, text="Quiz terminé !", font=("Segoe UI", 20, "bold"), bg="white", pady=30).pack()
        tk.Label(
            self, text=f"Score : {self.score} / {total}  ({pourcentage}%)",
            font=("Segoe UI", 16), bg="white"
        ).pack(pady=10)

        message = "Excellent travail ! 🎉" if pourcentage >= 80 else (
            "Bien joué, continue comme ça !" if pourcentage >= 50 else
            "Pas mal, encore un peu de pratique et ce sera parfait."
        )
        tk.Label(self, text=message, font=("Segoe UI", 12), bg="white", fg="#666").pack(pady=5)

        tk.Button(
            self, text="Refaire un quiz", font=("Segoe UI", 11),
            command=self._recommencer
        ).pack(pady=20)

    def _recommencer(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.mots = list(models.lister_mots())
        if len(self.mots) < NB_CHOIX:
            self._afficher_message_insuffisant()
            return
        self.questions = random.sample(self.mots, min(NB_QUESTIONS_MAX, len(self.mots)))
        self.index_question = 0
        self.score = 0
        self._build_layout()
        self._afficher_question()
