import streamlit as st
import os
from io import BytesIO
import re
from html import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    ListFlowable,
    ListItem
)

from streamlit_quill import st_quill
from bs4 import BeautifulSoup

from database import (
    get_jeu_by_id,
    get_fiche_by_jeu,
    add_fiche,
    update_fiche,
    extraire_mots_cles
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images_jeux")



# Sécurité sqlite3.Row


def safe_get(row, key):

    try:
        return row[key]

    except:
        return None



# Nettoyage texte


def clean_text(text):

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()



# Parsing Quill sécurisé


def parse_quill(html):

    if not html:
        return []

    soup = BeautifulSoup(
        str(html),
        "html.parser"
    )

    blocks = []

    # Paragraphes

    for p in soup.find_all("p"):

        txt = clean_text(
            p.get_text(" ", strip=True)
        )

        if txt:

            blocks.append((
                "p",
                escape(txt)
            ))

    # Listes UL

    for ul in soup.find_all("ul"):

        items = []

        for li in ul.find_all("li"):

            txt = clean_text(
                li.get_text(" ", strip=True)
            )

            if txt:

                items.append(
                    escape(txt)
                )

        if items:

            blocks.append((
                "ul",
                items
            ))

    # Listes OL

    for ol in soup.find_all("ol"):

        items = []

        for li in ol.find_all("li"):

            txt = clean_text(
                li.get_text(" ", strip=True)
            )

            if txt:

                items.append(
                    escape(txt)
                )

        if items:

            blocks.append((
                "ol",
                items
            ))

    return blocks



# Génération PDF


def generer_pdf_fiche(jeu, fiche):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    # Couleurs

    VIOLET = colors.HexColor("#4F46E5")
    GRIS = colors.HexColor("#475569")

    # Styles

    titre_style = ParagraphStyle(
        "titre",
        fontSize=18,
        textColor=VIOLET,
        fontName="Helvetica-Bold",
        spaceAfter=8
    )

    section_style = ParagraphStyle(
        "section",
        fontSize=12,
        textColor=VIOLET,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "body",
        fontSize=10,
        textColor=GRIS,
        fontName="Helvetica",
        leading=16,
        spaceAfter=6
    )

    contenu = []

    
    # Titre
    

    contenu.append(
        Paragraph(
            escape(jeu["titre"]),
            titre_style
        )
    )

    
    # Infos jeu
    

    infos = []

    if safe_get(jeu, "editeur"):

        infos.append(
            f"Éditeur : {jeu['editeur']}"
        )

    if safe_get(jeu, "age_minimum"):

        infos.append(
            f"Âge : {jeu['age_minimum']} ans"
        )

    if safe_get(jeu, "duree_min"):

        infos.append(
            f"Durée : {jeu['duree_min']} min"
        )

    if safe_get(jeu, "categorie"):

        infos.append(
            f"Catégorie : {jeu['categorie']}"
        )

    if infos:

        contenu.append(
            Paragraph(
                escape(" | ".join(infos)),
                body_style
            )
        )

    contenu.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=VIOLET
        )
    )

    contenu.append(
        Spacer(1, 0.3 * cm)
    )

    
    # Parsing sécurisé
    

    competences = parse_quill(
        safe_get(fiche, "competences")
    )

    objectifs = parse_quill(
        safe_get(fiche, "objectifs")
    )

    resume = parse_quill(
        safe_get(fiche, "resume_regles")
    )

    
    # Rendu sections
    

    def render(title, blocks):

        contenu.append(
            Paragraph(
                escape(title),
                section_style
            )
        )

        for typ, data in blocks:

            # Paragraphes

            if typ == "p":

                contenu.append(
                    Paragraph(
                        data,
                        body_style
                    )
                )

            # Liste UL

            elif typ == "ul":

                items = []

                for item in data:

                    items.append(
                        ListItem(
                            Paragraph(
                                item,
                                body_style
                            )
                        )
                    )

                contenu.append(
                    ListFlowable(
                        items,
                        bulletType="bullet"
                    )
                )

            # Liste OL

            elif typ == "ol":

                items = []

                for item in data:

                    items.append(
                        ListItem(
                            Paragraph(
                                item,
                                body_style
                            )
                        )
                    )

                contenu.append(
                    ListFlowable(
                        items,
                        bulletType="1"
                    )
                )

        contenu.append(
            Spacer(1, 0.25 * cm)
        )

    
    # Sections PDF
    

    render(
        "Compétences mobilisées",
        competences
    )

    render(
        "Objectifs pédagogiques",
        objectifs
    )

    render(
        "Résumé des règles",
        resume
    )

    
    # Mots-clés
    

    # texte = " ".join([
    #     safe_get(fiche, "competences") or "",
    #     safe_get(fiche, "objectifs") or "",
    #     safe_get(fiche, "resume_regles") or ""
    # ])

    # mots_cles = extraire_mots_cles(
    #     texte,
    #     n=8
    # )

    # if mots_cles:

    #     contenu.append(
    #         HRFlowable(
    #             width="100%",
    #             thickness=0.5,
    #             color=GRIS
    #         )
    #     )

    #     contenu.append(
    #         Spacer(1, 0.15 * cm)
    #     )

    #     contenu.append(
    #         Paragraph(
    #             escape(
    #                 "Mots-clés : " +
    #                 ", ".join(mots_cles)
    #             ),
    #             body_style
    #         )
    #     )

    
    # Construction PDF
    

    doc.build(contenu)

    buffer.seek(0)

    return buffer.read()



