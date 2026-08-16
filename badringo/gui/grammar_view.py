"""
gui/grammar_view.py
Trois sections regroupées sous un même onglet :
- Mes règles : fiches de grammaire/conjugaison ajoutées manuellement
- Conjugueur : génère automatiquement les formes d'un verbe anglais
- Verbes irréguliers : liste de référence des verbes irréguliers courants
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import models
from services.conjugaison import conjuguer, VERBES_IRREGULIERS


class GrammarView(tk.Frame):
    def __init__(self, parent, theme="light"):
        super().__init__(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(self, text="Grammaire & Conjugaison", font=("Segoe UI", 16, "bold"), bg="white").pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        onglet_regles = tk.Frame(onglets, bg="white")
        onglet_conjugueur = tk.Frame(onglets, bg="white")
        onglet_irreguliers = tk.Frame(onglets, bg="white")

        onglets.add(onglet_regles, text="Mes règles")
        onglets.add(onglet_conjugueur, text="Conjugueur")
        onglets.add(onglet_irreguliers, text="Verbes irréguliers")

        self._build_onglet_regles(onglet_regles)
        self._build_onglet_conjugueur(onglet_conjugueur)
        self._build_onglet_irreguliers(onglet_irreguliers)

    # ==================================================================
    # ONGLET 1 : Mes règles (fonctionnalité existante, inchangée)
    # ==================================================================
    def _build_onglet_regles(self, parent):
        form = tk.Frame(parent, bg="white")
        form.pack(fill="x", padx=10, pady=10)

        ligne_haut = tk.Frame(form, bg="white")
        ligne_haut.pack(fill="x")

        tk.Label(ligne_haut, text="Catégorie", bg="white").grid(row=0, column=0, sticky="w")
        self.categorie = ttk.Combobox(ligne_haut, values=["conjugaison", "grammaire"], width=15, state="readonly")
        self.categorie.set("conjugaison")
        self.categorie.grid(row=1, column=0, padx=(0, 10), sticky="w")

        tk.Label(ligne_haut, text="Titre", bg="white").grid(row=0, column=1, sticky="w")
        self.titre = tk.Entry(ligne_haut, width=40)
        self.titre.grid(row=1, column=1, padx=(0, 10), sticky="w")

        tk.Button(ligne_haut, text="Ajouter", command=self.ajouter_regle).grid(row=1, column=2, padx=10)

        # Zones multi-lignes : Explication / Commentaire / Exemples, côte à côte.
        # Contrairement à un Entry classique, un Text permet d'aller à la ligne
        # (touche Entrée) en tapant du texte plus long.
        ligne_textes = tk.Frame(form, bg="white")
        ligne_textes.pack(fill="x", pady=(10, 0))

        tk.Label(ligne_textes, text="Explication", bg="white").grid(row=0, column=0, sticky="w")
        self.explication = tk.Text(ligne_textes, width=30, height=4, wrap="word")
        self.explication.grid(row=1, column=0, padx=(0, 10), sticky="w")

        tk.Label(ligne_textes, text="Commentaire", bg="white").grid(row=0, column=1, sticky="w")
        self.commentaire = tk.Text(ligne_textes, width=30, height=4, wrap="word")
        self.commentaire.grid(row=1, column=1, padx=(0, 10), sticky="w")

        tk.Label(ligne_textes, text="Exemples", bg="white").grid(row=0, column=2, sticky="w")
        self.exemples = tk.Text(ligne_textes, width=30, height=4, wrap="word")
        self.exemples.grid(row=1, column=2, sticky="w")

        self.liste_frame = tk.Frame(parent, bg="white")
        self.liste_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._rafraichir_regles()

    def ajouter_regle(self):
        titre = self.titre.get().strip()
        explication = self.explication.get("1.0", "end").strip()
        commentaire = self.commentaire.get("1.0", "end").strip()
        exemples = self.exemples.get("1.0", "end").strip()
        if not titre or not explication:
            messagebox.showwarning("Champs manquants", "Le titre et l'explication sont obligatoires.")
            return
        models.ajouter_regle(self.categorie.get(), titre, explication, commentaire, exemples)
        self.titre.delete(0, tk.END)
        for zone in (self.explication, self.commentaire, self.exemples):
            zone.delete("1.0", "end")
        self._rafraichir_regles()

    def _rafraichir_regles(self):
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
            if r["commentaire"]:
                tk.Label(carte, text=f"Commentaire : {r['commentaire']}", bg="#f0f0f0", fg="#2563eb", wraplength=800, justify="left").pack(anchor="w")
            if r["exemples"]:
                tk.Label(carte, text=f"Exemples : {r['exemples']}", bg="#f0f0f0", fg="#555", wraplength=800, justify="left").pack(anchor="w")
            tk.Button(carte, text="Supprimer", command=lambda rid=r["id"]: self._supprimer_regle(rid)).pack(anchor="e")

    def _supprimer_regle(self, regle_id):
        models.supprimer_regle(regle_id)
        self._rafraichir_regles()

    # ==================================================================
    # ONGLET 2 : Conjugueur automatique
    # ==================================================================
    def _build_onglet_conjugueur(self, parent):
        tk.Label(
            parent, text="Tape un verbe en anglais pour générer automatiquement ses formes conjuguées.",
            bg="white", font=("Segoe UI", 10), fg="#555"
        ).pack(anchor="w", padx=10, pady=(15, 10))

        recherche = tk.Frame(parent, bg="white")
        recherche.pack(anchor="w", padx=10)

        self.entree_verbe = tk.Entry(recherche, font=("Segoe UI", 14), width=20)
        self.entree_verbe.pack(side="left")
        self.entree_verbe.bind("<Return>", lambda e: self._generer_conjugaison())

        tk.Button(recherche, text="Générer", font=("Segoe UI", 11), command=self._generer_conjugaison).pack(
            side="left", padx=10
        )

        self.resultat_conjugueur = tk.Frame(parent, bg="white")
        self.resultat_conjugueur.pack(fill="x", padx=10, pady=20)

    def _generer_conjugaison(self):
        for widget in self.resultat_conjugueur.winfo_children():
            widget.destroy()

        verbe = self.entree_verbe.get().strip()
        resultat = conjuguer(verbe)

        if resultat is None:
            tk.Label(
                self.resultat_conjugueur, text="Merci de saisir un verbe valide (lettres uniquement).",
                bg="white", fg="#dc2626"
            ).pack(anchor="w")
            return

        badge = "🔴 Verbe irrégulier" if resultat["irregulier"] else "🟢 Verbe régulier"
        entete = f"{resultat['verbe'].capitalize()}  —  {badge}"
        if resultat["traduction"]:
            entete += f"  ({resultat['traduction']})"

        tk.Label(self.resultat_conjugueur, text=entete, font=("Segoe UI", 14, "bold"), bg="white").pack(
            anchor="w", pady=(0, 10)
        )

        lignes = [
            ("Présent (I/you/we/they)", resultat["verbe"]),
            ("Présent (he/she/it)", resultat["he_she_it"]),
            ("Participe présent (-ing)", resultat["ing"]),
            ("Passé simple", resultat["past_simple"]),
            ("Participe passé", resultat["past_participle"]),
        ]

        tableau = tk.Frame(self.resultat_conjugueur, bg="white")
        tableau.pack(anchor="w")
        for i, (label, forme) in enumerate(lignes):
            tk.Label(tableau, text=label, bg="white", font=("Segoe UI", 10), fg="#555", width=28, anchor="w").grid(
                row=i, column=0, sticky="w", pady=4
            )
            tk.Label(tableau, text=forme, bg="white", font=("Segoe UI", 12, "bold")).grid(
                row=i, column=1, sticky="w", padx=10
            )

        if resultat["irregulier"] and resultat["verbe"] != "be":
            tk.Label(
                self.resultat_conjugueur,
                text="Le passé simple et le participe passé sont identiques pour la plupart des verbes irréguliers,\n"
                     "mais vérifie toujours dans un dictionnaire en cas de doute.",
                bg="white", fg="#888", font=("Segoe UI", 9), justify="left"
            ).pack(anchor="w", pady=(15, 0))
        elif not resultat["irregulier"]:
            tk.Label(
                self.resultat_conjugueur,
                text="Formes générées automatiquement selon les règles standard. Certains cas particuliers\n"
                     "(verbes en plusieurs syllabes, accent tonique...) peuvent nécessiter une vérification.",
                bg="white", fg="#888", font=("Segoe UI", 9), justify="left"
            ).pack(anchor="w", pady=(15, 0))

    # ==================================================================
    # ONGLET 3 : Liste de référence des verbes irréguliers
    # ==================================================================
    def _build_onglet_irreguliers(self, parent):
        recherche = tk.Frame(parent, bg="white")
        recherche.pack(fill="x", padx=10, pady=(15, 10))

        tk.Label(recherche, text="Filtrer :", bg="white").pack(side="left")
        self.filtre_irreguliers = tk.Entry(recherche, width=20)
        self.filtre_irreguliers.pack(side="left", padx=5)
        self.filtre_irreguliers.bind("<KeyRelease>", lambda e: self._rafraichir_irreguliers())

        colonnes = ("base", "passe", "participe", "traduction")
        self.arbre_irreguliers = ttk.Treeview(parent, columns=colonnes, show="headings", height=18)
        entetes = {"base": "Base", "passe": "Passé simple", "participe": "Participe passé", "traduction": "Traduction"}
        largeurs = {"base": 120, "passe": 150, "participe": 150, "traduction": 200}
        for c in colonnes:
            self.arbre_irreguliers.heading(c, text=entetes[c])
            self.arbre_irreguliers.column(c, width=largeurs[c])
        self.arbre_irreguliers.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self._rafraichir_irreguliers()

    def _rafraichir_irreguliers(self):
        for item in self.arbre_irreguliers.get_children():
            self.arbre_irreguliers.delete(item)

        filtre = self.filtre_irreguliers.get().strip().lower()
        for base, passe, participe, traduction in VERBES_IRREGULIERS:
            if filtre and filtre not in base.lower() and filtre not in traduction.lower():
                continue
            self.arbre_irreguliers.insert("", "end", values=(base, passe, participe, traduction))
