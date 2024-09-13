import os
import re
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime, timedelta
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

    # Récupérer les valeurs entre parenthèses de la première ligne
    dates_row = [extract_date_from_cell(cell.value) for cell in sheet_colloscope[1]]
    print(f"Dates extraites de la première ligne : {dates_row}")

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


def extract_date_from_cell(cell_value):
    """Extract the date from a cell value if it's in parentheses."""
    if isinstance(cell_value, str):
        match = re.search(r'\((\d{2}/\d{2})\)', cell_value)
        if match:
            return match.group(1)
    return None


def get_current_date():
    """Get the current date in format %d/%m and add 3 days."""
    timezone = pytz.timezone('Europe/Paris')
    current_date = datetime.now(timezone)
    new_date = current_date + timedelta(days=3)
    return new_date.strftime("%d/%m")


def load_last_updated_date():
    """Load the last updated date from a file."""
    if os.path.exists('last_updated.txt'):
        with open('last_updated.txt', 'r') as f:
            return f.read().strip()
    return None


def save_current_date(date):
    """Save the current date to a file."""
    with open('last_updated.txt', 'w') as f:
        f.write(date)


def compare_dates_with_columns(dates_row, current_date):
    """Compare the dates from the first row with the current date."""
    for idx, date in enumerate(dates_row[1:], start=1):  # Ignorer la colonne 0 (index)
        if date and date == current_date:
            return idx + 1  # Retourner le numéro de colonne correspondant (B = 2, C = 3, etc.)
    return None


def colo(groupe, semaine, data_dict, data_dict1, matching_column):
    m = []

    try:
        # Vérification de la présence du groupe dans data_dict
        if groupe not in data_dict:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")

        # Vérification que l'index de la semaine est valide
        if semaine - 1 >= len(data_dict[groupe]) or semaine - 1 < 0:
            raise IndexError(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")

        # Accès aux données de la semaine spécifiée
        s = data_dict[groupe][semaine - 1]

        # Si une colonne correspond à la date actuelle, utiliser cette colonne
        if matching_column:
            s = data_dict[groupe][matching_column - 1]

        # Boucle pour assembler les éléments
        for k in range(len(s)):
            # Vérification de la clé dans data_dict1
            if s[k] not in data_dict1:
                raise KeyError(f"La clé '{s[k]}' n'existe pas dans les données de légende.")

            joined_elements = flatten_list(data_dict1[s[k]])
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


def get_current_week():
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)


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

    # Obtenir la date actuelle avec 3 jours ajoutés
    current_date = get_current_date()
    st.write(f"Date actuelle (avec 3 jours ajoutés) : {current_date}")

    # Charger la dernière date mise à jour
    last_updated_date = load_last_updated_date()
    st.write(f"Date de la dernière mise à jour : {last_updated_date}")

    # Mettre à jour si la date a changé
    if last_updated_date != current_date:
        save_current_date(current_date)
        st.write(f"La date actuelle a été mise à jour : {current_date}")
    else:
        st.write(f"La date actuelle est : {current_date}")

    # Comparer les dates de la première ligne avec la date actuelle
    matching_column = compare_dates_with_columns(dates_row, current_date)
    st.write(f"Colonne correspondant à la date actuelle : {matching_column}")

    if matching_column:
        data = colo(groupe, semaine, data_dict, data_dict1, matching_column)
    else:
        data = colo(groupe, semaine, data_dict, data_dict1, None)

    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle"])
    df.index = ['' for i in range(len(df))]

    st.table(df.style.hide(axis='index'))
    st.write(data_row[1])


def main():
    st.sidebar.header("Sélection")

    # Charger les paramètres et vérifier qu'ils sont valides
    settings = load_settings()
    if not all(isinstance(x, str) for x in settings):
        st.error("Les paramètres chargés depuis le fichier de configuration sont invalides.")
        return

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value=settings[0])
    semaine = st.sidebar.text_input("Semaine", value=settings[1])

    if st.sidebar.button("Télécharger le fichier EXE", 'https://drive.google.com/drive/folders/1EiyTE39U-jhlz4S8Mtun3qG04IG0_Gxn?usp=sharing'):
        st.sidebar.markdown(
            'En Construction',
            unsafe_allow_html=True
        )

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
