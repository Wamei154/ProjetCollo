import os
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime
import pandas as pd


def resource_path(relative_path):
    """ Return the absolute path to the resource """
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def flatten_list(nested_list):
    return [' '.join(inner_list) for inner_list in nested_list]


@st.cache_data
def load_data(classe):
    """ Load data from Excel files based on the selected class """
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
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)


def save_settings(groupe, semaine, classe):
    with open('config.txt', 'w') as f:
        f.write(f"{groupe}\n{semaine}\n{classe}")

def load_settings():
    groupe = "G10"
    semaine = str(get_current_week())
    classe = "1"  # Default class
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
    s = data_dict[groupe][semaine - 1]
    for k in range(len(s)):
        joined_elements = flatten_list(data_dict1[s[k]])
        m.append(joined_elements)
    return m


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
        st.error("Veuillez entrer un nombre valide entre 1 et 30. Les lettres ou autres caractères ne sont pas autorisés.")
        return

    try:
        group_number = int(groupe[1:])
        if group_number < 0 or group_number > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide entre 1 et 20. Les lettres ou autres caractères ne sont pas autorisés.")
        return

    data_dict, data_dict1 = load_data(classe)

    data = colo(groupe, semaine, data_dict, data_dict1)

   
    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle"])
    df.index = ['' for i in range(len(df))]

   
    st.table(df.style.hide(axis='index'))
   
# Main function
def main():
    st.sidebar.header("Paramètres")

    
    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)

    groupe = st.sidebar.text_input("Groupe", value=load_settings()[0])
    semaine = st.sidebar.text_input("Semaine", value=load_settings()[1])


    st.sidebar.link_button("Télécharger le fichier EXE", 'https://drive.google.com/drive/folders/1EiyTE39U-jhlz4S8Mtun3qG04IG0_Gxn?usp=sharing' )


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
    st.session_state.classe = classe  # Store the class in session state

if __name__ == "__main__":
    main()
