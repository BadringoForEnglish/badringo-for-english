"""
gui/errors_view.py
Journal des erreurs : phrase fautive -> correction -> explication.
Alimenté manuellement ou automatiquement depuis le chat IA.
"""

import tkinter as tk
from tkinter import ttk

from database import models


class ErrorsView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Journal d'erreurs", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        colonnes = ("original", "correction", "explication", "regle", "date")
        self.arbre = ttk.Treeview(self, columns=colonnes, show="headings", height=20)
        largeurs = (220, 220, 260, 140, 140)
        for c, l in zip(colonnes, largeurs):
            self.arbre.heading(c, text=c.capitalize())
            self.arbre.column(c, width=l)
        self.arbre.pack(fill="both", expand=True, padx=20, pady=10)

        self._rafraichir()

    def _rafraichir(self):
        for item in self.arbre.get_children():
            self.arbre.delete(item)
        for e in models.lister_erreurs():
            self.arbre.insert(
                "", "end",
                values=(
                    e["phrase_originale"], e["phrase_corrigee"], e["explication"] or "",
                    e["regle_titre"] or "-", e["date_ajout"]
                )
            )
