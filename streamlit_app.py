import os
import streamlit as st
import requests
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta
import base64
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

st.set_page_config(
    page_title="Colloscope TSI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
CONFIG = {
    "max_groups": 20,
    "max_weeks": 30,
    "max_classes": 2,
    "school_year_start_month": 9,
    "cache_ttl_hours": 24,
}

# Charger le code propriétaire depuis une variable d'environnement (sécurité améliorée)
OWNER_CODE = os.getenv("COLLOSCOPE_OWNER_CODE", "debug123")

# ============================================================================
# UTILITAIRES DE SÉCURITÉ & FICHIERS
# ============================================================================

def chemin_ressource(chemin_relatif: str) -> str:
    """Résout un chemin relatif par rapport au répertoire de travail."""
    return os.path.join(os.path.abspath("."), chemin_relatif)

def charger_parametres() -> Tuple[str, str, str]:
    """Charge les paramètres sauvegardés (groupe, semaine, classe)."""
    defaults = {"groupe": "G1", "semaine": "1", "classe": "1"}
    
    config_file = Path('config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return (
                    data.get("groupe", defaults["groupe"]),
                    data.get("semaine", defaults["semaine"]),
                    data.get("classe", defaults["classe"])
                )
        except (json.JSONDecodeError, IOError):
            pass
    
    return defaults["groupe"], defaults["semaine"], defaults["classe"]

def enregistrer_parametres(groupe: str, semaine: str, classe: str) -> None:
    """Enregistre les paramètres (groupe, semaine, classe) en JSON."""
    config_file = Path('config.json')
    try:
        with open(config_file, 'w') as f:
            json.dump({"groupe": groupe, "semaine": semaine, "classe": classe}, f)
    except IOError as e:
        st.warning(f"Impossible d'enregistrer les paramètres : {e}")

# ============================================================================
# TRAITEMENT DES DONNÉES
# ============================================================================

def aplatir_liste(liste_imbriquee: List[List[str]]) -> List[str]:
    """Aplatit une liste imbriquée en joignant les sous-listes par espaces."""
    return [' '.join(sous_liste) if sous_liste else '' for sous_liste in liste_imbriquee]

def extract_date(cell_str: str, year: int) -> Optional[datetime]:
    """Extrait la date d'une chaîne de cellule (format: (JJ/MM)) et l'associe à l'année."""
    match = re.search(r'\((\d{2}/\d{2})\)', cell_str)
    if match:
        date_str = match.group(1)
        full_date_str = f"{date_str}/{year}"
        try:
            return datetime.strptime(full_date_str, "%d/%m/%Y")
        except ValueError:
            return None
    return None

def to_naive(dt: datetime) -> datetime:
    """Convertit un datetime timezone-aware en naive."""
    return dt.replace(tzinfo=None) if dt.tzinfo else dt

def detecter_annee_scolaire_actuelle(date_actuelle: Optional[datetime] = None) -> str:
    """Détecte l'année scolaire actuelle au format 'YYYY-YYYY'."""
    if date_actuelle is None:
        date_actuelle = datetime.now()

    annee_courante = date_actuelle.year
    mois_courant = date_actuelle.month

    if mois_courant >= CONFIG["school_year_start_month"]:
        return f"{annee_courante}-{annee_courante + 1}"
    else:
        return f"{annee_courante - 1}-{annee_courante}"

def semaine_actuelle(dates_semaines: List[Optional[datetime]], 
                     date_actuelle: Optional[datetime] = None) -> int:
    """Détermine le numéro de la semaine actuelle."""
    if date_actuelle is None:
        date_actuelle = datetime.now()
    
    current_weekday = date_actuelle.weekday()
    date_du_lundi = (date_actuelle - timedelta(days=current_weekday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    for i, date_semaine in enumerate(dates_semaines):
        if date_semaine is None:
            continue
        
        lundi_excel = date_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
        if lundi_excel >= date_du_lundi:
            return i + 1
    
    return len(dates_semaines)

# ============================================================================
# CHARGEMENT DES DONNÉES (AVEC CACHE)
# ============================================================================

@st.cache_data(ttl=3600)  # Cache 1 heure
def charger_donnees(classe: str, annee_scolaire_str: str) -> Tuple[Dict, Dict, List]:
    """
    Charge les données du colloscope et de la légende.
    
    Returns:
        tuple: (dictionnaire_donnees, dictionnaire_legende, dates_semaines)
    """
    annee_numerique = int(annee_scolaire_str.split('-')[0])

    try:
        fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
        fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')

        excel_colloscope = load_workbook(fichier_colloscope, data_only=True)
        excel_legende = load_workbook(fichier_legende, data_only=True)

        feuille_colloscope = excel_colloscope.active
        feuille_legende = excel_legende.active

        # Extraire les dates des semaines
        dates_semaines = []
        for cell in feuille_colloscope[1][1:]:
            if cell.value:
                date_extrait = extract_date(str(cell.value), annee_numerique)
                dates_semaines.append(date_extrait)
            else:
                dates_semaines.append(None)

        # Charger les données du colloscope
        dictionnaire_donnees = {}
        for ligne in feuille_colloscope.iter_rows(min_row=2, values_only=True):
            cle = ligne[0]
            valeurs = ligne[1:]
            valeurs = [v.split() if v is not None else [] for v in valeurs]
            dictionnaire_donnees[cle] = valeurs

        # Charger la légende
        dictionnaire_legende = {}
        for ligne in feuille_legende.iter_rows(min_row=2, values_only=True):
            cle_legende = ligne[0]
            valeurs_legende = ligne[1:]
            valeurs_legende = [v.split() if v is not None else [] for v in valeurs_legende]
            dictionnaire_legende[cle_legende] = valeurs_legende

        return dictionnaire_donnees, dictionnaire_legende, dates_semaines

    except FileNotFoundError as e:
        st.error(f"❌ Fichier manquant : {e}")
        return {}, {}, []
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {e}")
        return {}, {}, []

@st.cache_data(ttl=3600)
def obtenir_vacances(zone: str = "C", annee_scolaire_str: Optional[str] = None) -> List[Tuple]:
    """Récupère les dates de vacances scolaires via l'API de l'Éducation nationale."""
    if annee_scolaire_str is None:
        annee_scolaire_str = detecter_annee_scolaire_actuelle()

    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 500,
        "refine.zone": f"Zone {zone}",
        "refine.annee_scolaire": annee_scolaire_str,
    }
    
    vacances = []
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for record in data.get("records", []):
            fields = record.get("fields", {})
            start_str = fields.get("start_date")
            end_str = fields.get("end_date")
            
            if start_str and end_str:
                try:
                    debut = datetime.fromisoformat(start_str)
                    fin = datetime.fromisoformat(end_str)
                    vacances.append((debut, fin))
                except ValueError:
                    continue

        # Filtrer les vacances pour la période pertinente
        annee_debut_num = int(annee_scolaire_str.split('-')[0])
        annee_fin_num = int(annee_scolaire_str.split('-')[1])
        
        periode_debut = datetime(annee_debut_num, CONFIG["school_year_start_month"], 1)
        periode_fin = datetime(annee_fin_num, CONFIG["school_year_start_month"] - 1, 28)

        vacances = [
            (start, end) for start, end in vacances 
            if to_naive(end) >= periode_debut and to_naive(start) <= periode_fin
        ]

    except requests.RequestException as e:
        st.warning(f"⚠️ Impossible de récupérer les vacances : {e}")
    
    return vacances

# ============================================================================
# LOGIQUE MÉTIER
# ============================================================================

MATIERES_MAP = {
    'M': "Mathématiques",
    'A': "Anglais",
    'SI': "Sciences de l'Ingénieur",
    'F': "Français",
    'I': "Informatique",
    'P': "Physique",
    'H': "Histoire-Géo",
    'PHI': "Philosophie",
}

def determiner_matiere(cle: str) -> str:
    """Détermine la matière à partir de la clé."""
    for prefix, matiere in MATIERES_MAP.items():
        if cle.startswith(prefix):
            return matiere
    return "Non spécifié"

def creer_tableau(groupe: str, semaine: str, dictionnaire_donnees: Dict, 
                  dictionnaire_legende: Dict) -> List[List[str]]:
    """Crée le tableau de planning pour un groupe et une semaine."""
    tableau = []
    
    try:
        semaine_int = int(semaine)
        
        if groupe not in dictionnaire_donnees:
            return []

        if not (1 <= semaine_int <= len(dictionnaire_donnees[groupe])):
            return []

        ligne = dictionnaire_donnees[groupe][semaine_int - 1]

        for cle_legende in ligne:
            if cle_legende not in dictionnaire_legende:
                continue 
            
            elements = aplatir_liste(dictionnaire_legende[cle_legende])
            matiere = determiner_matiere(cle_legende)
            elements.append(matiere)
            tableau.append(elements)

    except (ValueError, KeyError, IndexError):
        pass
    
    return tableau

def changer_semaine(sens: int) -> None:
    """Change la semaine dans le session state."""
    if "semaine" in st.session_state:
        nouvelle_semaine = int(st.session_state.semaine) + sens
        if 1 <= nouvelle_semaine <= CONFIG["max_weeks"]:
            st.session_state.semaine = str(nouvelle_semaine)

# ============================================================================
# COMPOSANTS UI
# ============================================================================

def afficher_logo_sidebar():
    """Affiche le logo dans la sidebar."""
    logo_path = "logo_prepa.png"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode()
                html_code = f'''
                <div style="text-align: center; margin-bottom: 30px;">
                    <a href="https://sites.google.com/site/cpgetsimarcelsembat/" target="_blank">
                        <img src="data:image/png;base64,{b64_data}" width="120" style="border-radius: 8px;">
                    </a>
                </div>
                '''
                st.sidebar.markdown(html_code, unsafe_allow_html=True)
        except Exception as e:
            st.sidebar.warning(f"Logo non disponible : {e}")

def afficher_planning(groupe: str, semaine: str, classe: str, 
                      annee_scolaire: str) -> None:
    """Affiche le planning pour le groupe et la semaine sélectionnée."""
    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(
        classe, annee_scolaire
    )
    
    if not dictionnaire_donnees:
        st.error("Impossible de charger les données.")
        return
    
    tableau = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)
    
    if not tableau:
        st.info("📋 Aucun cours pour cette semaine.")
        return
    
    df = pd.DataFrame(tableau, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    
    # Style personnalisé du tableau
    styled_df = df.style.format(escape=False).apply(
        lambda x: ['background-color: #f0f2f6'] * len(x), axis=1
    )
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

def afficher_edt_eps():
    """Affiche les images EDT EPS."""
    eps_files = ["EPS_page-0001.jpg", "EPS_page-0002.jpg"]
    
    col1, col2 = st.columns(2)
    
    for idx, file in enumerate(eps_files):
        if os.path.exists(file):
            try:
                with col1 if idx == 0 else col2:
                    st.image(file, caption=f"EDT EPS TSI{idx + 1}", use_container_width=True)
            except Exception as e:
                st.warning(f"Impossible de charger {file}: {e}")
        else:
            (col1 if idx == 0 else col2).info(f"📄 {file} non trouvé")

# ============================================================================
# GESTION DE L'AUTHENTIFICATION PROPRIÉTAIRE
# ============================================================================

@st.dialog("🔐 Accès Propriétaire")
def dialog_authentification():
    """Dialogue d'authentification pour accès propriétaire."""
    st.write("Entrez le code secret pour accéder aux outils de débogage.")
    
    code_input = st.text_input(
        "Code secret",
        type="password",
        key="dialog_secret_code",
        placeholder="••••••••"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Valider", use_container_width=True):
            if code_input == OWNER_CODE:
                st.session_state["authenticated_owner"] = True
                st.success("✨ Accès accordé !")
                st.rerun()
            else:
                st.error("❌ Code incorrect.")
                st.session_state["authenticated_owner"] = False
    
    with col2:
        if st.button("❌ Fermer", use_container_width=True):
            st.rerun()

# ============================================================================
# ONGLET OUTILS PROPRIÉTAIRE
# ============================================================================

def afficher_dictionnaires(classe: str, annee_scolaire: str) -> None:
    """Affiche les dictionnaires de données et légende."""
    st.subheader("📊 Dictionnaires de données")
    
    try:
        dict_donnees, dict_legende, dates_semaines = charger_donnees(
            classe, annee_scolaire
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Données du Colloscope**")
            st.json(dict_donnees)
        
        with col2:
            st.write("**Légende**")
            st.json(dict_legende)
        
        st.write("**Dates des Semaines**")
        dates_str = [d.strftime("%d/%m/%Y") if d else "—" for d in dates_semaines]
        st.write(dates_str)
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")

def afficher_outils_debug(classe: str, annee_scolaire: str) -> None:
    """Affiche les outils de débogage."""
    st.subheader("🔧 Outils de Débogage")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recharger données", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache vidé !")
            st.rerun()
    
    with col2:
        if st.button("🧹 Vider tout le cache", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache complet vidé !")
            st.rerun()
    
    with col3:
        if st.button("📋 Afficher état", use_container_width=True):
            st.write("**État du session_state :**")
            st.json(st.session_state.to_dict())
    
    st.markdown("---")
    
    # Infos système
    st.write("**Informations Système**")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("Date/Heure", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    with col_info2:
        st.metric("Année Scolaire", annee_scolaire)
    
    with col_info3:
        st.metric("Classe Actuelle", classe)

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale de l'application."""
    # Détection automatique de l'année scolaire
    annee_scolaire_actuelle = detecter_annee_scolaire_actuelle()

    # Chargement des paramètres
    groupe_default, semaine_default, classe_default = charger_parametres()

    # Initialisation session_state
    if "groupe" not in st.session_state:
        st.session_state.groupe = groupe_default
    if "semaine" not in st.session_state:
        st.session_state.semaine = semaine_default
    if "classe" not in st.session_state:
        st.session_state.classe = classe_default
    if "authenticated_owner" not in st.session_state:
        st.session_state.authenticated_owner = False

    # Logo sidebar
    afficher_logo_sidebar()
    
    st.sidebar.markdown("---")

    # Déterminer les onglets
    tab_names = ["📅 Colloscope"]
    if st.session_state.get("authenticated_owner", False):
        tab_names.append("🛠️ Outils Propriétaire")

    tabs = st.tabs(tab_names)

    # ===== ONGLET COLLOSCOPE =====
    with tabs[0]:
        st.header("📅 Colloscope")
        
        # Affichage EDT EPS
        with st.expander("🏀 Afficher EDT EPS"):
            afficher_edt_eps()

        st.sidebar.subheader("⚙️ Sélection")

        # Informations de la semaine actuelle
        date_actuelle = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        _, _, dates_semaines = charger_donnees(st.session_state.classe, annee_scolaire_actuelle)
        
        semaine_actuelle_num = semaine_actuelle(dates_semaines, date_actuelle)
        semaine_auto = str(min(semaine_actuelle_num, CONFIG["max_weeks"]))

        # Affichage infos
        col_info_left, col_info_right = st.sidebar.columns(2)
        with col_info_left:
            st.metric("📅 Date", date_actuelle.strftime("%d/%m"))
        with col_info_right:
            st.metric("📍 Semaine", semaine_actuelle_num)

        st.sidebar.caption(f"Année scolaire : **{annee_scolaire_actuelle}**")

        st.sidebar.markdown("---")

        # Sélecteurs
        st.session_state.classe = st.sidebar.selectbox(
            "Classe TSI",
            options=["1", "2"],
            index=int(st.session_state.classe) - 1,
            key="classe_select"
        )

        st.session_state.groupe = st.sidebar.text_input(
            "Groupe",
            value=st.session_state.groupe,
            key="groupe_input",
            placeholder="ex: G1, G2, G10..."
        )

        semaine_index = min(int(semaine_auto) - 1, CONFIG["max_weeks"] - 1)
        st.session_state.semaine = st.sidebar.selectbox(
            "Semaine",
            options=[str(i) for i in range(1, CONFIG["max_weeks"] + 1)],
            index=semaine_index,
            key="semaine_select"
        )

        # Boutons de navigation
        col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
        
        with col_btn1:
            if st.button("◀ Précédente", use_container_width=True, key="prev_week"):
                changer_semaine(-1)
                st.rerun()
        
        with col_btn2:
            if st.button("Afficher", use_container_width=True, key="show_btn"):
                enregistrer_parametres(
                    st.session_state.groupe,
                    st.session_state.semaine,
                    st.session_state.classe
                )
                st.rerun()
        
        with col_btn3:
            if st.button("Suivante ▶", use_container_width=True, key="next_week"):
                changer_semaine(1)
                st.rerun()

        st.sidebar.info("⚠️ Vérifiez votre colloscope papier pour éviter les erreurs.")

        # Affichage du planning
        st.markdown("---")
        afficher_planning(
            st.session_state.groupe,
            st.session_state.semaine,
            st.session_state.classe,
            annee_scolaire_actuelle
        )

    # ===== ONGLET OUTILS PROPRIÉTAIRE =====
    if st.session_state.get("authenticated_owner", False):
        with tabs[1]:
            st.subheader("🛠️ Outils Propriétaire")
            
            if st.button("🚪 Déconnexion", use_container_width=True, key="logout_btn"):
                st.session_state["authenticated_owner"] = False
                st.rerun()
            
            st.markdown("---")
            
            debug_tabs = st.tabs(["📊 Dictionnaires", "🔧 Debug"])
            
            with debug_tabs[0]:
                afficher_dictionnaires(
                    st.session_state.classe,
                    annee_scolaire_actuelle
                )
            
            with debug_tabs[1]:
                afficher_outils_debug(
                    st.session_state.classe,
                    annee_scolaire_actuelle
                )

    # ===== BOUTON ACCÈS PROPRIÉTAIRE =====
    st.sidebar.markdown("---")
    
    if not st.session_state.get("authenticated_owner", False):
        if st.sidebar.button("🐞 Accès Propriétaire", use_container_width=True, key="owner_btn"):
            dialog_authentification()
    else:
        st.sidebar.success("✅ Vous êtes authentifié")

    # ===== FOOTER =====
    st.markdown(
        """
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; 
                    font-size: 11px; text-align: center; color: #666;">
            Fait par <strong>BERRY Mael</strong>, avec l'aide de SOUVELAIN Gauthier, 
            ChatGPT, Gemini et DAMBRY Paul<br/>
            <em>Version améliorée 2024</em>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
