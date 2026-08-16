"""
gui/vocab_view.py
Ajout, liste et révision du vocabulaire (répétition espacée).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from database import models
from services.ai_service import traduire_mot


class VocabView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Vocabulaire", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        # --- Traducteur EN -> FR (via Ollama), mot, expression ou phrase ---
        traducteur = tk.Frame(self, bg="#f0f4ff", padx=15, pady=10)
        traducteur.pack(fill="x", padx=20, pady=(0, 15))

        tk.Label(traducteur, text="Traducteur : texte en anglais →", bg="#f0f4ff").pack(side="left", anchor="n")

        self.entree_source = tk.Text(traducteur, width=30, height=2, wrap="word")
        self.entree_source.pack(side="left", padx=5)
        self.entree_source.bind("<Return>", self._touche_traducteur)

        self.bouton_traduire = tk.Button(traducteur, text="Traduire", command=self.traduire)
        self.bouton_traduire.pack(side="left", padx=5, anchor="n")

        self.resultat_traduction = tk.Text(
            traducteur, width=35, height=2, wrap="word", state="disabled", bg="#f0f4ff", relief="flat"
        )
        self.resultat_traduction.pack(side="left", padx=10)

        self.bouton_utiliser_traduction = tk.Button(
            traducteur, text="↓ Utiliser dans le formulaire", command=self._utiliser_traduction, state="disabled"
        )
        self.bouton_utiliser_traduction.pack(side="left", padx=5, anchor="n")

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
        self.entree_exemple = tk.Text(form, width=30, height=3, wrap="word")
        self.entree_exemple.grid(row=1, column=2, padx=(0, 10))

        tk.Label(form, text="Thème", bg="white").grid(row=0, column=3, sticky="w")
        self.entree_theme = tk.Entry(form, width=15)
        self.entree_theme.insert(0, "general")
        self.entree_theme.grid(row=1, column=3)

        tk.Button(form, text="Ajouter", command=self.ajouter_mot).grid(row=1, column=4, padx=10)

        # --- Liste des mots ---
        colonnes = ("mot", "traduction", "exemple", "theme", "niveau", "prochaine_revision")
        self.arbre = ttk.Treeview(self, columns=colonnes, show="headings", height=12)
        largeurs = {"mot": 120, "traduction": 120, "exemple": 250, "theme": 90, "niveau": 90, "prochaine_revision": 150}
        for c in colonnes:
            self.arbre.heading(c, text=c.capitalize())
            self.arbre.column(c, width=largeurs[c])
        self.arbre.pack(fill="both", expand=True, padx=20, pady=10)
        self.arbre.bind("<<TreeviewSelect>>", self._afficher_detail_exemple)

        # --- Détail de l'exemple sélectionné (affiche les retours à la ligne) ---
        detail_frame = tk.Frame(self, bg="white")
        detail_frame.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(detail_frame, text="Exemple complet :", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.detail_exemple = tk.Text(detail_frame, height=3, wrap="word", state="disabled", bg="#f5f5f5")
        self.detail_exemple.pack(fill="x")

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
        exemple = self.entree_exemple.get("1.0", "end").strip()
        models.ajouter_mot(mot, traduction, exemple, self.entree_theme.get().strip() or "general")
        self.entree_mot.delete(0, tk.END)
        self.entree_traduction.delete(0, tk.END)
        self.entree_exemple.delete("1.0", "end")
        self._rafraichir()

    def _touche_traducteur(self, event):
        """Entrée seule lance la traduction ; Maj+Entrée insère un retour à la ligne."""
        if event.state & 0x1:  # touche Maj (Shift) enfoncée
            return None
        self.traduire()
        return "break"

    def traduire(self):
        texte_en = self.entree_source.get("1.0", "end").strip()
        if not texte_en:
            return
        self.bouton_traduire.config(state="disabled", text="...")
        self.resultat_traduction.config(state="normal")
        self.resultat_traduction.delete("1.0", "end")
        self.resultat_traduction.config(state="disabled")
        self.bouton_utiliser_traduction.config(state="disabled")

        thread = threading.Thread(target=self._traduire_en_arriere_plan, args=(texte_en,), daemon=True)
        thread.start()

    def _traduire_en_arriere_plan(self, texte_en):
        resultat = traduire_mot(texte_en)
        self.after(0, self._traiter_traduction, texte_en, resultat)

    def _traiter_traduction(self, texte_en, resultat):
        self.bouton_traduire.config(state="normal", text="Traduire")
        self.resultat_traduction.config(state="normal")
        self.resultat_traduction.delete("1.0", "end")

        if resultat is None:
            self.resultat_traduction.insert("1.0", "Traduction indisponible (vérifie qu'Ollama tourne).")
            self.resultat_traduction.config(state="disabled")
            return

        self._derniere_traduction = {
            "texte_en": texte_en,
            "traduction_fr": resultat["traduction"],
            "exemple": resultat.get("exemple", "") or texte_en
        }
        self.resultat_traduction.insert("1.0", resultat["traduction"])
        self.resultat_traduction.config(state="disabled")
        self.bouton_utiliser_traduction.config(state="normal")

    def _utiliser_traduction(self):
        if not hasattr(self, "_derniere_traduction"):
            return
        infos = self._derniere_traduction
        self.entree_mot.delete(0, tk.END)
        self.entree_mot.insert(0, infos["texte_en"])
        self.entree_traduction.delete(0, tk.END)
        self.entree_traduction.insert(0, infos["traduction_fr"])
        self.entree_exemple.delete("1.0", "end")
        self.entree_exemple.insert("1.0", infos["exemple"])

    def _rafraichir(self):
        for item in self.arbre.get_children():
            self.arbre.delete(item)
        for row in models.lister_mots():
            niveau_txt = {0: "Nouveau", 1: "En cours", 2: "Maîtrisé"}[row["niveau_maitrise"]]
            # Aperçu sur une seule ligne pour le tableau (le détail complet
            # avec les retours à la ligne s'affiche en dessous à la sélection).
            exemple_apercu = (row["exemple"] or "").replace("\n", "  ⏎  ")
            self.arbre.insert(
                "", "end", iid=row["id"],
                values=(row["mot"], row["traduction"], exemple_apercu, row["theme"], niveau_txt, row["prochaine_revision"])
            )

    def _afficher_detail_exemple(self, event=None):
        mot_id = self._selection_id()
        self.detail_exemple.config(state="normal")
        self.detail_exemple.delete("1.0", "end")
        if mot_id is not None:
            for row in models.lister_mots():
                if row["id"] == mot_id:
                    self.detail_exemple.insert("1.0", row["exemple"] or "")
                    break
        self.detail_exemple.config(state="disabled")

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
