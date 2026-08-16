"""
database/db.py
Connexion et initialisation de la base de données SQLite.
"""

import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS mots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mot TEXT NOT NULL,
    traduction TEXT NOT NULL,
    exemple TEXT,
    theme TEXT DEFAULT 'general',
    niveau_maitrise INTEGER DEFAULT 0,      -- 0=nouveau,1=en cours,2=maitrise
    date_ajout TEXT DEFAULT (datetime('now')),
    prochaine_revision TEXT DEFAULT (datetime('now')),
    intervalle_jours INTEGER DEFAULT 1,
    nb_revisions INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS regles_grammaire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie TEXT NOT NULL,                -- 'conjugaison' ou 'grammaire'
    titre TEXT NOT NULL,
    explication TEXT NOT NULL,
    commentaire TEXT,
    exemples TEXT,
    niveau_maitrise INTEGER DEFAULT 0,
    date_ajout TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS erreurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_originale TEXT NOT NULL,
    phrase_corrigee TEXT NOT NULL,
    explication TEXT,
    regle_id INTEGER,
    date_ajout TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (regle_id) REFERENCES regles_grammaire(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sujet TEXT,
    date_debut TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    expediteur TEXT NOT NULL,               -- 'utilisateur' ou 'ia'
    contenu TEXT NOT NULL,
    erreurs_detectees TEXT,                 -- JSON stocké en texte
    date_envoi TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_session TEXT DEFAULT (datetime('now')),
    duree_minutes INTEGER DEFAULT 0,
    sujet TEXT,
    notes TEXT
);
"""


def init_db():
    conn = get_connection()
    with conn:
        conn.executescript(SCHEMA)
    # Migration légère : ajoute la colonne 'commentaire' si la base existait
    # déjà avant son introduction (ne fait rien si elle est déjà présente).
    try:
        with conn:
            conn.execute("ALTER TABLE regles_grammaire ADD COLUMN commentaire TEXT")
    except Exception:
        pass  # colonne déjà existante
    conn.close()
