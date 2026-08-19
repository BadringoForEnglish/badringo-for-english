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


def analyser_patterns_erreurs(limite=5):
    """
    Regroupe les erreurs enregistrées par notion (la règle de grammaire liée
    si elle existe, sinon l'explication donnée par l'IA), pour faire
    ressortir les erreurs les plus récurrentes. Calculé à la volée à partir
    de la table 'erreurs' existante : aucune donnée dupliquée, toujours à
    jour automatiquement.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT
               COALESCE(rg.titre, erreurs.explication) AS notion,
               COUNT(*) AS frequence,
               MAX(erreurs.date_ajout) AS derniere_occurrence
           FROM erreurs
           LEFT JOIN regles_grammaire rg ON erreurs.regle_id = rg.id
           WHERE COALESCE(rg.titre, erreurs.explication) IS NOT NULL
             AND COALESCE(rg.titre, erreurs.explication) != ''
           GROUP BY LOWER(COALESCE(rg.titre, erreurs.explication))
           ORDER BY frequence DESC, derniere_occurrence DESC
           LIMIT ?""",
        (limite,)
    ).fetchall()
    conn.close()
    return rows


# ----------------------- MAÎTRISE PAR NOTION -----------------------

def mettre_a_jour_maitrise(notion, correct):
    """Enregistre le résultat d'une réponse de quiz pour une notion donnée
    (thème de vocabulaire ou 'Conjugaison'). Crée la notion si elle
    n'existe pas encore."""
    if not notion:
        return
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO topic_mastery (notion, nb_reponses, nb_correctes)
               VALUES (?, 1, ?)
               ON CONFLICT(notion) DO UPDATE SET
                   nb_reponses = nb_reponses + 1,
                   nb_correctes = nb_correctes + excluded.nb_correctes,
                   derniere_mise_a_jour = datetime('now')""",
            (notion, 1 if correct else 0)
        )
    conn.close()


def lister_maitrise_notions(limite=10, minimum_reponses=3):
    """Renvoie les notions les moins maîtrisées en premier (score le plus
    bas), en ignorant celles avec trop peu de réponses pour être fiables."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT notion, nb_reponses, nb_correctes,
                  ROUND(100.0 * nb_correctes / nb_reponses, 0) AS score,
                  derniere_mise_a_jour
           FROM topic_mastery
           WHERE nb_reponses >= ?
           ORDER BY score ASC, nb_reponses DESC
           LIMIT ?""",
        (minimum_reponses, limite)
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


# ----------------------- PROFIL APPRENANT -----------------------

def obtenir_profil():
    """Renvoie la ligne unique du profil (toujours id=1, créée au démarrage)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM learner_profile WHERE id = 1").fetchone()
    conn.close()
    return row


def enregistrer_profil(prenom, langue_maternelle, objectif_general):
    """Met à jour les champs saisissables du profil (le niveau estimé n'est
    JAMAIS modifié ici : voir mettre_a_jour_niveau_estime, utilisée
    uniquement par le Skill Assessment automatique)."""
    conn = get_connection()
    with conn:
        conn.execute(
            """UPDATE learner_profile
               SET prenom = ?, langue_maternelle = ?, objectif_general = ?
               WHERE id = 1""",
            (prenom, langue_maternelle, objectif_general)
        )
    conn.close()


def mettre_a_jour_niveau_estime(niveau):
    """Écrit le niveau calculé automatiquement par le Skill Assessment
    (Phase 7). Jamais appelée depuis un formulaire saisi à la main."""
    conn = get_connection()
    with conn:
        conn.execute("UPDATE learner_profile SET niveau_estime = ? WHERE id = 1", (niveau,))
    conn.close()


# ----------------------- DASHBOARD QUOTIDIEN -----------------------

def jours_actifs():
    """Renvoie l'ensemble des dates (AAAA-MM-JJ) où une activité a eu lieu
    dans l'app (quiz, chat, vocabulaire ajouté, erreur enregistrée) —
    utilisé pour calculer le streak, sans nouvelle table de log."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(date_session) AS jour FROM sessions_quiz
           UNION
           SELECT date(date_envoi) FROM messages
           UNION
           SELECT date(date_ajout) FROM mots
           UNION
           SELECT date(date_ajout) FROM erreurs"""
    ).fetchall()
    conn.close()
    return {r["jour"] for r in rows if r["jour"]}


def sessions_quiz_recentes(jours=14):
    """Renvoie les sessions de quiz des N derniers jours (score, total,
    date), pour calculer une tendance de progression."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT score, total, date_session FROM sessions_quiz
           WHERE date_session >= date('now', ?)
           ORDER BY date_session ASC""",
        (f"-{jours} days",)
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
