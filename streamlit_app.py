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
    """Extrait la date d'une chaîne de cellule et l'associe à l'année donnée."""
    match = re.search(r'\((\d{2}/\d{2})\)', cell_str)
    if match:
        date_str = match.group(1)
        full_date_str = f"{date_str}/{year}"
        try:
            date_obj = datetime.strptime(full_date_str, "%d/%m/%Y")
            return date_obj
        except ValueError:
            return None
    return None

def to_naive(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def detecter_annee_scolaire_actuelle(date_actuelle=None):
    """
    Détecte l'année scolaire actuelle au format "YYYY-YYYY".
    Une année scolaire commence en septembre.
    """
    if date_actuelle is None:
        date_actuelle = datetime.now()

    annee_courante = date_actuelle.year
    mois_courant = date_actuelle.month

    if mois_courant >= 9: # Si on est en Septembre ou plus tard, l'année scolaire commence cette année
        annee_debut = annee_courante
        annee_fin = annee_courante + 1
    else: # Si on est avant Septembre, l'année scolaire a commencé l'année précédente
        annee_debut = annee_courante - 1
        annee_fin = annee_courante
    
    return f"{annee_debut}-{annee_fin}"


# --- Fonctions de chargement des données ---

@st.cache_data
def charger_donnees(classe, annee_scolaire_str):
    """
    Charge les données du colloscope et de la légende pour une classe et une année scolaire données.
    annee_scolaire_str est au format "YYYY-YYYY" (ex: "2024-2025").
    """
    # Extraire l'année de début pour extract_date (ex: 2024 de "2024-2025")
    annee_numerique = int(annee_scolaire_str.split('-')[0])

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
            date_extrait = extract_date(str(cell.value), annee_numerique) # Utilise l'année numérique
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
def obtenir_vacances(zone="C", annee_scolaire_str=None):
    """
    Récupère les dates de vacances scolaires pour une zone et une année scolaire données.
    annee_scolaire_str est au format "YYYY-YYYY".
    """
    # Si annee_scolaire_str n'est pas fourni, le détecter automatiquement
    if annee_scolaire_str is None:
        annee_scolaire_str = detecter_annee_scolaire_actuelle()

    url = "https://data.education.gouv.fr/api/records/1.0/search/"
    params = {
        "dataset": "fr-en-calendrier-scolaire",
        "rows": 500,
        "refine.zone": f"Zone {zone}",
        "refine.annee_scolaire": annee_scolaire_str, # Utilise la chaîne de l'année scolaire détectée
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
                except ValueError:
                    pass

        # Filtrer les vacances pour la période pertinente (début septembre à fin août de l'année suivante)
        annee_debut_num = int(annee_scolaire_str.split('-')[0])
        annee_fin_num = int(annee_scolaire_str.split('-')[1])
        
        periode_debut = datetime(annee_debut_num, 9, 1)
        periode_fin = datetime(annee_fin_num, 8, 31)

        vacances = [(start, end) for start, end in vacances if 
                    (to_naive(end) >= periode_debut and to_naive(start) <= periode_fin)]

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
    """Enregistre les paramètres de l'application (groupe, semaine, classe)."""
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")

def charger_parametres():
    """Charge les paramètres de l'application (groupe, semaine, classe)."""
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

def afficher_donnees_colloscope(annee_scolaire_actuelle):
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

    dictionnaire_donnees, dictionnaire_legende, _ = charger_donnees(classe, annee_scolaire_actuelle)
    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)

    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]

    st.table(df.style.hide(axis='index'))

# --- Fonctions d'accès propriétaire (Debug) ---

def afficher_dictionnaires_secrets(classe_selectionnee, annee_scolaire_actuelle):
    st.subheader("Contenu des dictionnaires")
    try:
        dictionnaire_donnees, dictionnaire_legende, dates_semaines = charger_donnees(classe_selectionnee, annee_scolaire_actuelle)
        
        st.write("### Dictionnaire de Données (`dictionnaire_donnees`)")
        st.json(dictionnaire_donnees)

        st.write("### Dictionnaire de Légende (`dictionnaire_legende`)")
        st.json(dictionnaire_legende)

        st.write("### Dates des Semaines (`dates_semaines`)")
        dates_str = [d.strftime("%d/%m/%Y") if d else "None" for d in dates_semaines]
        st.write(dates_str)

    except Exception as e:
        st.error(f"Erreur lors du chargement ou de l'affichage des dictionnaires : {e}")

