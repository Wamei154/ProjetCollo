import os
import streamlit as st
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta


def resource_path(relative_path):
    """Return the absolute path to the resource."""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def flatten_list(nested_list):
    """Flatten a nested list."""
    return [' '.join(inner_list) for inner_list in nested_list]


@st.cache_data
def load_data(classe):
    """Load data from Excel files based on the selected class."""
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


def get_week_start_date(start_date, current_date):
    """
    Calculate the start date of the current or next week.
    If the current date is outside the interval, move to the next week.
    """
    while current_date > start_date + timedelta(days=6):  # If outside the interval
        start_date += timedelta(days=7)  # Move to the next week
    return start_date


def colo(groupe, semaine, data_dict, data_dict1):
    m = []
    try:
        if groupe not in data_dict:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")
        if semaine - 1 >= len(data_dict[groupe]) or semaine - 1 < 0:
            raise IndexError(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")
        s = data_dict[groupe][semaine - 1]
        for k in range(len(s)):
            if s[k] not in data_dict1:
                raise KeyError(f"La clé '{s[k]}' n'existe pas dans les données de légende.")
            joined_elements = flatten_list(data_dict1[s[k]])
            matiere = "Non spécifié"
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


def display_data():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    try:
        semaine = int(semaine)
        if semaine < 1 or semaine > 30:
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide entre 1 et 30.")
        return

    try:
        group_number = int(groupe[1:])
        if group_number < 1 or group_number > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide en commençant par 'G'.")
        return

    data_dict, data_dict1 = load_data(classe)
    data = colo(groupe, semaine, data_dict, data_dict1)

    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]
    st.table(df.style.hide(axis='index'))


def main():
    st.sidebar.header("Sélection")

    # Définir la date de début de la première semaine
    start_date = datetime.strptime("16/09/2024", "%d/%m/%Y")
    current_date = datetime.now()
    first_day_of_week = get_week_start_date(start_date, current_date)
    end_date = first_day_of_week + timedelta(days=6)

    st.sidebar.write(f"Premier jour de la semaine : {first_day_of_week.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"Dernier jour de la semaine : {end_date.strftime('%d/%m/%Y')}")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value="G1")
    semaine = st.sidebar.text_input("Semaine", value="1")

    if st.sidebar.button("Afficher"):
        st.session_state.groupe = groupe
        st.session_state.semaine = semaine
        st.session_state.classe = classe
        display_data()

    st.markdown(
        """
        <div style="position: fixed; bottom: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
