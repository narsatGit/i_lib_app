import streamlit as st

from database import (
    init_db,
    migrate_excel
)

st.set_page_config(
    page_title="i_lib",
    page_icon="🎲",
    layout="wide"
)

init_db()
migrate_excel()

if "action" not in st.session_state:
    st.session_state.action = "catalogue"

st.markdown("## 🎲 i_lib")
st.divider()

with st.sidebar:

    st.markdown("### Menu")

    # synchronise le radio avec l'action en cours, sans la forcer
    # si l'action vient d'un bouton interne (modifier_jeu, creer_fiche...)
    if st.session_state.action in (
        "catalogue", "modifier_jeu", "creer_fiche", "modifier_fiche"
    ):
        default_page = "Catalogue des jeux"
    elif st.session_state.action == "ajouter_jeu":
        default_page = "Ajouter un jeu"
    elif st.session_state.action == "bilan":
        default_page = "Bilan"
    else:
        default_page = "Catalogue des jeux"

    options = ["Catalogue des jeux", "Ajouter un jeu", "Bilan"]
    page = st.radio(
        label="Navigation",
        options=options,
        index=options.index(default_page),
        label_visibility="collapsed"
    )

    # ne change l'action que si l'utilisateur clique réellement
    # dans le menu (évite d'écraser une action interne en cours)
    if page == "Catalogue des jeux":
        if st.session_state.action not in (
            "catalogue", "modifier_jeu", "creer_fiche", "modifier_fiche"
        ):
            st.session_state.action = "catalogue"
            st.rerun()

    elif page == "Ajouter un jeu":
        if st.session_state.action != "ajouter_jeu":
            st.session_state.action = "ajouter_jeu"
            st.rerun()

    elif page == "Bilan":
        if st.session_state.action != "bilan":
            st.session_state.action = "bilan"
            st.rerun()

action = st.session_state.get("action")

if action == "catalogue":
    import vue_catalogue
    vue_catalogue.show()

elif action == "ajouter_jeu":
    import ajouter_jeu
    ajouter_jeu.show(mode="ajouter")

elif action == "modifier_jeu":
    import ajouter_jeu
    ajouter_jeu.show(mode="modifier")

elif action in ("creer_fiche", "modifier_fiche"):
    import fiche_peda
    fiche_peda.show()

elif action == "bilan":
    import bilan
    bilan.show()

else:
    # filet de sécurité si action prend une valeur inattendue
    st.session_state.action = "catalogue"
    st.rerun()