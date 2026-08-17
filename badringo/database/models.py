"""
database/models.py
Fonctions CRUD pour le vocabulaire, la grammaire, les erreurs,
les conversations/messages et les sessions.
"""

import json
from datetime import datetime, timedelta
from database.db import get_connection


# ----------------------- VOCABULAIRE -----------------------

def ajouter_mot(mot, traduction, exemple="", theme="general"):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO mots (mot, traduction, exemple, theme) VALUES (?, ?, ?, ?)",
            (mot, traduction, exemple, theme)
        )
    conn.close()


def lister_mots(theme=None, a_reviser_seulement=False):
    conn = get_connection()
    query = "SELECT * FROM mots"
    conditions = []
    params = []
    if theme:
        conditions.append("theme = ?")
        params.append(theme)
    if a_reviser_seulement:
        conditions.append("prochaine_revision <= datetime('now')")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date_ajout DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def supprimer_mot(mot_id):
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM mots WHERE id = ?", (mot_id,))
    conn.close()


def reviser_mot(mot_id, reussi: bool):
    """
    Met à jour un mot après une révision, avec une répétition espacée
    simplifiée (inspirée de SM-2) : si réussi, l'intervalle augmente ;
    sinon, il revient à 1 jour.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM mots WHERE id = ?", (mot_id,)).fetchone()
    if not row:
        conn.close()
        return

    intervalle = row["intervalle_jours"]
    niveau = row["niveau_maitrise"]

    if reussi:
        intervalle = max(1, round(intervalle * 2.2))
        niveau = min(2, niveau + 1) if row["nb_revisions"] >= 2 else niveau
    else:
        intervalle = 1
        niveau = 0

    prochaine = (datetime.now() + timedelta(days=intervalle)).strftime("%Y-%m-%d %H:%M:%S")

    with conn:
        conn.execute(
            """UPDATE mots SET intervalle_jours = ?, niveau_maitrise = ?,
               prochaine_revision = ?, nb_revisions = nb_revisions + 1
               WHERE id = ?""",
            (intervalle, niveau, prochaine, mot_id)
        )
    conn.close()


# ----------------------- GRAMMAIRE / CONJUGAISON -----------------------

def ajouter_regle(categorie, titre, explication, commentaire="", exemples=""):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO regles_grammaire (categorie, titre, explication, commentaire, exemples) VALUES (?, ?, ?, ?, ?)",
            (categorie, titre, explication, commentaire, exemples)
        )
    conn.close()


def lister_regles(categorie=None):
    conn = get_connection()
    if categorie:
        rows = conn.execute(
            "SELECT * FROM regles_grammaire WHERE categorie = ? ORDER BY titre",
            (categorie,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM regles_grammaire ORDER BY categorie, titre").fetchall()
    conn.close()
    return rows


def supprimer_regle(regle_id):
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM regles_grammaire WHERE id = ?", (regle_id,))
    conn.close()


# ----------------------- JOURNAL D'ERREURS -----------------------

def ajouter_erreur(phrase_originale, phrase_corrigee, explication="", regle_id=None):
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO erreurs (phrase_originale, phrase_corrigee, explication, regle_id)
               VALUES (?, ?, ?, ?)""",
            (phrase_originale, phrase_corrigee, explication, regle_id)
        )
    conn.close()


def lister_erreurs():
    conn = get_connection()
    rows = conn.execute(
        """SELECT erreurs.*, regles_grammaire.titre AS regle_titre
           FROM erreurs LEFT JOIN regles_grammaire ON erreurs.regle_id = regles_grammaire.id
           ORDER BY erreurs.date_ajout DESC"""
    ).fetchall()
    conn.close()
    return rows


# ----------------------- CONVERSATIONS / CHAT -----------------------

def creer_conversation(sujet=""):
    conn = get_connection()
    with conn:
        cur = conn.execute("INSERT INTO conversations (sujet) VALUES (?)", (sujet,))
        conv_id = cur.lastrowid
    conn.close()
    return conv_id


def ajouter_message(conversation_id, expediteur, contenu, erreurs_detectees=None):
    conn = get_connection()
    erreurs_json = json.dumps(erreurs_detectees, ensure_ascii=False) if erreurs_detectees else None
    with conn:
        conn.execute(
            """INSERT INTO messages (conversation_id, expediteur, contenu, erreurs_detectees)
               VALUES (?, ?, ?, ?)""",
            (conversation_id, expediteur, contenu, erreurs_json)
        )
    conn.close()


def lister_messages(conversation_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY date_envoi ASC",
        (conversation_id,)
    ).fetchall()
    conn.close()
    return rows


def lister_conversations():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM conversations ORDER BY date_debut DESC").fetchall()
    conn.close()
    return rows


def conversation_existe(conversation_id):
    conn = get_connection()
    row = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    conn.close()
    return row is not None


# ----------------------- STATISTIQUES -----------------------

# ----------------------- HISTORIQUE DU QUIZ -----------------------

def enregistrer_session_quiz(score, total):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO sessions_quiz (score, total) VALUES (?, ?)", (score, total))
    conn.close()


def lister_sessions_quiz(limite=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions_quiz ORDER BY date_session DESC, id DESC LIMIT ?", (limite,)
    ).fetchall()
    conn.close()
    return rows


def statistiques():
    conn = get_connection()
    stats = {}
    stats["total_mots"] = conn.execute("SELECT COUNT(*) FROM mots").fetchone()[0]
    stats["mots_maitrises"] = conn.execute(
        "SELECT COUNT(*) FROM mots WHERE niveau_maitrise = 2"
    ).fetchone()[0]
    stats["mots_a_reviser"] = conn.execute(
        "SELECT COUNT(*) FROM mots WHERE prochaine_revision <= datetime('now')"
    ).fetchone()[0]
    stats["total_erreurs"] = conn.execute("SELECT COUNT(*) FROM erreurs").fetchone()[0]
    stats["total_regles"] = conn.execute("SELECT COUNT(*) FROM regles_grammaire").fetchone()[0]
    stats["total_conversations"] = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    conn.close()
    return stats
