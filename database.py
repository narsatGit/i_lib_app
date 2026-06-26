import sqlite3
import os
import unicodedata
import pandas as pd
import spacy

nlp = spacy.load("fr_core_news_sm")
MOTS_VIDES = nlp.Defaults.stop_words

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "data", "i_lib.db")
EXCEL_PATH = os.path.join(BASE_DIR, "tableurs", "inventaire_jeux.xlsx")


def get_connection():
    """
    Connexion SQLite avec row_factory et clés étrangères actives.
    Entrée : aucune
    Sortie : sqlite3.Connection
    """
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion


def init_db():
    """
    Crée les deux tables si elles n'existent pas.
    Entrée : aucune
    Sortie : aucune
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_connection() as connexion:
        curseur = connexion.cursor()

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS jeux (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                titre                 TEXT NOT NULL,
                editeur               TEXT,
                age_minimum           INTEGER,
                duree_min             INTEGER,
                nb_joueurs            TEXT,
                categorie             TEXT,
                classification_esar   TEXT,
                sous_classification_1 TEXT,
                sous_classification_2 TEXT,
                sous_classification_3 TEXT,
                theme                 TEXT,
                fichier_regle         TEXT,
                fichier_image         TEXT,
                date_ajout            TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS fiches_pedagogiques (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                jeu_id            INTEGER NOT NULL,
                competences       TEXT,
                objectifs         TEXT,
                resume_regles     TEXT,
                date_modification TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jeu_id) REFERENCES jeux(id) ON DELETE CASCADE
            )
        """)

        connexion.commit()


def normaliser_texte(texte):
    """
    Prétraitement TAL : minuscules, suppression accents et ponctuation.
    Entrée : str
    Sortie : str
    """
    if not texte:
        return ""

    texte = texte.lower()

    # NFD décompose les caractères accentués, "Mn" = marque diacritique
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")

    doc = nlp(texte)
    return " ".join(
        token.text for token in doc
        if not token.is_punct and not token.is_space
    ).strip()


def tokeniser(texte):
    """
    Pipeline spaCy : tokenisation + filtrage mots vides + lemmatisation.
    Entrée : str
    Sortie : list[str] -- lemmes significatifs
    """
    if not texte:
        return []

    doc = nlp(texte.lower())
    lemmes = []

    for token in doc:
        if token.is_punct or token.is_space or token.is_stop:
            continue
        if len(token.lemma_) < 3:
            continue
        lemmes.append(token.lemma_)

    return lemmes


def extraire_mots_cles(texte, n=5):
    """
    Fréquence des lemmes, tri décroissant, retourne les n premiers.
    Entrée : str, int
    Sortie : list[str]
    """
    if not texte:
        return []

    doc = nlp(texte.lower())
    frequences = {}

    for token in doc:
        if token.is_punct or token.is_space or token.is_stop:
            continue
        if len(token.lemma_) < 3:
            continue
        lemme = token.lemma_
        if lemme not in frequences:
            frequences[lemme] = 0
        else:
            frequences[lemme] += 1

    mots_tries = sorted(frequences.items(), key=lambda x: x[1], reverse=True)
    return [mot for mot, _ in mots_tries[:n]]


def migrate_excel():
    """
    Peuple la table jeux depuis le fichier Excel.
    Garde-fou : s'arrête si la table n'est pas vide.
    dtype=str évite qu'Excel interprète "2-4" comme une date.
    Entrée : aucune
    Sortie : aucune
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("SELECT COUNT(*) FROM jeux")
        if curseur.fetchone()[0] > 0:
            return

    if not os.path.exists(EXCEL_PATH):
        print(f"Fichier Excel introuvable : {EXCEL_PATH}")
        return

    df = pd.read_excel(EXCEL_PATH, sheet_name="Inventaire des jeux", dtype=str)
    df.columns = [col.strip() for col in df.columns]

    with get_connection() as connexion:
        curseur = connexion.cursor()

        for _, ligne in df.iterrows():

            def nettoyer(valeur):
                # NaN pandas -> None -> NULL SQLite
                if pd.isna(valeur):
                    return None
                valeur = str(valeur).strip()
                return None if valeur == "" else valeur

            titre = nettoyer(ligne.get("titre_jeu"))
            if not titre:
                continue

            # pandas lit les entiers Excel en float : int(float("15.0")) = 15
            age_brut = ligne.get("age_minimum")
            age = int(float(age_brut)) if pd.notna(age_brut) else None

            duree_brute = ligne.get("duree_min")
            duree = int(float(duree_brute)) if pd.notna(duree_brute) else None

            curseur.execute("""
                INSERT INTO jeux (
                    titre, editeur, age_minimum, duree_min,
                    nb_joueurs, categorie, classification_esar,
                    sous_classification_1, sous_classification_2,
                    sous_classification_3, theme,
                    fichier_regle, fichier_image
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                titre,
                nettoyer(ligne.get("editeur")),
                age,
                duree,
                nettoyer(ligne.get("nb_joueurs")),
                nettoyer(ligne.get("categorie_jeu")),
                nettoyer(ligne.get("classification_ESAR")),
                nettoyer(ligne.get("sous_classification_ESAR")),
                None,
                None,
                nettoyer(ligne.get("theme")),
                nettoyer(ligne.get("regles")),
                nettoyer(ligne.get("images"))
            ))

        connexion.commit()
        print("Migration terminée.")


# --- CRUD jeux ---

def get_all_jeux():
    """Retourne tous les jeux triés par titre."""
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("SELECT * FROM jeux ORDER BY titre")
        return curseur.fetchall()


def get_jeu_by_id(jeu_id):
    """Retourne un jeu par son id, ou None."""
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("SELECT * FROM jeux WHERE id = ?", (jeu_id,))
        return curseur.fetchone()