def gerer_outils_debug(classe_selectionnee, annee_scolaire_actuelle):
    st.subheader("Outils de débogage")
    
    st.write(f"**Année Scolaire Détectée Automatiquement :** {annee_scolaire_actuelle}")

    st.markdown("---")

    if st.button("Recharger les données (Colloscope/Légende)", key="reload_data_btn_debug"):
        st.cache_data.clear()
        st.success("Cache des données vidé. Les fichiers Excel seront relus au prochain accès.")
        st.rerun()

    if st.button("Vider tout le cache Streamlit", key="clear_all_cache_btn_debug"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Tout le cache Streamlit a été vidé.")
        st.rerun()

    st.write("### Informations système")
    st.write(f"**Date et heure actuelle du serveur :** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    st.write("Contenu de `st.session_state`:")
    st.json(st.session_state.to_dict())

# --- Comparateur Excel ---

def comparer_excels(df1, df2, nom_fichier):
    same_cols = list(df1.columns) == list(df2.columns)
    same_shape = df1.shape == df2.shape

    st.write(f"### Résultat comparaison : {nom_fichier}")
    if same_cols and same_shape:
        st.success(f"✅ {nom_fichier} : même structure (colonnes + dimensions).")
    else:
        if not same_cols:
            st.error(f"⚠️ Colonnes différentes dans {nom_fichier} :")
            st.write("Référence :", list(df1.columns))
            st.write("Nouveau :", list(df2.columns))
        if not same_shape:
            st.error(f"⚠️ Dimensions différentes dans {nom_fichier} : {df1.shape} vs {df2.shape}")

    # Comparer la première ligne
    if not df1.empty and not df2.empty:
        first_row_ref = df1.iloc[0].tolist()
        first_row_new = df2.iloc[0].tolist()
        if first_row_ref == first_row_new:
            st.info(f"✅ Première ligne identique ({nom_fichier})")
        else:
            st.warning(f"⚠️ Différences dans la première ligne ({nom_fichier})")
            st.write("Référence :", first_row_ref)
            st.write("Nouveau :", first_row_new)

    # Comparer la première colonne
    if df1.shape[0] > 0 and df2.shape[0] > 0:
        first_col_ref = df1.iloc[:,0].tolist()
        first_col_new = df2.iloc[:,0].tolist()
        if first_col_ref == first_col_new:
            st.info(f"✅ Première colonne identique ({nom_fichier})")
        else:
            st.warning(f"⚠️ Différences dans la première colonne ({nom_fichier})")
            st.write("Référence :", first_col_ref)
            st.write("Nouveau :", first_col_new)

# --- Dialogue d'authentification pour le debug ---
@st.dialog("Accès Propriétaire")
def debug_dialog():
    st.write("Veuillez entrer le code secret pour accéder aux outils de débogage.")
    code_secret_input = st.text_input("Code secret", type="password", key="dialog_secret_code")

    if st.button("Valider l'accès"):
        if code_secret_input == CODE_PROPRIETAIRE:
            st.session_state["authenticated_owner"] = True
            st.success("Accès accordé !")
            st.rerun() 
        else:
            st.error("Code incorrect.")
            st.session_state["authenticated_owner"] = False

# --- Fonction principale de l'application ---

def principal():
    # Détecter l'année scolaire au début de chaque exécution
    annee_scolaire_actuelle = detecter_annee_scolaire_actuelle()

    # Charger les paramètres (groupe, semaine, classe)
    groupe_default, semaine_saved, classe_default = charger_parametres()

    # Initialiser st.session_state
    if "groupe" not in st.session_state:
        st.session_state.groupe = groupe_default
    if "semaine" not in st.session_state:
        st.session_state.semaine = semaine_saved
    if "classe" not in st.session_state:
        st.session_state.classe = classe_default

    # Définition des onglets principaux
    tabs_names = ["Colloscope"]
    if st.session_state.get("authenticated_owner", False):
        tabs_names.append("Outils Propriétaire")
    
    main_tabs = st.tabs(tabs_names)

    # Onglet Colloscope
    with main_tabs[0]:
        st.header("Colloscope")
        
        if st.button('EDT EPS', key="edt_eps_btn_main"):
            st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
            st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

        st.sidebar.header("Sélection")

        date_actuelle = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        _, _, dates_semaines_initiales = charger_donnees(st.session_state.classe, annee_scolaire_actuelle) 
        semaines_ecoulees = semaine_actuelle(dates_semaines_initiales, date_actuelle)
        date_actuelle_str = date_actuelle.strftime("%d/%m")

        st.sidebar.write(f
