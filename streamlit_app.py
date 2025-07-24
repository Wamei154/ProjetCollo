import os
import streamlit as st
import requests
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime, timedelta
import base64
import re

st.set_page_config(page_title="Colloscope")

# Charger et afficher le logo en sidebar
with open("logo_prepa.png", "rb") as img_file:
    b64_data = base64.b64encode(img_file.read()).decode()

html_code = f'''<div style="text-align: center; margin-bottom: 80px;"><a href="https://sites.google.com/site/cpgetsimarcelsembat/" target="_blank"><img src="data:image/png;base64,{b64_data}" width="150"></a></div>'''
st.sidebar.markdown(html_code, unsafe_allow_html=True)

# Définir le code propriétaire (À CHANGER POUR UNE UTILISATION RÉELLE !)
CODE_PROPRIETAIRE = "debug123" 

# --- Fonctions utilitaires ---

def chemin_ressource(chemin_relatif):
    base_path = os.path.abspath(".")
    return os.path.join(base_path, chemin_relatif)

def aplatir_liste(liste_imbriquee):
    return [' '.join(sous_liste) for sous_liste in liste_imbriquee]

def extract_date(cell_str, year):
    match = re.search(r'\((\d{2}/\d{2})\)', cell_str)
    if match:
        date_str = match.group(1)
        full_date_str = f"{date_str}/{year}"
        try:
            date_obj = datetime.strptime(full_date_str, "%d/%m/%Y")
            return date_obj
        except:
            return None
    return None

def to_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

# --- Fonctions de chargement des données ---

@st.cache_data
def charger_donnees(classe, annee_scolaire=2024):
    fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
    fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')

    excel_colloscope = load_workbook(fichier_colloscope)
    excel_legende = load_workbook(fichier_legende)

    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active

    dictionnaire_donnees = {}
    dictionnaire_legende = {}

    dates_semaines = []
    for cell in feuille_colloscope[1][1:]:
        if cell.value:
            date_extrait = extract_date(str(cell.value), annee_scolaire)
            dates_semaines.append(date_extrait)
        else:
            dates_semaines.append(None)

    for ligne in feuille_colloscope.iter_rows(min_row=2, values_only=True):
        cle = ligne[0]
        valeurs = ligne[1:]
        valeurs = [v.split() if v is not None else [] for v in valeurs]
        dictionnaire_donnees[cle] = valeurs

    for ligne in feuille_legende.iter_rows(min_row=2, values_only=True):
        cle_legende = ligne[0]
        valeurs_legende = ligne[1:]
        valeurs_legende = [v.split() if v is not None else [] for v in valeurs_legende]
        dictionnaire_legende[cle_legende] = valeurs_legende

    return dictionnaire_donnees, dictionnaire_legende, dates_semaines

@st.cache_data
def obtenir_vacances(zone="C", annee="2024-2025"):
    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 500,
        "refine.zone": f"Zone {zone}",
        "refine.annee_scolaire": annee,
    }
    vacances = []
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for record in data["records"]:
            fields = record.get("fields", {})
            start_str = fields.get("start_date")
            end_str = fields.get("end_date")
            if start_str and end_str:
                try:
                    debut = datetime.fromisoformat(start_str)
                    fin = datetime.fromisoformat(end_str)
                    vacances.append((debut, fin))
                except:
                    pass

        vacances = [(start, end) for start, end in vacances if to_naive(end) < datetime(2024, 9, 16) or to_naive(start) > datetime(2024, 9, 2)]

    except Exception as e:
        st.error(f"Erreur récupération vacances : {e}")
        vacances = []

    return vacances

# --- Fonctions de logique métier ---

def semaine_actuelle(dates_semaines, date_actuelle=None):
    if date_actuelle is None:
        date_actuelle = datetime.now()
    
    current_weekday = date_actuelle.weekday()
    date_du_lundi_actuel = date_actuelle - timedelta(days=current_weekday)
    date_du_lundi_actuel = date_du_lundi_actuel.replace(hour=0, minute=0, second=0, microsecond=0)

    for i, date_semaine_excel in enumerate(dates_semaines):
        if date_semaine_excel is None:
            continue
        
        lundi_excel = date_semaine_excel.replace(hour=0, minute=0, second=0, microsecond=0)

        if lundi_excel >= date_du_lundi_actuel:
            return i + 1
    
    return len(dates_semaines)

