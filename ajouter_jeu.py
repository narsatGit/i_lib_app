import streamlit as st
import os
from database import (
    get_all_jeux,
    get_jeu_by_id,
    add_jeu,
    update_jeu
)

# Chemins vers les dossiers de ressources
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images_jeux")
REGLE_DIR = os.path.join(BASE_DIR, "regle_jeux")

# Création des dossiers s'ils n'existent pas encore
os.makedirs(IMG_DIR,   exist_ok=True)
os.makedirs(REGLE_DIR, exist_ok=True)

# Liste fixe des sous-classifications fournie par la cliente
SOUS_CLASSIFICATIONS = [
    "—",
    "AMBIANCE",
    "ATTENTION/CONCENTRATION",
    "CHANCE/BLUFF",
    "COMPREHENSION/CONSIGNE/ECOUTE",
    "CONJUGAISONS",
    "CONSTRUCTION",
    "COOPERATION/ENTRAIDE",
    "COULEUR",
    "CREATION/IMAGINATION/MIME/TACTILE",
    "CULTURE GENERALE",
    "EDUCATIF",
    "EMOTIONS/ESTIME DE SOI/CONFIANCE EN SOI",
    "ENQUETE/ESCAPE",
    "EQUILIBRE",
    "EXPRESSION ORAL/COMMUNICATION",
    "GEOMETRIE/FORMES",
    "LOGIQUE/RAISONNEMENT/DEDUCTION",
    "MEMOIRE",
    "MOTRICITE FINE/COORDINATION ŒIL-MAIN/MANIPULATION",
    "NUMERATION/CALCUL/GRANDEUR/FRACTIONS",
    "ORTHOGRAPHE/GRAMMAIRE",
    "PHONEMES/GRAPHEMES/SYLLABES/LECTURE",
    "RAPIDITE",
    "REPERES TEMPORELS/ORIENTATION",
    "RESOLUTION DE PROBLEMES",
    "VOCABULAIRE",
]

# Fonctions de sauvegarde des fichiers

