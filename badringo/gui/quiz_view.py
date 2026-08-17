"""
gui/quiz_view.py
Quiz éducatif mêlant plusieurs types de questions :
- Vocabulaire EN -> FR et FR -> EN (dans les deux sens)
- Questions à trous à partir des phrases d'exemple enregistrées
- Conjugaison (verbes irréguliers courants)

Les mots dus pour révision (répétition espacée) sont priorisés. Chaque
session est enregistrée pour suivre la progression dans le temps.
"""

import random
import re
import tkinter as tk

from database import models
from services.conjugaison import VERBES_IRREGULIERS

NB_QUESTIONS_MAX = 10
NB_CHOIX = 4
NB_QUESTIONS_CONJUGAISON = 3  # nombre cible de questions de conjugaison mêlées au quiz


class QuizView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")

        self.questions = self._construire_questions()

        if not self.questions:
            self._afficher_message_insuffisant()
            return

        self.index_question = 0
        self.score = 0
        self.bouton_selectionne = None

        self._build_layout()
        self._afficher_question()

    # ------------------------------------------------------------------
    # CONSTRUCTION DES QUESTIONS
    # ------------------------------------------------------------------
    def _construire_questions(self):
        questions = []
        questions += self._construire_questions_vocabulaire()
        questions += self._construire_questions_conjugaison()
        random.shuffle(questions)
        return questions[:NB_QUESTIONS_MAX]

    def _construire_questions_vocabulaire(self):
        tous_mots = list(models.lister_mots())
        if len(tous_mots) < NB_CHOIX:
            return []

        # Priorité aux mots dus pour révision, puis complète avec le reste
        dus = list(models.lister_mots(a_reviser_seulement=True))
        ids_dus = {m["id"] for m in dus}
        autres = [m for m in tous_mots if m["id"] not in ids_dus]
        mots_ordonnes = dus + autres

        nb_a_generer = min(NB_QUESTIONS_MAX - NB_QUESTIONS_CONJUGAISON, len(mots_ordonnes))
        nb_a_generer = max(nb_a_generer, 0)
        mots_choisis = mots_ordonnes[:nb_a_generer]

        questions = []
        for mot in mots_choisis:
            # Question à trous si le mot apparaît bien dans son propre exemple
            if mot["exemple"] and self._mot_dans_exemple(mot["mot"], mot["exemple"]) and random.random() < 0.3:
                q = self._question_a_trou(mot, tous_mots)
                if q:
                    questions.append(q)
                    continue

            # Sinon, question classique EN->FR ou FR->EN (aléatoire)
            if random.random() < 0.5:
                questions.append(self._question_vocabulaire(mot, tous_mots, sens="en_fr"))
            else:
                questions.append(self._question_vocabulaire(mot, tous_mots, sens="fr_en"))

        return questions

    def _mot_dans_exemple(self, mot, exemple):
        return re.search(rf"\b{re.escape(mot)}\b", exemple, flags=re.IGNORECASE) is not None

    def _question_a_trou(self, mot, tous_mots):
        phrase_trouee = re.sub(
            rf"\b{re.escape(mot['mot'])}\b", "_____", mot["exemple"], count=1, flags=re.IGNORECASE
        )
        autres = [m["mot"] for m in tous_mots if m["id"] != mot["id"]]
        if len(autres) < NB_CHOIX - 1:
            return None
        distracteurs = random.sample(autres, NB_CHOIX - 1)
        options = [mot["mot"]] + distracteurs
        random.shuffle(options)
        return {
            "type": "trou",
            "mot_id": mot["id"],
            "consigne": "Complète la phrase :",
            "texte": phrase_trouee,
            "options": options,
            "reponse": mot["mot"],
        }

    def _question_vocabulaire(self, mot, tous_mots, sens):
        autres = [m for m in tous_mots if m["id"] != mot["id"]]
        distracteurs = random.sample(autres, min(NB_CHOIX - 1, len(autres)))

        if sens == "en_fr":
            consigne = "Traduis ce mot en français :"
            texte = mot["mot"]
            reponse = mot["traduction"]
            options = [mot["traduction"]] + [d["traduction"] for d in distracteurs]
        else:
            consigne = "Traduis ce mot en anglais :"
            texte = mot["traduction"]
            reponse = mot["mot"]
            options = [mot["mot"]] + [d["mot"] for d in distracteurs]

        random.shuffle(options)
        return {
            "type": "vocabulaire",
            "mot_id": mot["id"],
            "consigne": consigne,
            "texte": texte,
            "options": options,
            "reponse": reponse,
        }

    def _construire_questions_conjugaison(self):
        if len(VERBES_IRREGULIERS) < NB_CHOIX:
            return []

        verbes_choisis = random.sample(VERBES_IRREGULIERS, min(NB_QUESTIONS_CONJUGAISON, len(VERBES_IRREGULIERS)))
        questions = []
        for base, passe, participe, traduction in verbes_choisis:
            demander_participe = random.random() < 0.5
            forme_visee = participe if demander_participe else passe
            consigne = f"'{base}' → participe passé ?" if demander_participe else f"'{base}' → passé simple ?"

            autres = [v for v in VERBES_IRREGULIERS if v[0] != base]
            distracteurs_tuples = random.sample(autres, min(NB_CHOIX - 1, len(autres)))
            distracteurs = [(t[2] if demander_participe else t[1]) for t in distracteurs_tuples]

            options = [forme_visee] + distracteurs
            random.shuffle(options)
            questions.append({
                "type": "conjugaison",
                "mot_id": None,
                "consigne": consigne,
                "texte": "",
                "options": options,
                "reponse": forme_visee,
            })
        return questions

    # ------------------------------------------------------------------
    def _afficher_message_insuffisant(self):
        tk.Label(
            self, text="Quiz", font=("Segoe UI", 16, "bold"), bg="white"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        tk.Label(
            self,
            text="Pas encore assez de contenu pour générer un quiz. Ajoute quelques mots "
                 "dans le Vocabulaire, ou reviens plus tard !",
            bg="white", font=("Segoe UI", 11), wraplength=600, justify="left"
        ).pack(anchor="w", padx=20)

    # ------------------------------------------------------------------
    def _build_layout(self):
        tk.Label(self, text="Quiz", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 5)
        )

        self.progression_label = tk.Label(self, bg="white", font=("Segoe UI", 10), fg="#666")
        self.progression_label.pack(anchor="w", padx=20)

        self.consigne_label = tk.Label(self, text="", bg="white", font=("Segoe UI", 11), fg="#555")
        self.consigne_label.pack(pady=(20, 5))

        self.question_label = tk.Label(
            self, text="", bg="white", font=("Segoe UI", 18, "bold"), wraplength=700, justify="center"
        )
        self.question_label.pack(pady=(0, 20))

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
    def _afficher_question(self):
        self.bouton_selectionne = None
        self.feedback_label.config(text="")
        self.bouton_suivant.config(state="disabled")

        question = self.questions[self.index_question]

        self.progression_label.config(
            text=f"Question {self.index_question + 1} / {len(self.questions)}  •  Score : {self.score}"
        )
        self.consigne_label.config(text=question["consigne"])
        self.question_label.config(text=question["texte"])

        for btn, option in zip(self.boutons_choix, question["options"]):
            btn.config(text=option, bg="#f0f4ff", state="normal")

    def _selectionner_reponse(self, index_bouton):
        if self.bouton_selectionne is not None:
            return

        self.bouton_selectionne = index_bouton
        question = self.questions[self.index_question]
        option_choisie = question["options"][index_bouton]
        correct = option_choisie == question["reponse"]

        for i, btn in enumerate(self.boutons_choix):
            btn.config(state="disabled")
            if question["options"][i] == question["reponse"]:
                btn.config(bg="#bbf7d0")
            elif i == index_bouton:
                btn.config(bg="#fecaca")

        if correct:
            self.score += 1
            self.feedback_label.config(text="✔ Bonne réponse !", fg="#16a34a")
        else:
            self.feedback_label.config(
                text=f"✘ La bonne réponse était : {question['reponse']}", fg="#dc2626"
            )

        if question["mot_id"] is not None:
            models.reviser_mot(question["mot_id"], correct)

        self.bouton_suivant.config(state="normal")

    def _question_suivante(self):
        self.index_question += 1
        if self.index_question >= len(self.questions):
            self._afficher_resultat_final()
        else:
            self._afficher_question()

    def _afficher_resultat_final(self):
        total = len(self.questions)
        models.enregistrer_session_quiz(self.score, total)

        for widget in self.winfo_children():
            widget.destroy()

        pourcentage = round(100 * self.score / total) if total else 0

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
        self.questions = self._construire_questions()
        if not self.questions:
            self._afficher_message_insuffisant()
            return
        self.index_question = 0
        self.score = 0
        self._build_layout()
        self._afficher_question()
