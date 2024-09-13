import os
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime
import pandas as pd
import pytz


def resource_path(relative_path):
    """Return the absolute path to the resource."""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def flatten_list(nested_list):
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

    # Récupérer la première ligne des dates
    dates_row = [cell.value for cell in sheet_colloscope[1]]

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

    return data_dict, data_dict1, dates_row


def get_current_date():
    """Get the current date in format %d/%m."""
    timezone = pytz.timezone('Europe/Paris')
    return datetime.now(timezone).strftime("%d/%m")


def compare_dates_with_columns(dates_row, current_date):
    """Compare the dates from the first row with the current date."""
    for idx, date in enumerate(dates_row[1:], start=1):  # Ignorer la colonne 0 (index)
        if date:
            # Extraire la date entre parenthèses, si présente
            extracted_date = date[date.find("(")+1:date.find(")")] if '(' in date and ')' in date else date
            if extracted_date == current_date:
                return idx + 1  # Retourner le numéro de colonne correspondant (B = 2, C = 3, etc.)
    return None


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

    data_dict, data_dict1, dates_row = load_data(classe)

    # Obtenir la date actuelle
    current_date = get_current_date()

    # Comparer les dates de la première ligne avec la date actuelle
    matching_column = compare_dates_with_columns(dates_row, current_date)

    if matching_column:
        st.write(f"La date actuelle correspond à la colonne : {matching_column}")
    else:
        st.write("Aucune date ne correspond à la date actuelle.")

    data = colo(groupe, semaine, data_dict, data_dict1)

    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle"])
    df.index = ['' for i in range(len(df))]

    st.table(df.style.hide(axis='index'))


def main():
    st.sidebar.header("Sélection")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value=load_settings()[0])
    semaine = st.sidebar.text_input("Semaine", value=load_settings()[1])

    if st.sidebar.button("Télécharger le fichier EXE", 'https://drive.google.com/drive/folders/1EiyTE39U-jhlz4S8Mtun3qG04IG0_Gxn?usp=sharing'):
        st.sidebar.markdown("En Construction", unsafe_allow_html=True)

    st.sidebar.button("Afficher", on_click=display_data)

    st.sidebar.markdown(
        """
        <div style="position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 10px;">
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
