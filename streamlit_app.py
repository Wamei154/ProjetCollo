import os
import streamlit as st
import requests
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta
import base64
import re

st.set_page_config(page_title="Colloscope")

with open("logo_prepa.png", "rb") as img_file:
    b64_data = base64.b64encode(img_file.read()).decode()

html_code = f'''<div style="text-align: center; margin-bottom: 80px;"><a href="https://sites.google.com/site/cpgetsimarcelsembat/" target="_blank"><img src="data:image/png;base64,{b64_data}" width="150"></a></div>'''
st.sidebar.markdown(html_code, unsafe_allow_html=True)

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
            date_obj = datetime.strptime(full_date_str, "%d/%m/%Y")
            return date_obj
        except:
            return None
    return None

@st.cache_data
def charger_donnees(classe, annee_scolaire=2024):
    fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
    fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')

    excel_colloscope = load_workbook(fichier_colloscope)
    excel_legende = load_workbook(fichier_legende)

    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active

    dictionnaire_donnees = {}
    dictionnaire_legende = {}

    dates_semaines = []
    for cell in feuille_colloscope[1][1:]:
        date_extrait = extract_date(str(cell.value), annee_scolaire)
        dates_semaines.append(date_extrait)

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

def obtenir_vacances(zone="C", annee="2024-2025"):
    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 500,
        "refine.zone": f"Zone {zone}",
        "refine.annee_scolaire": annee,
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
                # Utilise dateutil.parser pour convertir les dates ISO avec fuseau
                debut = parser.isoparse(start_str).replace(tzinfo=None)
                fin = parser.isoparse(end_str).replace(tzinfo=None)
                vacances.append((debut, fin))
        # Filtrer les vacances avant ou après la période scolaire utile
        vacances = [(start, end) for start, end in vacances if end < datetime(2024, 9, 16) or start > datetime(2024, 9, 2)]
    except Exception as e:
        st.error(f"Erreur récupération vacances : {e}")
        vacances = []
    return vacances

def calculer_semaines_ecoulees(date_debut, date_actuelle, vacances):
    semaines = 0
    current_date = date_debut
    while current_date <= date_actuelle:
        est_vacances = False
        for debut, fin in vacances:
            if debut <= current_date <= fin:
                est_vacances = True
                break
        if not est_vacances:
            semaines += 1 if current_date.weekday() == 0 else 0
        current_date += timedelta(days=1)
    return max(1, semaines)

def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    tableau = []
    try:
        if groupe not in dictionnaire_donnees:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")
        semaine = int(semaine)
        if semaine - 1 >= len(dictionnaire_donnees[groupe]) or semaine - 1 < 0:
            raise IndexError(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")
        ligne = dictionnaire_donnees[groupe][semaine - 1]
        for k in range(len(ligne)):
            if ligne[k] not in dictionnaire_legende:
                raise KeyError(f"La clé '{ligne[k]}' n'existe pas dans les données de légende.")
            elements_assembles = aplatir_liste(dictionnaire_legende[ligne[k]])
            matiere = "Non spécifié"
            if ligne[k].startswith('M'):
                matiere = "Mathématiques"
            elif ligne[k].startswith('A'):
                matiere = "Anglais"
            elif ligne[k].startswith('SI'):
                matiere = "Sciences de l'Ingénieur"
            elif ligne[k].startswith('F'):
                matiere = "Français"
            elif ligne[k].startswith('I'):
                matiere = "Informatique"
            elif ligne[k].startswith('P'):
                matiere = "Physique"
            elements_assembles.append(matiere)
            tableau.append(elements_assembles)
    except (KeyError, IndexError, Exception) as erreur:
        st.error(str(erreur))
        return tableau
    return tableau

def enregistrer_parametres(groupe, semaine, classe):
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    groupe = "G1"
    classe = "1"
    vacances = obtenir_vacances()
    semaine = str(calculer_semaines_ecoulees(datetime.strptime("16/09/2024", "%d/%m/%Y"), datetime.now(), vacances))
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                groupe = lignes[0].strip()
                semaine = lignes[1].strip()
                classe = lignes[2].strip()
    return groupe, semaine, classe

def changer_semaine(sens):
    if "semaine" in st.session_state:
        nouvelle_semaine = int(st.session_state.semaine) + sens
        if 1 <= nouvelle_semaine <= 30:
            st.session_state.semaine = nouvelle_semaine

def afficher_donnees():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe
    enregistrer_parametres(groupe, semaine, classe)
    try:
        semaine = int(semaine)
        if semaine < 1 or semaine > 30:
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide entre 1 et 30.")
        return
    try:
        numero_groupe = int(groupe[1:])
        if numero_groupe < 0 or numero_groupe > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide entre 1 et 20.")
        return
    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(classe)
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)
    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]
    st.table(df.style.hide(axis='index'))

def principal():
    if st.sidebar.button('EDT EPS'):
        st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
        st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

    st.sidebar.header("Sélection")

    date_debut = datetime.strptime("16/09/2024", "%d/%m/%Y")
    date_actuelle = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    vacances = obtenir_vacances(zone="C", annee="2024-2025")
    semaines_ecoulees = calculer_semaines_ecoulees(date_debut, date_actuelle, vacances)
    date_actuelle_str = date_actuelle.strftime("%d/%m")

    st.sidebar.write(f"**Date** :  {date_actuelle_str}")
    st.sidebar.write(f"**N° semaine actuelle** :  {semaines_ecoulees}")

    semaine_auto = str(min(semaines_ecoulees, 30))
    groupe_default, semaine_saved, classe_default = charger_parametres()
    semaine_default = semaine_saved if os.path.exists('config.txt') else semaine_auto

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=int(classe_default) - 1)
    groupe = st.sidebar.text_input("Groupe", value=groupe_default)
    semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=int(semaine_default) - 1)

    cols = st.sidebar.columns(3)
    if cols[0].button("Afficher"):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()
    if cols[1].button(":material/arrow_left:"):
        changer_semaine(-1)
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()
    if cols[2].button(":material/arrow_right:"):
        changer_semaine(1)
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()

    st.markdown("""
        <div style="position: fixed; bottom: 0; width: 100%; font-size: 10px; text-align: center;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
    """, unsafe_allow_html=True)

    st.session_state.groupe = groupe
    st.session_state.semaine = semaine
    st.session_state.classe = classe

if __name__ == "__main__":
    principal()
