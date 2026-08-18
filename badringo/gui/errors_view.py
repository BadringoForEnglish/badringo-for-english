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

        # --- Erreurs récurrentes (Error Memory) ---
        self.frame_recurrentes = tk.Frame(self, bg="white")
        self.frame_recurrentes.pack(fill="x", padx=20, pady=(0, 15))

        colonnes = ("original", "correction", "explication", "regle", "date")
        self.arbre = ttk.Treeview(self, columns=colonnes, show="headings", height=16)
        largeurs = (220, 220, 260, 140, 140)
        for c, l in zip(colonnes, largeurs):
            self.arbre.heading(c, text=c.capitalize())
            self.arbre.column(c, width=l)
        self.arbre.pack(fill="both", expand=True, padx=20, pady=10)

        self._rafraichir()

    def _rafraichir(self):
        self._rafraichir_recurrentes()
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

    def _rafraichir_recurrentes(self):
        for widget in self.frame_recurrentes.winfo_children():
            widget.destroy()

        patterns = models.analyser_patterns_erreurs(limite=5)
        # N'affiche le panneau que s'il y a de vraies récurrences (2+ occurrences),
        # sinon il n'apporte rien et encombre l'écran pour rien.
        patterns = [p for p in patterns if p["frequence"] >= 2]
        if not patterns:
            return

        tk.Label(
            self.frame_recurrentes, text="🔁 Erreurs récurrentes", font=("Segoe UI", 12, "bold"), bg="white"
        ).pack(anchor="w")

        for p in patterns:
            ligne = tk.Frame(self.frame_recurrentes, bg="#fff7ed", padx=12, pady=6)
            ligne.pack(fill="x", pady=2)
            tk.Label(
                ligne, text=p["notion"], bg="#fff7ed", font=("Segoe UI", 10, "bold"), anchor="w"
            ).pack(side="left")
            tk.Label(
                ligne, text=f"{p['frequence']} fois  •  dernière fois : {p['derniere_occurrence'][:10]}",
                bg="#fff7ed", fg="#92400e", font=("Segoe UI", 9)
            ).pack(side="right")