def search_jeux(terme, categorie=None, age_max=None, duree_max=None):
    """
    Recherche multi-critères avec tokenisation spaCy.
    Construit dynamiquement la clause WHERE.
    Entrée : str, str|None, int|None, int|None
    Sortie : list[sqlite3.Row]
    """
    tokens = tokeniser(terme) if terme else []
    conditions = []
    parametres = []

    for token in tokens:
        t = f"%{token}%"
        conditions.append("""
            (LOWER(titre)                 LIKE ?
          OR LOWER(theme)                 LIKE ?
          OR LOWER(categorie)             LIKE ?
          OR LOWER(sous_classification_1) LIKE ?
          OR LOWER(editeur)               LIKE ?)
        """)
        parametres += [t, t, t, t, t]

    if categorie:
        conditions.append("categorie = ?")
        parametres.append(categorie)

    if age_max:
        conditions.append("age_minimum <= ?")
        parametres.append(age_max)

    if duree_max:
        conditions.append("(duree_min <= ? OR duree_min IS NULL)")
        parametres.append(duree_max)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute(
            f"SELECT * FROM jeux {where} ORDER BY titre",
            parametres
        )
        return curseur.fetchall()


def add_jeu(titre, editeur=None, age_minimum=None, duree_min=None,
            nb_joueurs=None, categorie=None, classification_esar=None,
            sous_classification_1=None, sous_classification_2=None,
            sous_classification_3=None, theme=None,
            fichier_regle=None, fichier_image=None):
    """
    Insère un jeu. Retourne l'id créé.
    Entrée : titre (str, obligatoire), reste optionnel
    Sortie : int
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("""
            INSERT INTO jeux (
                titre, editeur, age_minimum, duree_min,
                nb_joueurs, categorie, classification_esar,
                sous_classification_1, sous_classification_2,
                sous_classification_3, theme,
                fichier_regle, fichier_image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titre, editeur, age_minimum, duree_min,
            nb_joueurs, categorie, classification_esar,
            sous_classification_1, sous_classification_2,
            sous_classification_3, theme,
            fichier_regle, fichier_image
        ))
        connexion.commit()
        return curseur.lastrowid


def update_jeu(jeu_id, titre, editeur=None, age_minimum=None,
               duree_min=None, nb_joueurs=None, categorie=None,
               classification_esar=None,
               sous_classification_1=None, sous_classification_2=None,
               sous_classification_3=None, theme=None,
               fichier_regle=None, fichier_image=None):
    """
    Met à jour toutes les colonnes d'un jeu.
    Entrée : jeu_id (int), mêmes params que add_jeu
    Sortie : aucune
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("""
            UPDATE jeux SET
                titre                 = ?,
                editeur               = ?,
                age_minimum           = ?,
                duree_min             = ?,
                nb_joueurs            = ?,
                categorie             = ?,
                classification_esar   = ?,
                sous_classification_1 = ?,
                sous_classification_2 = ?,
                sous_classification_3 = ?,
                theme                 = ?,
                fichier_regle         = ?,
                fichier_image         = ?
            WHERE id = ?
        """, (
            titre, editeur, age_minimum, duree_min,
            nb_joueurs, categorie, classification_esar,
            sous_classification_1, sous_classification_2,
            sous_classification_3, theme,
            fichier_regle, fichier_image,
            jeu_id
        ))
        connexion.commit()


def delete_jeu(jeu_id):
    """
    Supprime un jeu. CASCADE sur fiches_pedagogiques.
    Entrée : int
    Sortie : aucune
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("DELETE FROM jeux WHERE id = ?", (jeu_id,))
        connexion.commit()


# --- CRUD fiches_pedagogiques ---

def get_fiche_by_jeu(jeu_id):
    """Retourne la fiche d'un jeu, ou None."""
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute(
            "SELECT * FROM fiches_pedagogiques WHERE jeu_id = ?",
            (jeu_id,)
        )
        return curseur.fetchone()


def add_fiche(jeu_id, competences=None, objectifs=None, resume_regles=None):
    """
    Crée une fiche pédagogique. Retourne l'id créé.
    Le contenu est stocké en HTML (streamlit-quill).
    Entrée : int, str|None, str|None, str|None
    Sortie : int
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("""
            INSERT INTO fiches_pedagogiques
                (jeu_id, competences, objectifs, resume_regles)
            VALUES (?, ?, ?, ?)
        """, (jeu_id, competences, objectifs, resume_regles))
        connexion.commit()
        return curseur.lastrowid


def update_fiche(fiche_id, competences=None, objectifs=None, resume_regles=None):
    """
    Met à jour une fiche et horodate date_modification.
    Entrée : int, str|None, str|None, str|None
    Sortie : aucune
    """
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute("""
            UPDATE fiches_pedagogiques SET
                competences       = ?,
                objectifs         = ?,
                resume_regles     = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (competences, objectifs, resume_regles, fiche_id))
        connexion.commit()


def delete_fiche(fiche_id):
    """Supprime une fiche par son id."""
    with get_connection() as connexion:
        curseur = connexion.cursor()
        curseur.execute(
            "DELETE FROM fiches_pedagogiques WHERE id = ?",
            (fiche_id,)
        )
        connexion.commit()


# --- Tests unitaires ---

if __name__ == "__main__":
    print("=== Init DB ===")
    init_db()
    print("Tables créées.")

    print("\n=== Migration Excel ===")
    migrate_excel()

    print("\n=== Lecture ===")
    jeux = get_all_jeux()
    print(f"{len(jeux)} jeux en base.")
    if jeux:
        print(f"Premier : {jeux[0]['titre']}")