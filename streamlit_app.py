import os
import streamlit as st
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta


def resource_path(relative_path):
    """Retourne le chemin absolu vers une ressource."""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def flatten_list(nested_list):
    return [' '.join(inner_list) for inner_list in nested_list]


@st.cache_data
def load_data(classe):
    """Charge les données des fichiers Excel selon la classe sélectionnée."""
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


def get_week_dates(start_date, current_date):
    """
    Calcule les dates de début de la semaine actuelle et de la semaine suivante.
    :param start_date: Date de début de la première semaine (datetime).
    :param current_date: Date actuelle (datetime).
    :return: Tuple contenant les dates de début des semaines actuelle et suivante.
    """
    # Trouver le début de la semaine actuelle
    while current_date > start_date + timedelta(days=6):  # Si hors intervalle de la semaine
        start_date += timedelta(days=7)
    # Calculer la semaine suivante
    next_week_start = start_date + timedelta(days=7)
    return start_date, next_week_start


def save_settings(groupe, semaine, classe):
    """Sauvegarde les paramètres sélectionnés dans un fichier de configuration."""
    with open('config.txt', 'w') as f:
        f.write(f"{groupe}\n{semaine}\n{classe}")


def load_settings():
    """Charge les paramètres sauvegardés à partir du fichier de configuration."""
    groupe = "G10"
    semaine = "1"
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
    """Construit les données à afficher pour le colloscope."""
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

    save_settings(groupe, semaine, classe)

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
        if group_number < 0 or group_number > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide et commencer par 'G'.")
        return

    data_dict, data_dict1 = load_data(classe)

    data = colo(groupe, semaine, data_dict, data_dict1)

    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for i in range(len(df))]

    st.table(df.style.hide(axis='index'))


def main():
    st.sidebar.header("Sélection")

    # Date de début de la première semaine
    start_date = datetime.strptime("16/09/2024", "%d/%m/%Y")
    current_date = datetime.now()

    # Calculer les semaines actuelle et suivante
    current_week_start, next_week_start = get_week_dates(start_date, current_date)

    # Formater les dates des semaines
    current_week_str = current_week_start.strftime("%d/%m")
    next_week_str = next_week_start.strftime("%d/%m")

    # Afficher les informations sur les semaines
    st.sidebar.write(f"**Semaine actuelle** : {current_week_str}")
    st.sidebar.write(f"**Semaine suivante** : {next_week_str}")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value="G1")
    semaine = st.sidebar.text_input("Semaine", value="1")

    if st.sidebar.button("Afficher"):
        st.session_state.groupe = groupe
        st.session_state.semaine = semaine
        st.session_state.classe = classe
        display_data()

    if st.sidebar.button("Afficher", on_click=display_data):
        st.info("""Veuillez verifier quand même de temps en temps votre colloscope papier, pour verifier si il n'y a pas d'erreur""",icon="⚠️")
    st.markdown(
        """
        <div style="position: fixed ; center: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
