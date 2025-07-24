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

@st.cache_data
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

def to_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

# NOUVELLE FONCTION AJOUTÉE
def calculer_semaines_ecoulees(date_debut, date_actuelle, vacances):
    """Calcule le nombre de semaines scolaires écoulées."""
    if date_actuelle < date_debut:
        return 1
    
    semaines_comptees = 0
    jour_courant = date_debut

    while jour_courant <= date_actuelle:
        est_en_vacances = False
        for debut_vac, fin_vac in vacances:
            # On vérifie si le début de la semaine est pendant des vacances
            if to_naive(debut_vac) <= jour_courant < to_naive(fin_vac):
                est_en_vacances = True
                break
        
        if not est_en_vacances:
            semaines_comptees += 1
        
        jour_courant += timedelta(days=7)
        
    return max(1, semaines_comptees)

# FONCTION MODIFIÉE
@st.cache_data
def obtenir_vacances(zone="C", annee="2024-2025"):
    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 50,
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
                    # On convertit immédiatement en "naive" pour éviter les erreurs
                    vacances.append((to_naive(debut), to_naive(fin)))
                except:
                    pass

        # Le filtrage fonctionne maintenant car toutes les dates sont "naives"
        vacances = [(start, end) for start, end in vacances if end < datetime(2025, 9, 1) and start > datetime(2024, 9, 1)]

    except Exception as e:
        st.error(f"Erreur récupération vacances : {e}")
        vacances = []

    return vacances


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
        valeurs = [v.split() if v is not None else [] for v in ligne[1:]]
        dictionnaire_donnees[cle] = valeurs

    for ligne in feuille_legende.iter_rows(min_row=2, values_only=True):
        cle_legende = ligne[0]
        valeurs_legende = [v.split() if v is not None else [] for v in ligne[1:]]
        dictionnaire_legende[cle_legende] = valeurs_legende

    return dictionnaire_donnees, dictionnaire_legende, dates_semaines

def semaine_actuelle(dates_semaines, date_actuelle=None):
    if date_actuelle is None:
        date_actuelle = datetime.now()
    for i, date_semaine in enumerate(dates_semaines):
        if date_semaine is None:
            continue
        if date_semaine > date_actuelle:
            return max(i, 1)
    return len(dates_semaines)

def enregistrer_parametres(groupe, semaine, classe):
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    groupe = "G1"
    classe = "1"
    semaine = "1" # Valeur par défaut de base
    
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                groupe = lignes[0].strip()
                semaine = lignes[1].strip()
                classe = lignes[2].strip()
    else:
        # Si le fichier de config n'existe pas, on calcule la semaine actuelle
        vacances = obtenir_vacances()
        date_debut_annee = datetime.strptime("02/09/2024", "%d/%m/%Y")
        semaine = str(calculer_semaines_ecoulees(date_debut_annee, datetime.now(), vacances))

    return groupe, semaine, classe

def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    tableau = []
    try:
        if groupe not in dictionnaire_donnees:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")

        semaine_idx = int(semaine) - 1

        if semaine_idx >= len(dictionnaire_donnees[groupe]) or semaine_idx < 0:
            return [] # Retourne un tableau vide si la semaine n'a pas de khôlle

        ligne = dictionnaire_donnees[groupe][semaine_idx]
        
        if not ligne: # Si la liste est vide pour cette semaine
            return []

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

    except (KeyError, IndexError) as erreur:
        st.warning(f"Pas de khôlle programmée pour le groupe {groupe} en semaine {semaine}.")
        return []
    except Exception as e:
        st.error(f"Une erreur inattendue est survenue : {e}")
        return []

    return tableau

def afficher_donnees():
    if 'groupe' not in st.session_state or 'semaine' not in st.session_state or 'classe' not in st.session_state:
        st.warning("Veuillez sélectionner une classe, un groupe et une semaine.")
        return

    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    enregistrer_parametres(groupe, semaine, classe)

    try:
        semaine_int = int(semaine)
        if not 1 <= semaine_int <= 36:
            st.error("La Semaine doit être entre 1 et 36.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide (un nombre).")
        return

    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(classe)
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)

    if donnees:
        df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
        st.table(df.style.hide(axis='index'))
    else:
        st.info(f"Pas de khôlle programmée pour le groupe {groupe} en semaine {semaine}.")
    
    st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")


def principal():
    st.title("Colloscope TSI")

    if st.sidebar.button('EDT EPS'):
        st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
        st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

    st.sidebar.header("Sélection")

    # Initialisation de session_state si les clés n'existent pas
    if 'groupe' not in st.session_state or 'semaine' not in st.session_state or 'classe' not in st.session_state:
        groupe_saved, semaine_saved, classe_saved = charger_parametres()
        st.session_state.groupe = groupe_saved
        st.session_state.semaine = semaine_saved
        st.session_state.classe = classe_saved

    date_actuelle = datetime.now()
    vacances = obtenir_vacances(zone="C", annee="2024-2025")
    date_debut_annee = datetime.strptime("02/09/2024", "%d/%m/%Y") # Rentrée scolaire
    semaines_ecoulees = calculer_semaines_ecoulees(date_debut_annee, date_actuelle, vacances)

    st.sidebar.write(f"**Date** : {date_actuelle.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"**N° semaine scolaire** : {semaines_ecoulees}")

    # Interface utilisateur
    def update_params():
        st.session_state.classe = st.session_state['classe_select']
        st.session_state.groupe = st.session_state['groupe_input']
        st.session_state.semaine = st.session_state['semaine_select']
        afficher_donnees()
    
    def change_week(direction):
        current_week = int(st.session_state.semaine)
        new_week = current_week + direction
        if 1 <= new_week <= 36:
            st.session_state.semaine = str(new_week)
        afficher_donnees()

    classe_options = ["1", "2"]
    classe_index = classe_options.index(st.session_state.classe) if st.session_state.classe in classe_options else 0
    st.sidebar.selectbox("TSI", options=classe_options, index=classe_index, key='classe_select')

    st.sidebar.text_input("Groupe", value=st.session_state.groupe, key='groupe_input')

    semaine_options = [str(i) for i in range(1, 37)]
    semaine_index = semaine_options.index(st.session_state.semaine) if st.session_state.semaine in semaine_options else semaines_ecoulees - 1
    st.sidebar.selectbox("Semaine", options=semaine_options, index=semaine_index, key='semaine_select')

    cols = st.sidebar.columns([2,1,1])
    cols[0].button("Afficher", on_click=update_params, use_container_width=True)
    cols[1].button("◀", on_click=change_week, args=(-1,), use_container_width=True)
    cols[2].button("▶", on_click=change_week, args=(1,), use_container_width=True)

    st.markdown(
        """
        <div style="position: fixed; bottom: 10px; left: 0; width: 100%; font-size: 12px; text-align: center;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Affichage initial
    afficher_donnees()


if __name__ == "__main__":
    principal()
