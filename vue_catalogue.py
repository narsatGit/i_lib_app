import streamlit as st
import os
import base64
from PIL import Image

from database import (
    get_all_jeux,
    get_jeu_by_id,
    search_jeux,
    delete_jeu,
    get_fiche_by_jeu,
)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "images_jeux")
REGLE_DIR = os.path.join(BASE_DIR, "regle_jeux")


def pluriel(nbr):
    """Accord singulier/pluriel pour le compteur de résultats."""
    if isinstance(nbr, int) and nbr > 1:
        return f"{nbr} jeux trouvés"
    return f"{nbr} jeu trouvé"


def show():
    """Écran catalogue : recherche, filtres, liste, détail."""

    st.markdown("### 🗃️ Catalogue des jeux")
    st.divider()

    col_recherche, col_cat, col_age = st.columns([3, 2, 2])

    with col_recherche:
        terme = st.text_input(
            "Rechercher",
            placeholder="Nom, thème, catégorie...",
            label_visibility="collapsed"
        )

    with col_cat:
        jeux_tous = get_all_jeux()
        categories = sorted(set(
            j["categorie"] for j in jeux_tous
            if j["categorie"] is not None
        ))
        cat_choisie = st.selectbox(
            "Catégorie",
            ["Toutes"] + categories,
            label_visibility="collapsed"
        )

    with col_age:
        # 0 = pas de filtre, l'âge n'a pas de plafond
        age_max = st.number_input(
            "Âge maximum",
            min_value=0,
            value=0,
            label_visibility="collapsed"
        )

    st.divider()

    categorie_filtre = None if cat_choisie == "Toutes" else cat_choisie
    age_filtre = None if age_max == 0 else age_max

    jeux = search_jeux(
        terme=terme,
        categorie=categorie_filtre,
        age_max=age_filtre
    )

    st.caption(pluriel(len(jeux)))

    if not jeux:
        st.info("Aucun jeu ne correspond à votre recherche.")
        return

    col_liste, col_detail = st.columns([1, 2])

    if "jeu_selectionne_id" not in st.session_state:
        st.session_state.jeu_selectionne_id = jeux[0]["id"]

    with col_liste:
        st.markdown("**Liste des jeux**")

        # hauteur fixe + scroll pour éviter que la page s'allonge
        with st.container(height=700):
            for jeu in jeux:
                if st.button(
                    jeu["titre"],
                    key=f"btn_{jeu['id']}",
                    use_container_width=True
                ):
                    st.session_state.jeu_selectionne_id = jeu["id"]
                    st.rerun()

        if st.button(
            "Ajouter un jeu",
            key="btn_ajouter_jeu",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.action = "ajouter_jeu"
            st.session_state.form_key = 0
            st.rerun()

    with col_detail:
        afficher_detail(st.session_state.jeu_selectionne_id)


def afficher_detail(jeu_id):
    """
    Détail complet d'un jeu : infos, image, PDF, fiche, actions.
    Entrée : jeu_id (int)
    """
    jeu = get_jeu_by_id(jeu_id)

    if not jeu:
        st.warning("Ce jeu n'existe plus.")
        return

    st.markdown(f"### {jeu['titre']}")

    if jeu["editeur"]:
        st.caption(f"Éditeur : {jeu['editeur']}")

    if jeu["fichier_image"]:
        chemin_image = os.path.join(IMG_DIR, jeu["fichier_image"])
        if os.path.exists(chemin_image):
            image = Image.open(chemin_image)
            image.thumbnail((200, 200))  # conserve les proportions
            st.image(image)
        else:
            st.caption("Image non disponible.")

    st.markdown("**Informations**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Âge minimum",
            f"{jeu['age_minimum']} ans" if jeu["age_minimum"] else "—"
        )
    with col2:
        st.metric(
            "Durée",
            f"{jeu['duree_min']} min" if jeu["duree_min"] else "—"
        )
    with col3:
        st.metric(
            "Nombre de joueurs",
            jeu["nb_joueurs"] if jeu["nb_joueurs"] else "—"
        )

    if jeu["categorie"]:
        st.markdown(f"**Catégorie** : {jeu['categorie']}")
    if jeu["classification_esar"]:
        st.markdown(f"**Classification ESAR** : {jeu['classification_esar']}")
    if jeu["sous_classification_1"]:
        st.markdown(f"**Sous-classification 1** : {jeu['sous_classification_1']}")
    if jeu["sous_classification_2"]:
        st.markdown(f"**Sous-classification 2** : {jeu['sous_classification_2']}")
    if jeu["sous_classification_3"]:
        st.markdown(f"**Sous-classification 3** : {jeu['sous_classification_3']}")
    if jeu["theme"]:
        st.markdown(f"**Thème** : {jeu['theme']}")

    st.divider()

    if jeu["fichier_regle"]:
        chemin_regle = os.path.join(REGLE_DIR, jeu["fichier_regle"])
        if os.path.exists(chemin_regle):
            # base64 permet d'intégrer le PDF dans un lien sans le télécharger
            with open(chemin_regle, "rb") as f:
                pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

            lien_pdf = f"data:application/pdf;base64,{pdf_base64}"
            st.markdown(
                f'''
                <a href="{lien_pdf}" target="_blank"
                style="
                    display: inline-block;
                    background-color: #055EE3;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 14px;
                ">
                Ouvrir les règles (PDF)
                </a>
                ''',
                unsafe_allow_html=True
            )

    st.markdown("**Fiche pédagogique**")
    fiche = get_fiche_by_jeu(jeu_id)

    if fiche:
        if st.button("Modifier la fiche pédagogique", key=f"modif_fiche_{jeu_id}"):
            st.session_state.jeu_selectionne_id = jeu_id
            st.session_state.action = "modifier_fiche"
            st.rerun()
    else:
        st.info("Aucune fiche pédagogique pour ce jeu.")
        if st.button("Créer une fiche", key=f"creer_fiche_{jeu_id}"):
            st.session_state.jeu_selectionne_id = jeu_id
            st.session_state.action = "creer_fiche"
            st.rerun()

    st.divider()

    col_modif, col_suppr = st.columns(2)

    with col_modif:
        if st.button(
            "Modifier ce jeu",
            key=f"modif_{jeu_id}",
            use_container_width=True
        ):
            st.session_state.jeu_a_modifier = jeu_id
            st.session_state.action = "modifier_jeu"
            st.rerun()

    with col_suppr:
        if st.button(
            "Supprimer ce jeu",
            key=f"suppr_{jeu_id}",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.jeu_a_supprimer = jeu_id
            st.rerun()

    if st.session_state.get("jeu_a_supprimer") == jeu_id:
        st.error(f"Supprimer '{jeu['titre']}' définitivement ?")
        col_oui, col_non = st.columns(2)

        with col_oui:
            if st.button("Oui, supprimer", key=f"confirme_{jeu_id}"):
                delete_jeu(jeu_id)
                st.session_state.jeu_selectionne_id = None
                st.session_state.jeu_a_supprimer = None
                st.success("Jeu supprimé.")
                st.rerun()

        with col_non:
            if st.button("Annuler", key=f"annule_{jeu_id}"):
                st.session_state.jeu_a_supprimer = None
                st.rerun()