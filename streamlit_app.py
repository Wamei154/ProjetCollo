import os
import streamlit as st
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime

def chemin_ressource(chemin_relatif):
    base_path = os.path.abspath(".")
    return os.path.join(base_path, chemin_relatif)

def aplatir_liste(liste_imbriquee):
    return [' '.join(sous_liste) for sous_liste in liste_imbriquee]

@st.cache_data
def charger_donnees(classe):
    fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
    fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')
    
    excel_colloscope = load_workbook(fichier_colloscope)
    excel_legende = load_workbook(fichier_legende)
    
    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active
    
    dictionnaire_donnees = {}
    dictionnaire_legende = {}
    
    for ligne in feuille_colloscope.iter_rows(min_row=2, values_only=True):
        dictionnaire_donnees[ligne[0]] = [v.split() if v is not None else [] for v in ligne[1:]]
    
    for ligne in feuille_legende.iter_rows(min_row=2, values_only=True):
        dictionnaire_legende[ligne[0]] = [v.split() if v is not None else [] for v in ligne[1:]]
    
    return dictionnaire_donnees, dictionnaire_legende

def obtenir_semaine_actuelle():
    return min(datetime.now().isocalendar()[1], 30)

def enregistrer_parametres(groupe, semaine, classe):
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                return lignes[0].strip(), lignes[1].strip(), lignes[2].strip()
    return "G1", str(obtenir_semaine_actuelle()), "1"

def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    tableau = []
    try:
        if groupe not in dictionnaire_donnees:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")
        semaine = int(semaine)
        ligne = dictionnaire_donnees[groupe][semaine - 1]
        for k in range(len(ligne)):
            if ligne[k] not in dictionnaire_legende:
                raise KeyError(f"La clé '{ligne[k]}' n'existe pas dans les données de légende.")
            elements_assembles = aplatir_liste(dictionnaire_legende[ligne[k]])
            matiere = "Non spécifié"
            if ligne[k].startswith('M'): matiere = "Mathématiques"
            elif ligne[k].startswith('A'): matiere = "Anglais"
            elif ligne[k].startswith('SI'): matiere = "Sciences de l'Ingénieur"
            elif ligne[k].startswith('F'): matiere = "Français"
            elif ligne[k].startswith('I'): matiere = "Informatique"
            elif ligne[k].startswith('P'): matiere = "Physique"
            elements_assembles.append(matiere)
            tableau.append(elements_assembles)
    except Exception as erreur:
        st.error(f"Erreur : {str(erreur)}")
    return tableau

def changer_semaine(sens):
    if "semaine" in st.session_state:
        nouvelle_semaine = int(st.session_state.semaine) + sens
        if 1 <= nouvelle_semaine <= 30:
            st.session_state.semaine = str(nouvelle_semaine)

def afficher_donnees():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe
    enregistrer_parametres(groupe, semaine, classe)
    dictionnaire_donnees, dictionnaire_legende = charger_donnees(classe)
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)
    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]
    st.table(df.style.hide(axis='index'))

def principal():
    if "semaine" not in st.session_state:
        st.session_state.semaine = charger_parametres()[1]
    if "groupe" not in st.session_state:
        st.session_state.groupe = charger_parametres()[0]
    if "classe" not in st.session_state:
        st.session_state.classe = charger_parametres()[2]
    
    st.sidebar.header("Sélection")
    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value=st.session_state.groupe)
    semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=int(st.session_state.semaine) - 1)
    
    cols = st.sidebar.columns(3)
    if cols[0].button("⬅", on_click=changer_semaine, args=(-1,)):
        afficher_donnees()
    if cols[1].button("Afficher", on_click=afficher_donnees):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
    if cols[2].button("➡", on_click=changer_semaine, args=(1,)):
        afficher_donnees()
    
    st.session_state.groupe = groupe
    st.session_state.semaine = semaine
    st.session_state.classe = classe
    
    st.markdown("""
        <div style="position: fixed ; center: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    principal()
