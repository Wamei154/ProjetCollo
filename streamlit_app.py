import os
import streamlit as st
from openpyxl import load_workbook
import pandas as pd
import time
from datetime import datetime

def resource_path(relative_path):
    """ Retourne le chemin absolu vers la ressource """
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def flatten_list(nested_list):
    return [' '.join(inner_list) for inner_list in nested_list]


@st.cache_data
def load_data(classe):
    """ Charge les données des fichiers Excel selon la classe sélectionnée """
    colloscope_file = resource_path(f'Colloscope{classe}.xlsx')
    legende_file = resource_path(f'Legende{classe}.xlsx')

    excel_colloscope = load_workbook(colloscope_file)
    excel_legende = load_workbook(legende_file)

    sheet_colloscope = excel_colloscope.active
    sheet_legende = excel_legende.active

    data_dict = {}
    data_dict1 = {}

    for row in sheet_colloscope.iter_rows(min_row=2, values_only=True):
        key = row[0]
        values = row[1:]
        values = [v.split() if v is not None else [] for v in values]
        data_dict[key] = values

    for row in sheet_legende.iter_rows(min_row=2, values_only=True):
        key1 = row[0]
        values1 = row[1:]
        values1 = [v.split() if v is not None else [] for v in values1]
        data_dict1[key1] = values1

    return data_dict, data_dict1


def get_current_week():
    """Retourne la semaine actuelle (max 30)"""
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)


def save_settings(groupe, semaine, classe):
    with open('config.txt', 'w') as f:
        f.write(f"{groupe}\n{semaine}\n{classe}")

def load_settings():
    groupe = "G1"
    semaine = str(get_current_week())
    classe = "1"  # Classe par défaut
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) >= 3:
                groupe = lines[0].strip()
                semaine = lines[1].strip()
                classe = lines[2].strip()
    return groupe, semaine, classe


def colo(groupe, semaine, data_dict, data_dict1):
    m = []

    try:
        # Vérification de la présence du groupe dans data_dict
        if groupe not in data_dict:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")

        # Convertir 'semaine' en entier pour éviter l'erreur de type
        semaine = int(semaine)

        # Vérification que l'index de la semaine est valide
        if semaine - 1 >= len(data_dict[groupe]) or semaine - 1 < 0:
            raise IndexError(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")

        # Accès aux données de la semaine spécifiée
        s = data_dict[groupe][semaine - 1]

        # Boucle pour assembler les éléments
        for k in range(len(s)):
            # Vérification de la clé dans data_dict1
            if s[k] not in data_dict1:
                raise KeyError(f"La clé '{s[k]}' n'existe pas dans les données de légende.")

            # Assemble the row
            joined_elements = flatten_list(data_dict1[s[k]])

            # Handle specific letters to assign subjects (Matière)
            matiere = "Non spécifié"  # Default value

            if s[k].startswith('M'):
                matiere = "Mathématiques"
            elif s[k].startswith('A'):
                matiere = "Anglais"
            elif s[k].startswith('SI'):
                matiere = "Sciences de l'Ingénieur"
            elif s[k].startswith('F'):
                matiere = "Français"
            elif s[k].startswith('I'):
                matiere = "Informatique"
            elif s[k].startswith('P'):
                matiere = "Physique"
            # Add more conditions for other subjects as needed

            # Add the Matière column to the row
            joined_elements.append(matiere)
            m.append(joined_elements)

    except KeyError as e:
        st.error(str(e))
        return m

    except IndexError as e:
        st.error(str(e))
        return m

    except Exception as e:
        st.error(f"Une erreur inattendue s'est produite : {str(e)}")
        return m

    return m


def get_weeks_passed(start_date, current_date):
    """Calcule le nombre de semaines passées depuis la date de début"""
    delta = current_date - start_date
    weeks_passed = delta.days // 7
    return weeks_passed


def display_data():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    save_settings(groupe, semaine, classe)  

    try:
        semaine = int(semaine)
        if semaine < 1 or semaine > 30:
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide entre 1 et 30. Les lettres ou autres caractères ne sont pas nécessaires.")
        return

    try:
        group_number = int(groupe[1:])
        if group_number < 0 or group_number > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide entre 1 et 20 et de commencer par 'G' comme G10.")
        return

    data_dict, data_dict1 = load_data(classe)

    data = colo(groupe, semaine, data_dict, data_dict1)

    # Updated columns to include the Matière
    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for i in range(len(df))]

    st.table(df.style.hide(axis='index'))


def main():
    if st.sidebar.button('EDT EPS'):
        st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
        st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

    st.sidebar.header("Sélection")

    # Date de début de la première semaine
    start_date = datetime.strptime("16/09/2024", "%d/%m/%Y")
    current_date = datetime.now()

    # Calculer le nombre de semaines passées depuis le début de l'année
    weeks_passed = get_weeks_passed(start_date, current_date)
    #Établir la liste de toutes les dates de début de semaine
    L_dates_debut_semaines=None

    # Afficher le nombre de semaines passées dans la barre latérale
    st.sidebar.write(f"**Semaine en cours** : {weeks_passed}")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value=load_settings()[0])
    #semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=int(load_settings()[1])-1)  # Selection de la semaine avec Selectbox
    semaine = st.sidebar.selectbox("Semaine", options=[str(i)+str(L_dates_debut_semaines[i])+"à"+str(L_dates_debut_semaines[i+1]) for i in range(1, 31)], index=int(load_settings()[1])-1)  # Selection de la semaine avec Selectbox
    
    if st.sidebar.button("Télécharger le fichier EXE", 'https://drive.google.com/drive/folders/1EiyTE39U-jhlz4S8Mtun3qG04IG0_Gxn?usp=sharing'):
        st.sidebar.markdown(
            f'En Construction',
            unsafe_allow_html=True
        )

    if st.sidebar.button("Afficher", on_click=display_data):
        st.info("""Veuillez verifier quand même de temps en temps votre colloscope papier, pour verifier si il n'y a pas d'erreur""", icon="⚠️")

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
    main()
