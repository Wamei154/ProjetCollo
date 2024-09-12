import os
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime
import pandas as pd
import io

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
def load_data(classe):
    """ Load data from Excel files based on the selected class """
    colloscope_file = resource_path(f'Colloscope{classe}.xlsx')
    legende_file = resource_path(f'Legende{classe}.xlsx')

    try:
        excel_colloscope = load_workbook(colloscope_file)
        excel_legende = load_workbook(legende_file)
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return {}, {}

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

# Function to get the current week number
def get_current_week():
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)

# Save and load settings
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

# Function to display data
def colo(groupe, semaine, data_dict, data_dict1):
    m = []
    s = data_dict[groupe][semaine - 1]
    for k in range(len(s)):
        joined_elements = flatten_list(data_dict1[s[k]])
        m.append(joined_elements)
    return m

# Function to create an Excel file from data
def create_excel_file(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    output.seek(0)
    return output

# Display data in Streamlit
def display_data():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    save_settings(groupe, semaine, classe)  # Save the selected group, week, and class

    semaine = int(semaine)
    if semaine < 1 or semaine > 30:
        semaine = st.session_state.semaine

    try:
        group_number = int(groupe[1:])
        if group_number > 100:
            groupe = 'G100'
    except ValueError:
        groupe = 'G10'

    data_dict, data_dict1 = load_data(classe)

    if groupe not in data_dict:
        groupe = 'G10'

    data = colo(groupe, semaine, data_dict, data_dict1)

    # Create DataFrame with custom column headers
    df = pd.DataFrame(data, columns=["Professeur", "Jour", "Heure", "Salle"])
    df.index = ['' for i in range(len(df))]

    # Hide the index of the DataFrame
    st.table(df.style.hide(axis='index'))

    # Create and display download button for Excel file
    excel_file = create_excel_file(df)
    st.download_button(
        label="Télécharger le fichier Excel",
        data=excel_file,
        file_name=f"Data_{groupe}_{semaine}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Display button to redirect to Google Drive
    drive_link = "https://drive.google.com/drive/folders/1EiyTE39U-jhlz4S8Mtun3qG04IG0_Gxn?usp=sharing"  # Replace with your file's ID
    st.markdown(
        f'<a href="{drive_link}" target="_blank" class="btn">Le fichier EXE</a>',
        unsafe_allow_html=True
    )

# Main function
def main():
    st.sidebar.header("Paramètres")

    # Adding a class selector
    classe = st.sidebar.selectbox("Classe", options=["TSI 1", "TSI 2"], index=0)

    groupe = st.sidebar.text_input("Groupe", value=load_settings()[0])
    semaine = st.sidebar.text_input("Semaine", value=load_settings()[1])

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
