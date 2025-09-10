import os
import streamlit as st
import requests
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta
import base64
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import io
import json
classe = "1"
print(DRIVE_FILE_IDS.get(f"Colloscope{classe}", "Clé introuvable"))

st.set_page_config(page_title="Colloscope")

# --- Logo ---
with open("logo_prepa.png", "rb") as img_file:
    b64_data = base64.b64encode(img_file.read()).decode()
html_code = f'''<div style="text-align: center; margin-bottom: 80px;">
<a href="https://sites.google.com/site/cpgetsimarcelsembat/" target="_blank">
<img src="data:image/png;base64,{b64_data}" width="150"></a></div>'''
st.sidebar.markdown(html_code, unsafe_allow_html=True)

# --- Code propriétaire ---
CODE_PROPRIETAIRE = "debug123"

# --- Google Drive ---
sa_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"]["json"])

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

credentials = service_account.Credentials.from_service_account_info(sa_info)
credentials = credentials.with_scopes(SCOPES)

# --- Initialiser le service Drive ---
service = build("drive", "v3", credentials=credentials)

DRIVE_FILE_IDS = {
    "Colloscope1.xlsx": "ID_DRIVE_COLLOSCOPE1",
    "Legende1": "ID_DRIVE_LEGENDE1",
    "Colloscope2": "ID_DRIVE_COLLOSCOPE2",
    "Legende2": "ID_DRIVE_LEGENDE2"
}

# --- Fonctions utilitaires ---
def chemin_ressource(chemin_relatif):
    base_path = os.path.abspath(".")
    return os.path.join(base_path, chemin_relatif)

def aplatir_liste(liste_imbriquee):
    return [' '.join(sous_liste) for sous_liste in liste_imbriquee]

def extract_date(cell_str, year):
    match = re.search(r'\((\d{2}/\d{2})\)', cell_str)
    if match:
        date_str = match.group(1)
        full_date_str = f"{date_str}/{year}"
        try:
            return datetime.strptime(full_date_str, "%d/%m/%Y")
        except ValueError:
            return None
    return None

def to_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def detecter_annee_scolaire_actuelle(date_actuelle=None):
    if date_actuelle is None:
        date_actuelle = datetime.now()
    annee_courante = date_actuelle.year
    mois_courant = date_actuelle.month
    if mois_courant >= 9:
        return f"{annee_courante}-{annee_courante+1}"
    else:
        return f"{annee_courante-1}-{annee_courante}"