def enregistrer_parametres(groupe, semaine, classe):
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    groupe = "G1"
    classe = "1"
    semaine = "1" 

    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                groupe = lignes[0].strip()
                semaine = lignes[1].strip()
                classe = lignes[2].strip()
    return groupe, semaine, classe

def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    tableau = []
    try:
        semaine = int(semaine)
        if groupe not in dictionnaire_donnees:
            st.error(f"Le groupe '{groupe}' n'existe pas dans les données.")
            return tableau

        if not (1 <= semaine <= len(dictionnaire_donnees[groupe])):
            st.error(f"La semaine {semaine} n'est pas valide ou dépasse le nombre de semaines disponibles pour le groupe '{groupe}'.")
            return tableau

        ligne = dictionnaire_donnees[groupe][semaine - 1]

        for k in range(len(ligne)):
            cle_legende = ligne[k]
            if cle_legende not in dictionnaire_legende:
                tableau.append([None, None, None, None, f"Clé inconnue: {cle_legende}"])
                continue 

            elements_assembles = aplatir_liste(dictionnaire_legende[cle_legende])
            
            matiere = "Non spécifié"
            if cle_legende.startswith('M'): matiere = "Mathématiques"
            elif cle_legende.startswith('A'): matiere = "Anglais"
            elif cle_legende.startswith('SI'): matiere = "Sciences de l'Ingénieur"
            elif cle_legende.startswith('F'): matiere = "Français"
            elif cle_legende.startswith('I'): matiere = "Informatique"
            elif cle_legende.startswith('P'): matiere = "Physique"

            elements_assembles.append(matiere)
            tableau.append(elements_assembles)

    except ValueError:
        st.error("Veuillez entrer une Semaine valide (nombre entier).")
    except Exception as erreur:
        st.error(f"Une erreur inattendue est survenue : {erreur}")
    return tableau

def changer_semaine(sens):
    if "semaine" in st.session_state:
        nouvelle_semaine = int(st.session_state.semaine) + sens
        if 1 <= nouvelle_semaine <= 30:
            st.session_state.semaine = nouvelle_semaine

def afficher_donnees():
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    enregistrer_parametres(groupe, semaine, classe)

    try:
        semaine_int = int(semaine)
        if not (1 <= semaine_int <= 30):
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide entre 1 et 30.")
        return

    try:
        numero_groupe = int(groupe[1:])
        if not (1 <= numero_groupe <= 20):
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide (ex: G1) entre 1 et 20.")
        return

    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(classe) 
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)

    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]

    st.table(df.style.hide(axis='index'))

# --- Fonctions d'accès propriétaire (Debug) ---

def afficher_dictionnaires_secrets(classe_selectionnee):
    st.subheader("Contenu des dictionnaires")
    try:
        dictionnaire_donnees, dictionnaire_legende, dates_semaines = charger_donnees(classe_selectionnee)
        
        st.write("### Dictionnaire de Données (`dictionnaire_donnees`)")
        st.json(dictionnaire_donnees)

        st.write("### Dictionnaire de Légende (`dictionnaire_legende`)")
        st.json(dictionnaire_legende)

        st.write("### Dates des Semaines (`dates_semaines`)")
        dates_str = [d.strftime("%d/%m/%Y") if d else "None" for d in dates_semaines]
        st.write(dates_str)

    except Exception as e:
        st.error(f"Erreur lors du chargement ou de l'affichage des dictionnaires : {e}")

