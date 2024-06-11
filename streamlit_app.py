import os
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime
from PIL import Image
import pandas as pd

# Function to get the resource path
def resource_path(relative_path):
    """ Return the absolute path to the resource """
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Flatten a nested list
def flatten_list(nested_list):
    return [' '.join(inner_list) for inner_list in nested_list]

# Function to load data
@st.cache_data
def load_data():
    """ Load data from Excel files """
    colloscope_file = resource_path('Colloscope.xlsx')
    legende_file = resource_path('Legende.xlsx')

    excel_colloscope = load_workbook(colloscope_file)
    excel_legende = load_workbook(legende_file)

    sheet_colloscope = excel_colloscope.active
    sheet_legende = excel_legende.active

    data_dict = {}
    data_dict1 = {}

    for row in sheet_colloscope.iter_rows(min_row=2, values_only=True):
        key = row[0]
        values = row[1:]
        values = [v.split() for v in values]
        data_dict[key] = values

    for row in sheet_legende.iter_rows(min_row=1, values_only=True):
        key1 = row[0]
        values1 = row[1:]
        values1 = [v.split() for v in values1]
        data_dict1[key1] = values1

    return data_dict, data_dict1

# Function to get the current week number
def get_current_week():
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)

# Save and load settings
def save_settings(groupe, semaine):
    with open('config.txt', 'w') as f:
        f.write(f"{groupe}\n{semaine}")

def load_settings():
    groupe = "G10"
    semaine = str(get_current_week())
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                groupe = lines[0].strip()
                semaine = lines[1].strip()
    return groupe, semaine

# Function to display data
def colo(groupe, semaine, data_dict, data_dict1):
    m = []
    s = data_dict[groupe][semaine - 1]
    for k in range(len(s)):
        joined_elements = flatten_list(data_dict1[s[k]])
        m.append(joined_elements)
    return m

# Display data in Streamlit
def display_data():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine

    save_settings(groupe, semaine)  # Save the selected group and week

    semaine = int(semaine)
    if semaine < 1 or semaine > 30:
        semaine = get_current_week()

    try:
        group_number = int(groupe[1:])
        if group_number > 100:
            groupe = 'G100'
    except ValueError:
        groupe = 'G10'

    data_dict, data_dict1 = load_data()

    if groupe not in data_dict:
        groupe = 'G10'

    data = colo(groupe, semaine, data_dict, data_dict1)

    # Create DataFrame with custom column headers
    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle"])

    # Hide the index of the DataFrame
    st.table(df.style.hide(axis='index'))
    
    # Display the authorship text at the bottom
    st.write("Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier")
    
# Main function
def main():
    st.title("")

    st.sidebar.header("Paramètres")
    groupe = st.sidebar.text_input("Groupe", value=load_settings()[0])
    semaine = st.sidebar.text_input("Semaine", value=load_settings()[1])

    st.sidebar.button("Afficher", on_click=display_data)

    st.session_state.groupe = groupe
    st.session_state.semaine = semaine

if __name__ == "__main__":
    main()