# --- Google Drive: charger Excel ---
@st.cache_data
def charger_excel_drive(file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return load_workbook(fh)

# --- Charger données Colloscope/Légende ---
@st.cache_data
def charger_donnees(classe, annee_scolaire_str):
    annee_numerique = int(annee_scolaire_str.split('-')[0])
    excel_colloscope = charger_excel_drive(DRIVE_FILE_IDS[f'Colloscope{classe}'])
    excel_legende = charger_excel_drive(DRIVE_FILE_IDS[f'Legende{classe}'])
    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active

    dictionnaire_donnees = {}
    dictionnaire_legende = {}
    dates_semaines = []

    for cell in feuille_colloscope[1][1:]:
        if cell.value:
            dates_semaines.append(extract_date(str(cell.value), annee_numerique))
        else:
            dates_semaines.append(None)

    for ligne in feuille_colloscope.iter_rows(min_row=2, values_only=True):
        cle = ligne[0]
        valeurs = ligne[1:]
        valeurs = [v.split() if v is not None else [] for v in valeurs]
        dictionnaire_donnees[cle] = valeurs

    for ligne in feuille_legende.iter_rows(min_row=2, values_only=True):
        cle_legende = ligne[0]
        valeurs_legende = ligne[1:]
        valeurs_legende = [v.split() if v is not None else [] for v in valeurs_legende]
        dictionnaire_legende[cle_legende] = valeurs_legende

    return dictionnaire_donnees, dictionnaire_legende, dates_semaines

# --- Fonctions vacances, semaine, tableau (inchangées) ---
def obtenir_vacances(zone="C", annee_scolaire_str=None):
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
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for record in data["records"]:
            fields = record.get("fields", {})
            start_str = fields.get("start_date")
            end_str = fields.get("end_date")
            if start_str and end_str:
                try:
                    debut = datetime.fromisoformat(start_str)
                    fin = datetime.fromisoformat(end_str)
                    vacances.append((debut, fin))
                except ValueError:
                    pass
        annee_debut_num = int(annee_scolaire_str.split('-')[0])
        annee_fin_num = int(annee_scolaire_str.split('-')[1])
        periode_debut = datetime(annee_debut_num, 9, 1)
        periode_fin = datetime(annee_fin_num, 8, 31)
        vacances = [(start, end) for start, end in vacances if 
                    (to_naive(end) >= periode_debut and to_naive(start) <= periode_fin)]
    except Exception as e:
        st.error(f"Erreur récupération vacances : {e}")
        vacances = []
    return vacances

def semaine_actuelle(dates_semaines, date_actuelle=None):
    if date_actuelle is None:
        date_actuelle = datetime.now()
    current_weekday = date_actuelle.weekday()
    date_du_lundi_actuel = date_actuelle - timedelta(days=current_weekday)
    date_du_lundi_actuel = date_du_lundi_actuel.replace(hour=0, minute=0, second=0, microsecond=0)
    for i, date_semaine_excel in enumerate(dates_semaines):
        if date_semaine_excel is None:
            continue
        lundi_excel = date_semaine_excel.replace(hour=0, minute=0, second=0, microsecond=0)
        if lundi_excel >= date_du_lundi_actuel:
            return i + 1
    return len(dates_semaines)

def enregistrer_parametres(groupe, semaine, classe):
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    groupe = "G1"
    classe = "1"
    semaine = "1"
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                groupe = lignes[0].strip()
                semaine = lignes[1].strip()
                classe = lignes[2].strip()
    return groupe, semaine, classe

def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    tableau = []
    try:
        semaine = int(semaine)
        if groupe not in dictionnaire_donnees:
            st.error(f"Le groupe '{groupe}' n'existe pas dans les données.")
            return tableau
        if not (1 <= semaine <= len(dictionnaire_donnees[groupe])):
            st.error(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")
            return tableau
        ligne = dictionnaire_donnees[groupe][semaine - 1]
        for k in range(len(ligne)):
            cle_legende = ligne[k]
            if cle_legende not in dictionnaire_legende:
                tableau.append([None, None, None, None, f"Clé inconnue: {cle_legende}"])
                continue
            elements_assembles = aplatir_liste(dictionnaire_legende[cle_legende])
            matiere = "Non spécifié"
            if cle_legende.startswith('M'): matiere = "Mathématiques"
            elif cle_legende.startswith('A'): matiere = "Anglais"
            elif cle_legende.startswith('SI'): matiere = "Sciences de l'Ingénieur"
            elif cle_legende.startswith('F'): matiere = "Français"
            elif cle_legende.startswith('I'): matiere = "Informatique"
            elif cle_legende.startswith('P'): matiere = "Physique"
            elements_assembles.append(matiere)
            tableau.append(elements_assembles)
    except ValueError:
        st.error("Veuillez entrer une Semaine valide.")
    except Exception as erreur:
        st.error(f"Erreur inattendue : {erreur}")
    return tableau

def changer_semaine(sens):
    if "semaine" in st.session_state:
        nouvelle_semaine = int(st.session_state.semaine) + sens
        if 1 <= nouvelle_semaine <= 30:
            st.session_state.semaine = nouvelle_semaine

def afficher_donnees_colloscope(annee_scolaire_actuelle):
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe
    enregistrer_parametres(groupe, semaine, classe)
    try:
        semaine_int = int(semaine)
        if not (1 <= semaine_int <= 30):
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide.")
        return
    try:
        numero_groupe = int(groupe[1:])
        if not (1 <= numero_groupe <= 20):
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide (ex: G1).")
        return
    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(classe, annee_scolaire_actuelle)
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)
    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]
    st.table(df.style.hide(axis='index'))