# Interface Streamlit


def show():

    jeu_id = st.session_state.get(
        "jeu_selectionne_id"
    )

    # Vérification jeu

    if not jeu_id:

        st.warning(
            "Aucun jeu sélectionné."
        )

        return

    # Chargement données

    jeu = get_jeu_by_id(jeu_id)

    fiche = get_fiche_by_jeu(jeu_id)

    if not jeu:

        st.error(
            "Jeu introuvable."
        )

        return

    
    # En-tête
    

    col_img, col_info = st.columns([1, 3])

    with col_img:

        fichier_image = safe_get(
            jeu,
            "fichier_image"
        )

        if fichier_image:

            chemin = os.path.join(
                IMG_DIR,
                fichier_image
            )

            if os.path.exists(chemin):

                st.image(
                    chemin,
                    width=120
                )

    with col_info:

        st.markdown(
            f"### {jeu['titre']}"
        )

        infos = []

        if safe_get(jeu, "editeur"):

            infos.append(
                f"Éditeur : {jeu['editeur']}"
            )

        if safe_get(jeu, "age_minimum"):

            infos.append(
                f"Âge : {jeu['age_minimum']} ans"
            )

        if safe_get(jeu, "duree_min"):

            infos.append(
                f"Durée : {jeu['duree_min']} min"
            )

        if safe_get(jeu, "categorie"):

            infos.append(
                f"Catégorie : {jeu['categorie']}"
            )

        st.caption(
            " | ".join(infos)
        )

    st.divider()

    
    # Valeurs initiales
    

    val_comp = (
        safe_get(fiche, "competences")
        if fiche else ""
    )

    val_obj = (
        safe_get(fiche, "objectifs")
        if fiche else ""
    )

    val_res = (
        safe_get(fiche, "resume_regles")
        if fiche else ""
    )

    
    # Éditeurs Quill
    

    st.markdown(
        "**Compétences mobilisées**"
    )

    competences = st_quill(
        value=val_comp,
        html=True,
        key="quill_comp"
    )

    st.markdown(
        "**Objectifs pédagogiques**"
    )

    objectifs = st_quill(
        value=val_obj,
        html=True,
        key="quill_obj"
    )

    st.markdown(
        "**Résumé des règles**"
    )

    resume = st_quill(
        value=val_res,
        html=True,
        key="quill_res"
    )

    st.divider()

    
    # Boutons
    

    col_save, col_pdf, col_annuler = st.columns(3)

    # Sauvegarde

    with col_save:

        if st.button(
            "Enregistrer",
            use_container_width=True,
            type="primary"
        ):

            if fiche:

                update_fiche(
                    fiche_id=fiche["id"],
                    competences=competences,
                    objectifs=objectifs,
                    resume_regles=resume
                )

            else:

                add_fiche(
                    jeu_id=jeu_id,
                    competences=competences,
                    objectifs=objectifs,
                    resume_regles=resume
                )

            st.success(
                "Fiche enregistrée."
            )

            st.rerun()
    

    # Export PDF

    with col_pdf:

        if fiche:

            try:

                pdf = generer_pdf_fiche(
                    jeu,
                    fiche
                )

                st.download_button(
                    label="Exporter PDF",
                    data=pdf,
                    file_name=f"fiche_{jeu['titre'].lower().replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            except Exception as e:

                st.error(
                    f"Erreur lors de la génération du PDF : {e}"
                )

        else:

            st.button(
                "Exporter PDF",
                disabled=True,
                use_container_width=True
            )
            
            
    # Annuler
    
    # Annuler

    with col_annuler:

        if st.button(
            "Annuler",
            use_container_width=True
        ):

            # Retour catalogue

            st.session_state.action = "catalogue"

            # Nettoyage éventuel

            if "jeu_a_modifier" in st.session_state:
                del st.session_state["jeu_a_modifier"]

            st.rerun()