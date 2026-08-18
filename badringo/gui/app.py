"""
gui/app.py
Fenêtre principale : barre latérale de navigation + zone de contenu.
"""

import shutil
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config import APP_NAME, APP_VERSION, DB_PATH, load_settings, save_settings
from gui.vocab_view import VocabView
from gui.grammar_view import GrammarView
from gui.errors_view import ErrorsView
from gui.chat_view import ChatView
from gui.stats_view import StatsView
from gui.profile_view import ProfileView
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
            ("🎓 Mon profil", "profil"),
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

        btn_restaurer = tk.Button(
            self.sidebar, text="📂 Restaurer une sauvegarde", anchor="w", relief="flat",
            bg=couleurs["sidebar"], fg=couleurs["text"], font=("Segoe UI", 9),
            padx=20, pady=8, command=self.restaurer_sauvegarde
        )
        btn_restaurer.pack(side="bottom", fill="x")

        btn_sauvegarder = tk.Button(
            self.sidebar, text="💾 Sauvegarder mes données", anchor="w", relief="flat",
            bg=couleurs["sidebar"], fg=couleurs["text"], font=("Segoe UI", 9),
            padx=20, pady=8, command=self.sauvegarder_donnees
        )
        btn_sauvegarder.pack(side="bottom", fill="x")

    def sauvegarder_donnees(self):
        nom_par_defaut = f"badringo_sauvegarde_{datetime.now().strftime('%Y-%m-%d')}.db"
        destination = filedialog.asksaveasfilename(
            title="Enregistrer la sauvegarde",
            defaultextension=".db",
            initialfile=nom_par_defaut,
            filetypes=[("Base de données Badringo", "*.db")]
        )
        if not destination:
            return
        try:
            shutil.copy2(DB_PATH, destination)
            messagebox.showinfo("Sauvegarde", "Tes données ont été sauvegardées avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la sauvegarde : {e}")

    def restaurer_sauvegarde(self):
        reponse = messagebox.askyesno(
            "Restaurer une sauvegarde",
            "Cela va REMPLACER toutes tes données actuelles (vocabulaire, grammaire, "
            "erreurs, conversations) par celles du fichier de sauvegarde.\n\n"
            "Cette action est irréversible. Continuer ?"
        )
        if not reponse:
            return

        source = filedialog.askopenfilename(
            title="Choisir un fichier de sauvegarde",
            filetypes=[("Base de données Badringo", "*.db")]
        )
        if not source:
            return

        try:
            shutil.copy2(source, DB_PATH)
            messagebox.showinfo(
                "Restauration réussie",
                "Tes données ont été restaurées. Ferme et rouvre l'application pour "
                "voir les changements."
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la restauration : {e}")

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

        self._lancer_telechargement_avec_progression(resultat["exe_url"])

    def _lancer_telechargement_avec_progression(self, exe_url):
        fenetre = tk.Toplevel(self)
        fenetre.title("Téléchargement en cours")
        fenetre.geometry("400x120")
        fenetre.resizable(False, False)
        fenetre.transient(self)
        fenetre.grab_set()  # bloque uniquement cette petite fenêtre, pas l'appli entière

        tk.Label(fenetre, text="Téléchargement de la mise à jour...", font=("Segoe UI", 11)).pack(pady=(20, 10))

        barre = ttk.Progressbar(fenetre, orient="horizontal", length=340, mode="determinate")
        barre.pack(pady=5)

        pourcentage_label = tk.Label(fenetre, text="0 %", font=("Segoe UI", 9), fg="#666")
        pourcentage_label.pack()

        def mettre_a_jour_barre(pourcentage):
            barre["value"] = pourcentage
            pourcentage_label.config(text=f"{pourcentage} %")

        def telecharger_en_arriere_plan():
            try:
                chemin = updater.download_update(
                    exe_url,
                    progress_callback=lambda p: self.after(0, mettre_a_jour_barre, p)
                )
                self.after(0, telechargement_termine, chemin)
            except Exception as e:
                self.after(0, telechargement_echoue, e)

        def telechargement_termine(chemin):
            fenetre.destroy()
            messagebox.showinfo(
                "Mise à jour",
                "Téléchargement terminé. L'application va redémarrer pour terminer l'installation."
            )
            updater.apply_update(chemin)

        def telechargement_echoue(erreur):
            fenetre.destroy()
            messagebox.showerror("Erreur", f"Échec de la mise à jour : {erreur}")

        threading.Thread(target=telecharger_en_arriere_plan, daemon=True).start()

    def afficher_vue(self, cle):
        for widget in self.content.winfo_children():
            widget.destroy()

        classes = {
            "profil": ProfileView,
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