# --- Dialogue et outils propriétaire ---
@st.dialog("Accès Propriétaire")
def debug_dialog():
    st.write("Veuillez entrer le code secret.")
    code_secret_input = st.text_input("Code secret", type="password", key="dialog_secret_code")
    if st.button("Valider l'accès"):
        if code_secret_input == CODE_PROPRIETAIRE:
            st.session_state["authenticated_owner"] = True
            st.success("Accès accordé !")
            st.rerun() 
        else:
            st.error("Code incorrect.")
            st.session_state["authenticated_owner"] = False

# --- Principal ---
def principal():
    annee_scolaire_actuelle = detecter_annee_scolaire_actuelle()
    groupe_default, semaine_saved, classe_default = charger_parametres()
    if "groupe" not in st.session_state:
        st.session_state.groupe = groupe_default
    if "semaine" not in st.session_state:
        st.session_state.semaine = semaine_saved
    if "classe" not in st.session_state:
        st.session_state.classe = classe_default

    tabs_names = ["Colloscope"]
    if st.session_state.get("authenticated_owner", False):
        tabs_names.append("Outils Propriétaire")
    main_tabs = st.tabs(tabs_names)

    # Onglet Colloscope
    with main_tabs[0]:
        st.header("Colloscope")
        if st.button('EDT EPS', key="edt_eps_btn_main"):
            st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
            st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

        st.sidebar.header("Sélection")
        _, _, dates_semaines_initiales = charger_donnees(st.session_state.classe, annee_scolaire_actuelle) 
        semaines_ecoulees = semaine_actuelle(dates_semaines_initiales)
        date_actuelle_str = datetime.now().strftime("%d/%m")
        st.sidebar.write(f"**Date** :  {date_actuelle_str}")
        st.sidebar.write(f"**N° semaine actuelle** :  {semaines_ecoulees}")
        st.sidebar.write(f"**Année scolaire** :  {annee_scolaire_actuelle}")

        semaine_auto = str(min(semaines_ecoulees, 30))
        st.session_state.classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=int(st.session_state.classe) - 1)
        st.session_state.groupe = st.sidebar.text_input("Groupe", value=st.session_state.groupe)
        semaine_index_default = int(semaine_auto) - 1
        if not (0 <= semaine_index_default < 30):
            semaine_index_default = 0
        st.session_state.semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=semaine_index_default)

        cols = st.sidebar.columns(3)
        if cols[0].button("Afficher"):
            st.sidebar.info("Veuillez vérifier votre colloscope papier.", icon="⚠️")
            afficher_donnees_colloscope(annee_scolaire_actuelle)
        if cols[1].button("◀"):
            changer_semaine(-1)
            st.sidebar.info("Veuillez vérifier votre colloscope papier.", icon="⚠️")
            afficher_donnees_colloscope(annee_scolaire_actuelle)
        if cols[2].button("▶"):
            changer_semaine(1)
            st.sidebar.info("Veuillez vérifier votre colloscope papier.", icon="⚠️")
            afficher_donnees_colloscope(annee_scolaire_actuelle)

    # Onglet Outils propriétaire
    if st.session_state.get("authenticated_owner", False):
        with main_tabs[1]:
            st.subheader("Outils Propriétaire")
            if st.button("Déconnexion"): 
                st.session_state["authenticated_owner"] = False
                st.rerun()
            st.markdown("---")
            st_debug_tabs = st.tabs(["Dictionnaires", "Outils de Debug"])
            with st_debug_tabs[0]:
                if st.button("Afficher les dictionnaires"):
                    dictionnaire_donnees, dictionnaire_legende, dates_semaines = charger_donnees(st.session_state.classe, annee_scolaire_actuelle)
                    st.write("### Données")
                    st.json(dictionnaire_donnees)
                    st.write("### Légende")
                    st.json(dictionnaire_legende)
            with st_debug_tabs[1]:
                st.write(f"**Année scolaire :** {annee_scolaire_actuelle}")
                st.write(f"Date serveur : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                st.json(st.session_state.to_dict())

    if not st.session_state.get("authenticated_owner", False):
        if st.sidebar.button("🐞"):
            debug_dialog()

    st.markdown("""
    <div style="margin-top: 30px; font-size: 10px; text-align: center; color: gray;">
    Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier, ChatGPT, Gémini et de DAMBRY Paul
    </div>
    """, unsafe_allow_html=True)

# --- Lancer l'application ---
if __name__ == "__main__":
    principal()