def gerer_outils_debug(classe_selectionnee):
    st.subheader("Outils de débogage")
    
    if st.button("Recharger les données (Colloscope/Légende)", key="reload_data_btn"):
        st.cache_data.clear()
        st.success("Cache des données vidé. Les fichiers Excel seront relus au prochain accès.")
        st.rerun()

    if st.button("Vider tout le cache Streamlit", key="clear_all_cache_btn"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Tout le cache Streamlit a été vidé.")
        st.rerun()

    st.write("### Informations système")
    st.write(f"**Date et heure actuelle du serveur :** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    st.write("Contenu de `st.session_state`:")
    st.json(st.session_state.to_dict())

# --- NOUVEAU : Dialogue d'authentification pour le debug ---
@st.dialog("Accès Propriétaire")
def debug_dialog():
    st.write("Veuillez entrer le code secret pour accéder aux outils de débogage.")
    code_secret_input = st.text_input("Code secret", type="password", key="dialog_secret_code")

    if st.button("Valider l'accès"):
        if code_secret_input == CODE_PROPRIETAIRE:
            st.session_state["authenticated_owner"] = True
            st.success("Accès accordé !")
            st.rerun() # Rafraîchir pour afficher les outils
        else:
            st.error("Code incorrect.")
            st.session_state["authenticated_owner"] = False

# --- Fonction principale de l'application ---

def principal():
    # Bouton EDT EPS dans la sidebar
    if st.sidebar.button('EDT EPS', key="edt_eps_btn"):
        st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
        st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

    st.sidebar.header("Sélection")

    date_actuelle = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    _, _, dates_semaines_initiales = charger_donnees(classe="1") 
    
    semaines_ecoulees = semaine_actuelle(dates_semaines_initiales, date_actuelle)
    
    date_actuelle_str = date_actuelle.strftime("%d/%m")

    st.sidebar.write(f"**Date** :  {date_actuelle_str}")
    st.sidebar.write(f"**N° semaine actuelle** :  {semaines_ecoulees}")

    semaine_auto = str(min(semaines_ecoulees, 30))

    groupe_default, semaine_saved, classe_default = charger_parametres()

    semaine_default = semaine_saved if os.path.exists('config.txt') else semaine_auto

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=int(classe_default) - 1, key="classe_select")
    groupe = st.sidebar.text_input("Groupe", value=groupe_default, key="groupe_input")
    semaine = st.sidebar.selectbox("Semaine",options=[str(i) for i in range(1, 31)],index=int(semaine_default) - 1, key="semaine_select")

    cols = st.sidebar.columns(3)
    if cols[0].button("Afficher", key="afficher_btn"):
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()
    if cols[1].button("◀", key="prev_semaine_btn"):
        changer_semaine(-1)
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()
    if cols[2].button("▶", key="next_semaine_btn"):
        changer_semaine(1)
        st.sidebar.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")
        afficher_donnees()

    # --- Accès Propriétaire via Dialogue ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Accès Propriétaire", key="owner_access_btn"):
        debug_dialog() # Ouvre la boîte de dialogue

    # Afficher les outils de débogage si authentifié
    if st.session_state.get("authenticated_owner", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("Outils Propriétaire Actifs")
        if st.sidebar.button("Déconnexion", key="owner_logout_btn"):
            st.session_state["authenticated_owner"] = False
            st.rerun() # Rafraîchir pour masquer les outils

        # Onglets pour les outils de débogage
        st_debug_tabs = st.tabs(["Dictionnaires", "Outils de Debug"])

        with st_debug_tabs[0]:
            if st.button("Afficher les dictionnaires", key="show_dicts_btn"):
                afficher_dictionnaires_secrets(classe)
        
        with st_debug_tabs[1]:
            gerer_outils_debug(classe) # Correction : nom de fonction 'gerer_outils_debug'
    # --- Fin Accès Propriétaire ---


    # Pied de page (Footer)
    st.markdown(
    """
    <div style="margin-top: 30px; font-size: 10px; text-align: center; color: gray;">
        Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier, ChatGPT, Gémini et de DAMBRY Paul
    </div>
    """,
    unsafe_allow_html=True
    )

    # Sauvegarder l'état actuel dans session_state
    st.session_state.groupe = groupe
    st.session_state.semaine = semaine
    st.session_state.classe = classe

# Point d'entrée de l'application
if __name__ == "__main__":
    principal()
