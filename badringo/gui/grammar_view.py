"""
gui/grammar_view.py
Fiches de règles de conjugaison et de grammaire générale.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import models


class GrammarView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Grammaire & Conjugaison", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        form = tk.Frame(self, bg="white")
        form.pack(fill="x", padx=20, pady=10)

        tk.Label(form, text="Catégorie", bg="white").grid(row=0, column=0, sticky="w")
        self.categorie = ttk.Combobox(form, values=["conjugaison", "grammaire"], width=15, state="readonly")
        self.categorie.set("conjugaison")
        self.categorie.grid(row=1, column=0, padx=(0, 10))

        tk.Label(form, text="Titre", bg="white").grid(row=0, column=1, sticky="w")
        self.titre = tk.Entry(form, width=25)
        self.titre.grid(row=1, column=1, padx=(0, 10))

        tk.Label(form, text="Explication", bg="white").grid(row=0, column=2, sticky="w")
        self.explication = tk.Entry(form, width=40)
        self.explication.grid(row=1, column=2, padx=(0, 10))

        tk.Label(form, text="Exemples", bg="white").grid(row=0, column=3, sticky="w")
        self.exemples = tk.Entry(form, width=30)
        self.exemples.grid(row=1, column=3)

        tk.Button(form, text="Ajouter", command=self.ajouter_regle).grid(row=1, column=4, padx=10)

        # Liste
        self.liste_frame = tk.Frame(self, bg="white")
        self.liste_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._rafraichir()

    def ajouter_regle(self):
        titre = self.titre.get().strip()
        explication = self.explication.get().strip()
        if not titre or not explication:
            messagebox.showwarning("Champs manquants", "Le titre et l'explication sont obligatoires.")
            return
        models.ajouter_regle(self.categorie.get(), titre, explication, self.exemples.get().strip())
        for e in (self.titre, self.explication, self.exemples):
            e.delete(0, tk.END)
        self._rafraichir()

    def _rafraichir(self):
        for widget in self.liste_frame.winfo_children():
            widget.destroy()

        regles = models.lister_regles()
        if not regles:
            tk.Label(self.liste_frame, text="Aucune règle enregistrée pour le moment.", bg="white").pack(anchor="w")
            return

        for r in regles:
            carte = tk.Frame(self.liste_frame, bg="#f0f0f0", padx=10, pady=8)
            carte.pack(fill="x", pady=4)
            tk.Label(
                carte, text=f"[{r['categorie']}] {r['titre']}", font=("Segoe UI", 11, "bold"), bg="#f0f0f0"
            ).pack(anchor="w")
            tk.Label(carte, text=r["explication"], bg="#f0f0f0", wraplength=800, justify="left").pack(anchor="w")
            if r["exemples"]:
                tk.Label(carte, text=f"Exemples : {r['exemples']}", bg="#f0f0f0", fg="#555", wraplength=800, justify="left").pack(anchor="w")
            tk.Button(carte, text="Supprimer", command=lambda rid=r["id"]: self._supprimer(rid)).pack(anchor="e")

    def _supprimer(self, regle_id):
        models.supprimer_regle(regle_id)
        self._rafraichir()