def sauvegarder_image(uploaded_file, titre):
    """
    Sauvegarde l'image uploadée dans le dossier images_jeux/.

    Entree : uploaded_file -> fichier uploadé via st.file_uploader()
             titre  -> titre du jeu pour nommer le fichier
    Sortie : nom du fichier sauvegardé, ou None si pas de fichier
    """
    if uploaded_file is None:
        return None

    # Construction du nom de fichier à partir du titre du jeu
    extension  = uploaded_file.name.split(".")[-1].lower()
    nom_fichier = f"{titre.lower().replace(' ', '_')}_img.{extension}"
    chemin = os.path.join(IMG_DIR, nom_fichier)

    # Écriture du fichier sur le disque
    with open(chemin, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # On retourne uniquement le nom du fichier (pas le chemin complet) car c'est le nom qu'on stocke dans la base de données
    return nom_fichier


def sauvegarder_pdf(uploaded_file, titre):
    """
    Sauvegarde le PDF uploadé dans le dossier regle_jeux/.

    Entree : uploaded_file -> fichier uploadé via st.file_uploader()
             titre -> titre du jeu pour nommer le fichier
    Sortie : nom du fichier sauvegardé, ou None si pas de fichier
    """
    if uploaded_file is None:
        return None

    # Même logique que sauvegarder_image()
    nom_fichier = f"{titre.lower().replace(' ', '_')}_regle.pdf"
    chemin = os.path.join(REGLE_DIR, nom_fichier)

    with open(chemin, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return nom_fichier


# Fonction principale

def show(mode="ajouter"):
    """
    Affiche le formulaire d'ajout ou de modification d'un jeu.
    Appelée par app.py avec mode="ajouter" ou mode="modifier".

    Entree : mode -> "ajouter" ou "modifier"
    Sortie : aucune — affiche le formulaire dans Streamlit
    """

    # Titre de la page selon le mode
    if mode == "ajouter":
        st.markdown("### ➕ Ajouter un jeu")
    else:
        st.markdown("### ✏️Modifier un jeu")

    st.divider()

    # Récupération du jeu à modifier (mode modifier uniquement)
    jeu_existant = None
    if mode == "modifier":
        jeu_id = st.session_state.get("jeu_a_modifier")
        if jeu_id:
            # Récupération du jeu depuis la base de données
            jeu_existant = get_jeu_by_id(jeu_id)
        if not jeu_existant:
            st.error("Jeu introuvable.")
            return

    # Construction de la liste des catégories depuis la base
    jeux_tous  = get_all_jeux()
    categories = sorted(set(
        j["categorie"] for j in jeux_tous
        if j["categorie"] is not None
    ))

    # Construction de la liste des classifications ESAR
    classifications = sorted(set(
        j["classification_esar"] for j in jeux_tous
        if j["classification_esar"] is not None
    ))


    # Formulaire
    # Sans st.form(), Streamlit rechargerait la page à chaque frappe
    with st.form("formulaire_jeu"):

        # Ligne 1 : Titre et Éditeur 
        col1, col2 = st.columns(2)

        with col1:
            # value= pre-remplit le champ en mode modifier
            titre = st.text_input(
                "Titre du jeu *",
                value=jeu_existant["titre"] if jeu_existant else ""
            )
        with col2:
            editeur = st.text_input(
                "Éditeur",
                value=jeu_existant["editeur"] or "" if jeu_existant else ""
            )

        # Ligne 2 : Age et Durée
        col3, col4 = st.columns(2)

        with col3:
            # step=1 signifie qu'on avance de 1 en 1
            age_minimum = st.number_input(
                "Âge minimum",
                min_value = 0,
                step=1,
                value=int(jeu_existant["age_minimum"]) if jeu_existant and jeu_existant["age_minimum"] else 0
            )
        with col4:
            # step=5 signifie qu'on avance de 5 en 5 (5, 10, 15...)
            duree_min = st.number_input(
                "Durée (minutes)",
                min_value=0,
                step=5,
                value=int(jeu_existant["duree_min"]) if jeu_existant and jeu_existant["duree_min"] else 0
            )

        # Ligne 3 : Nombre de joueurs et Catégorie
        col5, col6 = st.columns(2)

        with col5:
            nb_joueurs = st.text_input(
                "Nombre de joueurs",
                value=jeu_existant["nb_joueurs"] or "" if jeu_existant else "",
                placeholder="ex : 2-4, en équipe"
            )
        with col6:
            # index= positionne le selectbox sur la valeur actuelle
            idx_cat = categories.index(jeu_existant["categorie"]) if (
                jeu_existant and jeu_existant["categorie"] in categories
            ) else 0
            categorie = st.selectbox(
                "Catégorie",
                categories if categories else ["—"],
                index=idx_cat
            )

        # Ligne 4 : Classification ESAR et Sous-classification ─
        col7, = st.columns([1])

        with col7:
            idx_classif = classifications.index(jeu_existant["classification_esar"]) if (
                jeu_existant and jeu_existant["classification_esar"] in classifications
            ) else 0
            classification_esar = st.selectbox(
                "Classification ESAR",
                classifications if classifications else ["—"],
                index=idx_classif
            )
        # Les 3 sous-classifications sur une ligne séparée
        st.markdown("**Sous-classifications (3 maximum)**")
        col8, col9, col10 = st.columns(3)

        with col8:
            idx_s1 = SOUS_CLASSIFICATIONS.index(
                jeu_existant["sous_classification_1"]
            ) if (
                jeu_existant and
                jeu_existant["sous_classification_1"] in SOUS_CLASSIFICATIONS
            ) else 0
            sous_cl_1 = st.selectbox(
                "Sous-classification 1",
                SOUS_CLASSIFICATIONS,
                index=idx_s1
            )

        with col9:
            idx_s2 = SOUS_CLASSIFICATIONS.index(
                jeu_existant["sous_classification_2"]
            ) if (
                jeu_existant and
                jeu_existant["sous_classification_2"] in SOUS_CLASSIFICATIONS
            ) else 0
            sous_cl_2 = st.selectbox(
                "Sous-classification 2",
                SOUS_CLASSIFICATIONS,
                index=idx_s2
            )

        with col10:
            idx_s3 = SOUS_CLASSIFICATIONS.index(
                jeu_existant["sous_classification_3"]
            ) if (
                jeu_existant and
                jeu_existant["sous_classification_3"] in SOUS_CLASSIFICATIONS
            ) else 0
            sous_cl_3 = st.selectbox(
                "Sous-classification 3",
                SOUS_CLASSIFICATIONS,
                index=idx_s3
            )
        # Thème
        theme = st.text_input(
            "Thème",
            value=jeu_existant["theme"] or "" if jeu_existant else ""
        )

        # Upload des fichiers 
        col9, col10 = st.columns(2)

        with col9:
            fichier_image = st.file_uploader(
                "Image du jeu",
                type=["png", "jpg", "jpeg"]
            )
            # En mode modifier, on indique l'image actuelle
            if jeu_existant and jeu_existant["fichier_image"]:
                st.caption(f"Image actuelle : {jeu_existant['fichier_image']}")

        with col10:
            fichier_regle = st.file_uploader(
                "Règles du jeu (PDF)",
                type=["pdf"]
            )
            # En mode modifier, on indique le PDF actuel
            if jeu_existant and jeu_existant["fichier_regle"]:
                st.caption(f"Règles actuelles : {jeu_existant['fichier_regle']}")

        st.divider()

        # Boutons de soumission
        col_ajouter, col_annuler = st.columns(2)

        with col_ajouter:
            if mode == "ajouter":
                # form_submit_button déclenche le traitement ci-dessous
                soumettre = st.form_submit_button(
                    "Ajouter le jeu",
                    use_container_width=True,
                    type="primary"
                )
            else:
                soumettre = st.form_submit_button(
                    "Enregistrer les modifications",
                    use_container_width=True,
                    type="primary"
                )

        with col_annuler:
            annuler = st.form_submit_button(
                "Annuler",
                use_container_width=True
            )

    # Traitement après soumission du formulaire 
    # Ce code s'exécute uniquement quand un bouton est cliqué

    if annuler:
        # Réinitialisation de l'action et retour au catalogue
        st.session_state.action = None
        st.session_state.jeu_a_modifier = None
        st.rerun()

    if soumettre:

        # Validation : le titre est obligatoire
        if not titre.strip():
            st.error("Le titre du jeu est obligatoire.")
            return

        # Gestion des valeurs nulles pour age et durée
        # si la valeur vaut 0 on stocke None dans la base
        age = age_minimum if age_minimum > 0 else None
        duree = duree_min   if duree_min > 0   else None

        # Gestion des valeurs vides pour les champs texte
        nb_j  = nb_joueurs.strip()  or None
        cat = categorie or None
        classif = classification_esar or None
        sous_cl_1 = None if sous_cl_1 == "—" else sous_cl_1
        sous_cl_2 = None if sous_cl_2 == "—" else sous_cl_2
        sous_cl_3 = None if sous_cl_3 == "—" else sous_cl_3
        the = theme.strip() or None

        if mode == "ajouter":

            # Sauvegarde des fichiers uploadés dans les dossiers
            nom_image = sauvegarder_image(fichier_image, titre) if fichier_image else None
            nom_regle = sauvegarder_pdf(fichier_regle,  titre) if fichier_regle else None

            # Insertion dans la base de données via database.py
            # add_jeu() retourne l'id du nouveau jeu créé
            nouvel_id = add_jeu(
                titre                 = titre.strip(),
                editeur               = editeur.strip() or None,
                age_minimum           = age,
                duree_min             = duree,
                nb_joueurs            = nb_j,
                categorie             = cat,
                classification_esar   = classif,
                sous_classification_1 = sous_cl_1,
                sous_classification_2 = sous_cl_2,
                sous_classification_3 = sous_cl_3,
                theme                 = the,
                fichier_image         = nom_image,
                fichier_regle         = nom_regle
            )

            st.success(f"Jeu '{titre}' ajouté avec succès (id : {nouvel_id}) !")

            # Retour automatique au catalogue après l'ajout
            st.session_state.action             = None
            st.session_state.jeu_selectionne_id = nouvel_id
            st.rerun()

        else:
            # Mode modifier : on met à jour le jeu existant
            if fichier_image:
                nom_image = sauvegarder_image(fichier_image, titre)
            else:
                # conservation du fichier image existant
                nom_image = jeu_existant["fichier_image"]

            if fichier_regle:
                nom_regle = sauvegarder_pdf(fichier_regle, titre)
            else:
                # conservation du fichier PDF existant
                nom_regle = jeu_existant["fichier_regle"]

            # Mise à jour dans la base de données via database.py
            update_jeu(
                jeu_id = jeu_existant["id"],
                titre = titre.strip(),
                editeur = editeur.strip() or None,
                age_minimum = age,
                duree_min = duree,
                nb_joueurs = nb_j,
                categorie = cat,
                classification_esar = classif,
                sous_classification_1 = sous_cl_1,
                sous_classification_2 = sous_cl_2,
                sous_classification_3 = sous_cl_3,
                theme = the,
                fichier_image = nom_image,
                fichier_regle = nom_regle
            )

            st.success(f"Jeu '{titre}' modifié avec succès !")

            # Retour au catalogue après la modification
            st.session_state.action = None
            st.session_state.jeu_a_modifier = None
            st.session_state.jeu_selectionne_id = jeu_existant["id"]
            st.rerun()