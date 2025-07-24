import os
import streamlit as st
import requests
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta
import base64

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

@st.cache_data
def charger_donnees(classe):
    fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
    fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')

    excel_colloscope = load_workbook(fichier_colloscope)
    excel_legende = load_workbook(fichier_legende)

    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active

    dictionnaire_donnees = {}
    dictionnaire_legende = {}

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

    return dictionnaire_donnees, dictionnaire_legende

@st.cache_data
def obtenir_vacances(zone="C", annee="2024-2025"):
    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 100,
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
                try:
                    debut = datetime.fromisoformat(start_str)
                    fin = datetime.fromisoformat(end_str)
                    vacances.append((debut, fin))
                except:
                    pass
    except Exception as e:
        print("Erreur récupération vacances :", e)
        vacances = []

    return vacances

def to_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def calculer_semaines_ecoulees(date_debut, date_actuelle, vacances):
    date_fin_annee = datetime(2025, 7, 4)

    vacances_valides = []
    for start, end in vacances:
        if isinstance(start, datetime) and isinstance(end, datetime):
            vacances_valides.append((to_naive(start), to_naive(end)))

    current = to_naive(date_debut)
    date_actuelle_naive = to_naive(date_actuelle.replace(hour=0, minute=0, second=0, microsecond=0))

    # On ne compte pas au-delà de la fin d’année scolaire
    date_limite = min(date_actuelle_naive, date_fin_annee)

    semaines_utiles = 0
    lundis_info = []

    while current <= date_limite:
        if current.weekday() == 0:  # Lundi
            in_vacances = any(start <= current <= end for start, end in vacances_valides)
            lundis_info.append((current.strftime("%d/%m/%Y"), "vacances" if in_vacances else "semaine utile"))
            if not in_vacances:
                semaines_utiles += 1
        current += timedelta(days=1)

    st.write("### Lundis analysés :")
    for date_str, statut in lundis_info:
        st.write(f"- {date_str} : {statut}")

    return semaines_utiles


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

    dictionnaire_donnees, dictionnaire_legende = charger_donnees(classe)
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
    date_actuelle = datetime.now()
    vacances = obtenir_vacances(zone="C", annee="2024-2025")
    date_actuelle = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    semaines_ecoulees = calculer_semaines_ecoulees(date_debut, date_actuelle, vacances)
    date_actuelle_str = date_actuelle.strftime("%d/%m")

    st.sidebar.write(f"**Date** :  {date_actuelle_str}")
    st.sidebar.write(f"**N° semaine acutelle** :  {semaine_default}")

    # Calcul de la semaine actuelle
    semaine_auto = str(min(semaines_ecoulees, 30))  # limite à 30 max

    # Charger les paramètres utilisateur s'ils existent
    groupe_default, semaine_saved, classe_default = charger_parametres()

    # Si l'utilisateur n'a pas modifié la semaine, on prend celle auto
    semaine_default = semaine_saved if os.path.exists('config.txt') else semaine_auto

    # Interface utilisateur
    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=int(classe_default) - 1)
    groupe = st.sidebar.text_input("Groupe", value=groupe_default)
    semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=int(semaine_default) - 1)

    cols = st.sidebar.columns(3)
    if cols[0].button("Afficher", on_click=afficher_donnees):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
    if cols[1].button(":material/arrow_left:", on_click=lambda: changer_semaine(-1)):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()
    if cols[2].button(":material/arrow_right:", on_click=lambda: changer_semaine(1)):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()

    st.markdown(
        """
        <div style="position: fixed ; center: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.groupe = groupe
    st.session_state.semaine = semaine
    st.session_state.classe = classe

if __name__ == "__main__":
    principal()
