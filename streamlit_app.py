import os
import sys
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime

# Function to get the resource path
def resource_path(relative_path):
    """Returns the absolute path to the file, using sys._MEIPASS if the application is packaged."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function to flatten nested lists
def flatten_list(nested_list):
    """Flattens a list of lists into a list of strings."""
    return [' '.join(inner_list) for inner_list in nested_list]

# Function to get data to display
def colo(groupe, semaine, data_dict, data_dict1):
    """Function to get the data to display in the interface."""
    m = []
    s = data_dict[groupe][semaine - 1]
    for k in range(len(s)):
        joined_elements = flatten_list(data_dict1[s[k]])
        m.append(joined_elements)
    return m

# Function to load data from Excel files
@st.cache
def load_data():
    """Loads data from Excel files."""
    excel_colloscope = load_workbook(resource_path('Colloscope.xlsx'))
    excel_legende = load_workbook(resource_path('Legende.xlsx'))

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

# Function to get the current week
def get_current_week():
    """Returns the current week number."""
    now = datetime.now()
    current_week = now.isocalendar()[1]
    return min(current_week, 30)

# Function to save settings
def save_settings(groupe, semaine):
    """Saves the selected group and week to a config file."""
    with open('config.txt', 'w') as f:
        f.write(f"{groupe}\n{semaine}")

# Function to load settings
def load_settings():
    """Loads the previously selected group and week from a config file."""
    groupe = "G10"
    semaine = str(get_current_week())
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                groupe = lines[0].strip()
                semaine = lines[1].strip()
    return groupe, semaine

# Load settings
groupe_default, semaine_default = load_settings()

# Initialize click counter
if 'click_count' not in st.session_state:
    st.session_state.click_count = 0

# Streamlit app layout
st.title("Colle TSI")

groupe = st.text_input("Groupe:", value=groupe_default)
semaine = st.text_input("Semaine:", value=semaine_default)

if st.button("Afficher"):
    st.session_state.click_count += 1
    save_settings(groupe, semaine)  # Save selected group and week
    
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
    
    # Display data in a table
    st.table(data)
    
    st.write("Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier")
    
    if st.session_state.click_count == 50:
        image_path = resource_path('IMG_20240604_085232.jpg')
        st.image(image_path, caption='Special Image', use_column_width=True)

