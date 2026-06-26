import streamlit as st
from io import BytesIO
from datetime import datetime
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)

from streamlit_quill import st_quill
from bs4 import BeautifulSoup


def nettoyer_html_quill(html):
    """
    Extrait le texte brut du HTML Quill.
    Nécessaire : reportlab ne supporte pas <span style>, <strong>, etc.
    Entrée : str (HTML)
    Sortie : str (texte brut)
    """
    if not html:
        return "—"

    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        img.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for tag in soup.find_all(["p", "div", "h1", "h2", "h3", "li"]):
        tag.append("\n")

    texte = soup.get_text()
    texte = re.sub(r"\n\s*\n+", "\n\n", texte)
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = texte.strip()

    return texte if texte else "—"


def generer_pdf_bilan(titre_seance, date_seance, bilan_seances,
                       observations, notes_libres):
    """
    Génère le PDF du bilan via reportlab.
    NB : la mise en forme HTML (gras, couleurs) n'est pas conservée,
    seul le texte brut est exporté.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )

    VERT = colors.HexColor("#059669")
    GRIS = colors.HexColor("#475569")

    titre_style = ParagraphStyle(
        "titre", fontSize=18, textColor=VERT,
        fontName="Helvetica-Bold", spaceAfter=4
    )
    date_style = ParagraphStyle(
        "date", fontSize=10, textColor=GRIS,
        fontName="Helvetica", spaceAfter=8
    )
    section_style = ParagraphStyle(
        "section", fontSize=12, textColor=VERT,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4
    )
    body_style = ParagraphStyle(
        "body", fontSize=10, textColor=GRIS,
        fontName="Helvetica", leading=16, spaceAfter=10
    )

    contenu = []

    contenu.append(Paragraph(titre_seance or "Bilan de séance", titre_style))
    contenu.append(Paragraph(f"Date : {date_seance}", date_style))
    contenu.append(HRFlowable(width="100%", thickness=1, color=VERT))
    contenu.append(Spacer(1, 0.3 * cm))

    bilan_clean = nettoyer_html_quill(bilan_seances)
    observations_clean = nettoyer_html_quill(observations)
    notes_clean = nettoyer_html_quill(notes_libres)

    # reportlab interprète <br/> mais pas <span> ni <strong> issus de Quill
    contenu.append(Paragraph("Bilan de la séance", section_style))
    contenu.append(Paragraph(bilan_clean.replace("\n", "<br/>"), body_style))

    contenu.append(Paragraph("Observations personnelles", section_style))
    contenu.append(Paragraph(observations_clean.replace("\n", "<br/>"), body_style))

    contenu.append(Paragraph("Notes libres", section_style))
    contenu.append(Paragraph(notes_clean.replace("\n", "<br/>"), body_style))

    doc.build(contenu)
    buffer.seek(0)
    return buffer.read()


def show():
    """Page Bilan, indépendante des jeux."""

    st.markdown("### Bilan de séance")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        titre_seance = st.text_input(
            "Titre de la séance",
            placeholder="Ex : Séance du 15 mars - Jeux de mémoire"
        )

    with col2:
        date_seance = st.date_input(
            "Date de la séance",
            value=datetime.today()
        )

    st.divider()

    st.markdown("**Bilan de la séance**")
    bilan_seances = st_quill(
        placeholder="Décrivez le déroulement de la séance...",
        html=True,
        key="quill_seances"
    )

    st.markdown("**Observations personnelles**")
    observations = st_quill(
        placeholder="Vos observations sur les joueurs, les difficultés...",
        html=True,
        key="quill_observations"
    )

    st.markdown("**Notes libres**")
    notes_libres = st_quill(
        placeholder="Espace libre pour toute autre note...",
        html=True,
        key="quill_notes"
    )

    st.divider()

    col_pdf, col_vide = st.columns([1, 2])

    with col_pdf:
        if st.button("Exporter en PDF", use_container_width=True, type="primary"):

            if not any([bilan_seances, observations, notes_libres]):
                st.warning("Remplissez au moins un champ avant d'exporter.")
            else:
                try:
                    pdf_bytes = generer_pdf_bilan(
                        titre_seance=titre_seance,
                        date_seance=str(date_seance),
                        bilan_seances=bilan_seances,
                        observations=observations,
                        notes_libres=notes_libres
                    )

                    nom_fichier = f"bilan_{date_seance}.pdf"
                    if titre_seance:
                        titre_clean = titre_seance.lower().replace(" ", "_")
                        nom_fichier = f"bilan_{titre_clean}.pdf"

                    st.success("PDF généré avec succès.")

                    st.download_button(
                        label="Télécharger le PDF",
                        data=pdf_bytes,
                        file_name=nom_fichier,
                        mime="application/pdf",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF : {e}")