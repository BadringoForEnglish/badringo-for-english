"""
gui/vocab_view.py
Ajout, liste et révision du vocabulaire (répétition espacée).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import models


class VocabView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Vocabulaire", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        # --- Formulaire d'ajout ---
        form = tk.Frame(self, bg="white")
        form.pack(fill="x", padx=20, pady=10)

        tk.Label(form, text="Mot (EN)", bg="white").grid(row=0, column=0, sticky="w")
        self.entree_mot = tk.Entry(form, width=20)
        self.entree_mot.grid(row=1, column=0, padx=(0, 10))

        tk.Label(form, text="Traduction (FR)", bg="white").grid(row=0, column=1, sticky="w")
        self.entree_traduction = tk.Entry(form, width=20)
        self.entree_traduction.grid(row=1, column=1, padx=(0, 10))

        tk.Label(form, text="Exemple", bg="white").grid(row=0, column=2, sticky="w")
        self.entree_exemple = tk.Entry(form, width=30)
        self.entree_exemple.grid(row=1, column=2, padx=(0, 10))

        tk.Label(form, text="Thème", bg="white").grid(row=0, column=3, sticky="w")
        self.entree_theme = tk.Entry(form, width=15)
        self.entree_theme.insert(0, "general")
        self.entree_theme.grid(row=1, column=3)

        tk.Button(form, text="Ajouter", command=self.ajouter_mot).grid(row=1, column=4, padx=10)

        # --- Liste des mots ---
        colonnes = ("mot", "traduction", "theme", "niveau", "prochaine_revision")
        self.arbre = ttk.Treeview(self, columns=colonnes, show="headings", height=15)
        for c, largeur in zip(colonnes, (150, 150, 100, 100, 160)):
            self.arbre.heading(c, text=c.capitalize())
            self.arbre.column(c, width=largeur)
        self.arbre.pack(fill="both", expand=True, padx=20, pady=10)

        bas = tk.Frame(self, bg="white")
        bas.pack(fill="x", padx=20, pady=(0, 20))
        tk.Button(bas, text="✔ Marquer réussi (révision)", command=lambda: self._reviser(True)).pack(side="left")
        tk.Button(bas, text="✘ Marquer raté (révision)", command=lambda: self._reviser(False)).pack(side="left", padx=10)
        tk.Button(bas, text="Supprimer", command=self._supprimer).pack(side="left")

        self._rafraichir()

    def ajouter_mot(self):
        mot = self.entree_mot.get().strip()
        traduction = self.entree_traduction.get().strip()
        if not mot or not traduction:
            messagebox.showwarning("Champs manquants", "Le mot et la traduction sont obligatoires.")
            return
        models.ajouter_mot(mot, traduction, self.entree_exemple.get().strip(), self.entree_theme.get().strip() or "general")
        for e in (self.entree_mot, self.entree_traduction, self.entree_exemple):
            e.delete(0, tk.END)
        self._rafraichir()

    def _rafraichir(self):
        for item in self.arbre.get_children():
            self.arbre.delete(item)
        for row in models.lister_mots():
            niveau_txt = {0: "Nouveau", 1: "En cours", 2: "Maîtrisé"}[row["niveau_maitrise"]]
            self.arbre.insert(
                "", "end", iid=row["id"],
                values=(row["mot"], row["traduction"], row["theme"], niveau_txt, row["prochaine_revision"])
            )

    def _selection_id(self):
        sel = self.arbre.selection()
        return int(sel[0]) if sel else None

    def _reviser(self, reussi):
        mot_id = self._selection_id()
        if mot_id is None:
            messagebox.showinfo("Sélection", "Sélectionne d'abord un mot dans la liste.")
            return
        models.reviser_mot(mot_id, reussi)
        self._rafraichir()

    def _supprimer(self):
        mot_id = self._selection_id()
        if mot_id is None:
            return
        models.supprimer_mot(mot_id)
        self._rafraichir()
