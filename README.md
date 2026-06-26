# i_lib - Gestionnaire de ludothèque pédagogique

## Table des matières

1. [Description](#description)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture](#architecture)
4. [Dépendances](#dépendances)
5. [Installation](#installation)
6. [API - Fonctions principales](#api-fonctions-principales)
7. [Structures de données](#structures-de-données)
8. [Complexité algorithmique](#complexité-algorithmique)
9. [Tests et bogues](#tests-et-bogues)
10. [Statistiques des données](#statistiques-des-données)
11. [Contribution](#contribution)

---

## Description

**i_lib** est une application Python locale de gestion de ludothèque. Elle s'appuie sur Streamlit pour l'interface et SQLite pour le stockage. Aucune connexion internet n'est requise au-delà de l'installation initiale.

Le moteur de recherche intègre un pipeline TAL (Traitement Automatique des Langues) via spaCy : tokenisation, suppression des mots vides et lemmatisation permettent de retrouver un jeu même en tapant une forme fléchie du mot.

### Contexte

Projet réalisé dans le cadre des cours de gestion de projet et de programmation Python pour le TAL, en Master Industries de la langue à l’Université Grenoble Alpes (2025–2026). Le projet a été développé en groupe de quatre étudiants, selon une approche Scrum (quatre sprints de deux semaines)

### Etudiants

- Jiahong Zhang
- Narcisse Affodehou
- Melissa Afettouche
- Samira Guerraiche

---

## Fonctionnalités

- Catalogue de jeux avec recherche par mots-clés
- Filtres combinés par catégorie et âge
- Ajout, modification et suppression de jeux
- Upload d'images et de règles PDF par jeu
- Ouverture des règles PDF dans le navigateur
- Gestion de fiches pédagogiques par jeu (compétences, objectifs, résumé des règles)
- Éditeur de texte riche sur les fiches (gras, italique, couleurs, listes - via streamlit-quill)
- Export des fiches pédagogiques en PDF (le texte brut est extrait - la mise en forme HTML n'est pas conservée dans le PDF, voir [bogues connus](#bogues-connus-non-corrigés))
- Page Bilan autonome pour consigner les séances avec export PDF
- Migration automatique depuis un fichier Excel au premier lancement
- Lancement en double-clic sous Windows (`.bat`)

---

## Architecture

```
i_lib/
├── app.py              # Point d'entrée - routage par session_state
├── database.py         # Couche données - SQLite, migrations, TAL
├── vue_catalogue.py    # Écran catalogue - liste et détail des jeux
├── ajouter_jeu.py      # Formulaire ajout/modification d'un jeu
├── fiche_peda.py       # Fiche pédagogique par jeu + export PDF
├── bilan.py            # Page bilan de séance + export PDF
├── data/
│   └── i_lib.db        # Base SQLite (générée automatiquement)
├── images_jeux/        # Images des jeux (.jpg, .png)
├── regle_jeux/         # Règles des jeux (.pdf)
├── tableurs/
│   └── inventaire_jeux.xlsx  # Source de la migration initiale
├── requirements.txt
├── Lancer i_lib.bat    # Lancement Windows (crée le venv si absent)
└── Fermer i_lib.bat    # Arrêt Windows
```

---

## Dépendances

### Bibliothèques Python

| Bibliothèque | Rôle |
|---|---|
| `streamlit` >= 1.32 | Interface graphique web |
| `pandas` | Lecture du fichier Excel |
| `openpyxl` | Support .xlsx pour pandas |
| `Pillow` | Redimensionnement et affichage des images |
| `spacy` | Tokenisation et lemmatisation (TAL) |
| `streamlit-quill` | Éditeur de texte riche (WYSIWYG) |
| `reportlab` | Génération des PDF |
| `beautifulsoup4` | Nettoyage du HTML produit par streamlit-quill |
| `sqlite3` | Base de données locale (inclus Python) |
| `unicodedata` | Suppression des accents (inclus Python) |

### Modèle spaCy

| Modèle | Langue | Rôle |
|---|---|---|
| `fr_core_news_sm` | Français | Tokenisation, lemmatisation, stop words |

---

## Installation

### Prérequis

- **Python 3.11** - versions ultérieures incompatibles avec spaCy
- Téléchargeable sur https://www.python.org/downloads/release/python-3110/
- Cocher **"Add Python to PATH"** lors de l'installation

### Windows - installation automatique

Cloner ou télécharger le dépôt, puis double-cliquer sur `Lancer i_lib.bat`.

Le script crée automatiquement le venv, installe les dépendances et télécharge le modèle spaCy si nécessaire. La première exécution peut prendre quelques minutes.

> Si le navigateur affiche "localhost n'autorise pas la connexion", patienter quelques secondes - Streamlit n'est pas encore prêt.

### Installation manuelle

```bash
git clone https://github.com/narsatGit/i_lib.git
cd i_lib

python -m venv venv

# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download fr_core_news_sm

streamlit run app.py
```

### Compatibilité

> spaCy est **incompatible avec Python 3.12 et supérieur**. Utiliser Python 3.11.

---

## API - Fonctions principales

### `database.py`

#### `get_connection()`
```
Entrée : aucune
Sortie : sqlite3.Connection avec row_factory et foreign_keys actifs
```

#### `init_db()`
```
Crée les tables jeux, fiches_pedagogiques et bilans (IF NOT EXISTS).
Entrée : aucune
Sortie : aucune - effet de bord sur i_lib.db
```

#### `migrate_excel()`
```
Lit tableurs/inventaire_jeux.xlsx et peuple la table jeux.
Garde-fou : s'arrête si la table n'est pas vide.
Force dtype=str pour éviter qu'Excel interprète "2-4" comme une date.
Entrée : aucune
Sortie : aucune
Complexité : O(n) - n = lignes Excel
```

#### `normaliser_texte(texte)`
```
Preprocessing TAL : minuscules + suppression accents (NFD) + ponctuation.
Entrée : str
Sortie : str
Complexité : O(n)
```

#### `tokeniser(texte)`
```
Pipeline spaCy : tokenisation + filtrage mots vides + lemmatisation.
"joueurs" -> "joueur", "éducatifs" -> "éducatif"
Entrée : str
Sortie : list[str]
Complexité : O(n)
```

#### `extraire_mots_cles(texte, n=5)`
```
Fréquence des lemmes, tri décroissant, retourne les n premiers.
Entrée : str, int
Sortie : list[str]
Complexité : O(n log n) - dominé par le tri
```

#### `search_jeux(terme, categorie, age_max, duree_max)`
```
Tokenise le terme via spaCy, construit dynamiquement la clause WHERE.
Cherche dans : titre, thème, catégorie, sous_classification, éditeur.
Entrée : str, str|None, int|None, int|None
Sortie : list[sqlite3.Row]
Complexité : O(t * c) - t = tokens, c = colonnes cherchées (5)
```

#### CRUD jeux
```
add_jeu(titre, ...)     -> int (lastrowid)
update_jeu(jeu_id, ...) -> None
delete_jeu(jeu_id)      -> None (CASCADE sur fiches_pedagogiques)
get_all_jeux()          -> list[sqlite3.Row]
get_jeu_by_id(jeu_id)   -> sqlite3.Row | None
Complexité : O(1)
```

#### CRUD fiches_pedagogiques
```
add_fiche(jeu_id, competences, objectifs, resume_regles) -> int
update_fiche(fiche_id, ...)                               -> None
delete_fiche(fiche_id)                                    -> None
get_fiche_by_jeu(jeu_id)                                  -> sqlite3.Row | None
Complexité : O(1)
```

#### CRUD bilans
```
add_bilan(jeu_id, bilan_seances, observations, notes_libres) -> int
update_bilan(bilan_id, ...)                                   -> None
delete_bilan(bilan_id)                                        -> None
get_bilan_by_jeu(jeu_id)                                      -> sqlite3.Row | None
Complexité : O(1)
```

---

### `vue_catalogue.py`

#### `show()`
```
Écran principal : barre de recherche, filtres, liste défilante, panneau détail.
Entrée : aucune (lit session_state)
Sortie : rendu Streamlit
```

#### `afficher_detail(jeu_id)`
```
Détail d'un jeu : image (Pillow), PDF (base64), fiche, boutons action.
Entrée : int
Sortie : rendu Streamlit
```

---

### `ajouter_jeu.py`

#### `show(mode)`
```
Formulaire ajout/modification. Pré-remplit en mode "modifier".
Entrée : str - "ajouter" | "modifier"
Sortie : rendu Streamlit
```

#### `sauvegarder_image(uploaded_file, titre)`
```
Sauvegarde dans images_jeux/, nomme le fichier d'après le titre.
Entrée : UploadedFile, str
Sortie : str (nom fichier) | None
```

#### `sauvegarder_pdf(uploaded_file, titre)`
```
Sauvegarde dans regle_jeux/, même logique que sauvegarder_image.
Entrée : UploadedFile, str
Sortie : str (nom fichier) | None
```

---

### `fiche_peda.py`

#### `show()`
```
Formulaire création/modification fiche pédagogique avec streamlit-quill.
Crée ou met à jour selon l'existence de la fiche (add_fiche vs update_fiche).
Entrée : aucune (lit session_state.jeu_selectionne_id)
Sortie : rendu Streamlit
```

#### `generer_pdf_fiche(jeu, fiche)`
```
Génère un PDF reportlab depuis les données de la fiche.
Le HTML produit par streamlit-quill est parsé via BeautifulSoup
avant d'être envoyé à reportlab (texte brut uniquement).
Entrée : sqlite3.Row, sqlite3.Row
Sortie : bytes
```

---

### `bilan.py`

Page autonome - non liée à un jeu spécifique. Permet de consigner le bilan d'une séance avec titre, date, trois zones de texte riche et export PDF.

#### `show()`
```
Affiche le formulaire de bilan avec éditeur streamlit-quill.
Non lié à un jeu - accessible depuis le menu principal.
Entrée : aucune
Sortie : rendu Streamlit
```

#### `generer_pdf_bilan(titre_seance, date_seance, bilan_seances, observations, notes_libres)`
```
Génère un PDF reportlab du bilan de séance.
Entrée : str, str, str, str, str
Sortie : bytes
```

#### `nettoyer_html_quill(html)`
```
Extrait le texte brut depuis le HTML de streamlit-quill via BeautifulSoup.
Nécessaire car reportlab n'accepte pas les balises HTML complexes.
Entrée : str (HTML)
Sortie : str (texte brut)
```

---

## Structures de données

### Table `jeux`

| Colonne | Type | Contrainte |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| titre | TEXT | NOT NULL |
| editeur | TEXT | |
| age_minimum | INTEGER | |
| duree_min | INTEGER | |
| nb_joueurs | TEXT | |
| categorie | TEXT | |
| classification_esar | TEXT | |
| sous_classification_1 | TEXT | |
| sous_classification_2 | TEXT | |
| sous_classification_3 | TEXT | |
| theme | TEXT | |
| fichier_regle | TEXT | nom du fichier PDF |
| fichier_image | TEXT | nom du fichier image |
| date_ajout | TEXT | DEFAULT CURRENT_TIMESTAMP |

### Table `fiches_pedagogiques`

| Colonne | Type | Contrainte |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| jeu_id | INTEGER | NOT NULL, FK -> jeux(id) ON DELETE CASCADE |
| competences | TEXT | stocké en HTML (streamlit-quill) |
| objectifs | TEXT | stocké en HTML (streamlit-quill) |
| resume_regles | TEXT | stocké en HTML (streamlit-quill) |
| date_modification | TEXT | DEFAULT CURRENT_TIMESTAMP |



### Relations

```
jeux (1) -------- (0..1) fiches_pedagogiques


ON DELETE CASCADE : la suppression d'un jeu entraîne la suppression
                     de sa fiche.
```

### Dataset Excel source

```
Feuille  : "Inventaire des jeux"
Format   : .xlsx
Colonnes : titre_jeu, editeur, age_minimum (float64), duree_min (float64),
           nb_joueurs (object), categorie_jeu, classification_ESAR,
           sous_classification_ESAR, theme, regles, images

Transformations à la migration :
  NaN pandas         -> None -> NULL SQLite
  float64 (15.0)     -> int (15) pour age_minimum et duree_min
  dtype=str forcé    -> évite qu'Excel convertisse "2-4" en datetime
```

### Objets spaCy

```
doc = nlp("Les joueurs développent leur mémoire visuelle.")

doc[1] : Token {
  text    : "joueurs"
  lemma_  : "joueur"
  pos_    : "NOUN"
  is_stop : False
}

tokeniser() -> ["joueur", "développer", "mémoire", "visuel"]

extraire_mots_cles() :
  fréquences : dict[str, int] -- {"mémoire": 3, "coordination": 2}
  sortie     : list[str]      -- ["mémoire", "coordination"]
```

### Session state Streamlit

```
action             : str  -- "catalogue" | "ajouter_jeu" | "modifier_jeu"
                            | "creer_fiche" | "modifier_fiche" | "bilan"
jeu_selectionne_id : int  -- jeu affiché dans le panneau détail
jeu_a_modifier     : int  -- jeu cible du formulaire modification
jeu_a_supprimer    : int  -- jeu en attente de confirmation suppression
form_key           : int  -- incrémentée à l'annulation pour vider le formulaire
```

---

## Complexité algorithmique

| Fonction | Temps | Espace | Note |
|---|---|---|---|
| `get_connection()` | O(1) | O(1) | |
| `init_db()` | O(1) | O(1) | IF NOT EXISTS |
| `migrate_excel()` | O(n) | O(n) | n = lignes Excel |
| `normaliser_texte()` | O(n) | O(n) | n = longueur texte |
| `tokeniser()` | O(n) | O(n) | n = tokens |
| `extraire_mots_cles()` | O(n log n) | O(n) | dominé par le tri |
| `search_jeux()` | O(t × c × r) | O(r) | t=tokens, c=5 colonnes, r=résultats |
| `get_all_jeux()` | O(r) | O(r) | r = nb jeux |
| `get_jeu_by_id()` | O(1) | O(1) | clé primaire |
| `add_jeu()` | O(1) | O(1) | |
| `update_jeu()` | O(1) | O(1) | |
| `delete_jeu()` | O(1) | O(1) | + CASCADE |
| `get_fiche_by_jeu()` | O(1) | O(1) | clé étrangère indexée |
| `add_fiche()` | O(1) | O(1) | |
| `update_fiche()` | O(1) | O(1) | |
| `nettoyer_html_quill()` | O(n) | O(n) | n = longueur HTML |
| `generer_pdf_fiche()` | O(n) | O(n) | n = blocs reportlab |
| `generer_pdf_bilan()` | O(n) | O(n) | n = blocs reportlab |

---

## Tests et bogues

### Tests effectués

| Test | Résultat |
|---|---|
| Migration Excel au premier lancement | Passé |
| Garde-fou contre les doublons | Passé |
| Recherche lemmatisée ("joueurs" -> "joueur") | Passé |
| Filtres combinés catégorie + âge | Passé |
| Ajout d'un jeu avec image et PDF | Passé |
| Modification d'un jeu (champs pré-remplis) | Passé |
| Suppression avec confirmation + CASCADE | Passé |
| Création et modification fiche pédagogique | Passé |
| Export PDF fiche pédagogique | Passé |
| Export PDF bilan de séance | Passé |
| Ouverture PDF règles dans nouvel onglet | Passé |
| Lancement .bat sans terminal visible | Passé |
| Port fixe à 8501 entre sessions | Passé |

### Bogues corrigés

| ID | Description | Cause | Correction |
|---|---|---|---|
| BUG-01 | `nb_joueurs` interprété comme date | Excel convertit "2-4" en datetime | `dtype=str` dans `pd.read_excel()` |
| BUG-02 | Port Streamlit change à chaque lancement | Port occupé par instance précédente | `taskkill` + `--server.port 8501` |
| BUG-03 | spaCy incompatible Python 3.12+ | Conflit dépendance `catalogue` | Downgrade Python 3.11 |
| BUG-04 | Bouton "Modifier" sans effet | Ordre `elif` incorrect dans `app.py` | Actions session_state avant pages |
| BUG-05 | Liste jeux allonge toute la page | Pas de conteneur à hauteur fixe | `st.container(height=700)` |
| BUG-06 | Annuler ne vide pas le formulaire | Limitation `st.form()` | `form_key` incrémentée |
| BUG-07 | Export PDF plante avec HTML Quill | `<span style>` non supporté par reportlab | Nettoyage BeautifulSoup avant envoi à reportlab |

### Bogues connus non corrigés

| ID | Description | Impact |
|---|---|---|
| BUG-09 | Export PDF ne conserve pas la mise en forme HTML | La mise en forme (gras, couleurs, italique) saisie dans l'éditeur streamlit-quill est perdue lors de l'export PDF. Seul le texte brut est extrait. La mise en forme reste visible dans l'interface Streamlit. Cause : reportlab n'accepte pas les balises HTML complexes produites par streamlit-quill (`<span style>`, `<strong>`, etc.). Solution envisagée : remplacer reportlab par weasyprint. |
| BUG-10 | PDF très lourds (>10 Mo) lents à ouvrir | Encodage base64 dans le lien HTML |

---

## Statistiques des données

```
Fichier Excel source :
  Lignes de données : ~207
  Colonnes          : 11
  Valeurs nulles    : fréquentes (theme, classification_esar)

Base SQLite après migration :
  Table jeux                : ~207 enregistrements
  Table fiches_pedagogiques : 0 au départ
  Table bilans               : 0 au départ

Répartition catégories (approximative) :
  Éducatif   : ~35%
  Ambiance   : ~25%
  Coopératif : ~20%
  Stratégie  : ~10%
  Autres     : ~10%

Modèle spaCy fr_core_news_sm :
  Taille      : ~15 Mo
  Stop words  : ~1300 mots vides français
  Pipeline    : tokenizer, morphologizer, tagger, parser, lemmatizer, ner
```

---

## Contribution

Les contributions sont les bienvenues. Pour proposer une amélioration :

1. Forker le dépôt
2. Créer une branche (`git checkout -b feature/nom-fonctionnalite`)
3. Commiter les changements (`git commit -m "description"`)
4. Pousser la branche (`git push origin feature/nom-fonctionnalite`)
5. Ouvrir une Pull Request

### Pistes d'amélioration identifiées

- Remplacer reportlab par weasyprint pour conserver la mise en forme HTML dans les PDF
- Ajouter une page statistiques (répartition par catégorie, jeux sans fiche, etc.)
- Permettre plusieurs thèmes par jeu (table de relation n-n)
- Séparer nb_joueurs en deux champs min/max
- Ajouter un champ "état/défaut" pour le suivi de l'usure des jeux
- Version Mac/Linux du script de lancement