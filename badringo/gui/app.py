"""
gui/app.py
Fenêtre principale : barre latérale de navigation + zone de contenu.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_NAME, APP_VERSION, load_settings, save_settings
from gui.vocab_view import VocabView
from gui.grammar_view import GrammarView
from gui.errors_view import ErrorsView
from gui.chat_view import ChatView
from gui.stats_view import StatsView
from gui.quiz_view import QuizView
import updater

COULEURS = {
    "light": {"bg": "#f5f5f7", "sidebar": "#ffffff", "accent": "#2563eb", "text": "#111111"},
    "dark":  {"bg": "#1e1e1e", "sidebar": "#252526", "accent": "#3b82f6", "text": "#f5f5f5"},
}


class BadringoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.theme = self.settings.get("theme", "light")

        self.title(f"{APP_NAME} — v{APP_VERSION}")
        self.geometry(f'{self.settings.get("window_width", 1100)}x{self.settings.get("window_height", 700)}')
        self.minsize(900, 600)

        self._build_layout()
        self.afficher_vue("stats")

    def _build_layout(self):
        couleurs = COULEURS[self.theme]

        self.sidebar = tk.Frame(self, bg=couleurs["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=couleurs["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        titre = tk.Label(
            self.sidebar, text=APP_NAME, bg=couleurs["sidebar"],
            fg=couleurs["accent"], font=("Segoe UI", 14, "bold"), pady=20
        )
        titre.pack(fill="x")

        boutons = [
            ("📊 Tableau de bord", "stats"),
            ("📚 Vocabulaire", "vocab"),
            ("📖 Grammaire & Conjugaison", "grammar"),
            ("📝 Journal d'erreurs", "errors"),
            ("🎯 Quiz", "quiz"),
            ("💬 Chat / Pratique", "chat"),
        ]
        for label, cle in boutons:
            btn = tk.Button(
                self.sidebar, text=label, anchor="w", relief="flat",
                bg=couleurs["sidebar"], fg=couleurs["text"], font=("Segoe UI", 11),
                padx=20, pady=10, activebackground=couleurs["accent"],
                command=lambda c=cle: self.afficher_vue(c)
            )
            btn.pack(fill="x")

        self.vues = {}

        # Bouton de mise à jour, en bas de la barre latérale
        version_label = tk.Label(
            self.sidebar, text=f"Version {APP_VERSION}", bg=couleurs["sidebar"],
            fg="#888", font=("Segoe UI", 9)
        )
        version_label.pack(side="bottom", pady=(0, 5))

        btn_maj = tk.Button(
            self.sidebar, text="🔄 Vérifier les mises à jour", anchor="w", relief="flat",
            bg=couleurs["sidebar"], fg=couleurs["text"], font=("Segoe UI", 9),
            padx=20, pady=8, command=self.verifier_mises_a_jour
        )
        btn_maj.pack(side="bottom", fill="x")

    def verifier_mises_a_jour(self):
        resultat = updater.check_for_updates()
        if resultat is None:
            messagebox.showinfo(
                "Mises à jour",
                "Impossible de vérifier les mises à jour (pas de connexion internet ?)."
            )
            return

        if not resultat["disponible"]:
            messagebox.showinfo("Mises à jour", "Vous avez déjà la dernière version.")
            return

        reponse = messagebox.askyesno(
            "Mise à jour disponible",
            f"Une nouvelle version ({resultat['version']}) est disponible.\n\n"
            f"{resultat['notes']}\n\nTélécharger et installer maintenant ?"
        )
        if not reponse:
            return

        try:
            chemin = updater.download_update(resultat["exe_url"])
            messagebox.showinfo(
                "Mise à jour",
                "Téléchargement terminé. L'application va redémarrer pour terminer l'installation."
            )
            updater.apply_update(chemin)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la mise à jour : {e}")

    def afficher_vue(self, cle):
        for widget in self.content.winfo_children():
            widget.destroy()

        classes = {
            "stats": StatsView,
            "vocab": VocabView,
            "grammar": GrammarView,
            "errors": ErrorsView,
            "quiz": QuizView,
            "chat": ChatView,
        }
        vue_class = classes[cle]
        vue = vue_class(self.content, theme=self.theme)
        vue.pack(fill="both", expand=True)

    def on_close(self):
        self.settings["window_width"] = self.winfo_width()
        self.settings["window_height"] = self.winfo_height()
        save_settings(self.settings)
        self.destroy()


def lancer_application():
    app = BadringoApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
