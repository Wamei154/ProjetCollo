import os
import streamlit as st
from openpyxl import load_workbook
import pandas as pd
from datetime import datetime

def chemin_ressource(chemin_relatif):
    """Retourne le chemin absolu vers la ressource"""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, chemin_relatif)


def aplatir_liste(liste_imbriquee):
    """Aplatis une liste imbriquée"""
    return [' '.join(sous_liste) for sous_liste in liste_imbriquee]


@st.cache_data
def charger_donnees(classe):
    """Charge les données des fichiers Excel selon la classe sélectionnée"""
    fichier_colloscope = chemin_ressource(f'Colloscope{classe}.xlsx')
    fichier_legende = chemin_ressource(f'Legende{classe}.xlsx')

    excel_colloscope = load_workbook(fichier_colloscope)
    excel_legende = load_workbook(fichier_legende)

    feuille_colloscope = excel_colloscope.active
    feuille_legende = excel_legende.active

    dictionnaire_donnees = {}
    dictionnaire_legende = {}

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

    return dictionnaire_donnees, dictionnaire_legende


def obtenir_semaine_actuelle():
    """Retourne la semaine actuelle (max 30)"""
    maintenant = datetime.now()
    semaine_actuelle = maintenant.isocalendar()[1]
    return min(semaine_actuelle, 30)


def enregistrer_parametres(groupe, semaine, classe):
    """Enregistre les paramètres dans un fichier de configuration"""
    with open('config.txt', 'w') as fichier:
        fichier.write(f"{groupe}\n{semaine}\n{classe}")


def charger_parametres():
    """Charge les paramètres depuis le fichier de configuration"""
    groupe = "G1"
    semaine = str(obtenir_semaine_actuelle())
    classe = "1"  # Classe par défaut
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as fichier:
            lignes = fichier.readlines()
            if len(lignes) >= 3:
                groupe = lignes[0].strip()
                semaine = lignes[1].strip()
                classe = lignes[2].strip()
    return groupe, semaine, classe


def creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende):
    """Génère les données pour un groupe et une semaine donnés"""
    tableau = []

    try:
        # Vérification de la présence du groupe dans dictionnaire_donnees
        if groupe not in dictionnaire_donnees:
            raise KeyError(f"Le groupe '{groupe}' n'existe pas dans les données.")

        # Convertir 'semaine' en entier pour éviter l'erreur de type
        semaine = int(semaine)

        # Vérification que l'index de la semaine est valide
        if semaine - 1 >= len(dictionnaire_donnees[groupe]) or semaine - 1 < 0:
            raise IndexError(f"La semaine {semaine} n'est pas valide pour le groupe '{groupe}'.")

        # Accès aux données de la semaine spécifiée
        ligne = dictionnaire_donnees[groupe][semaine - 1]

        # Boucle pour assembler les éléments
        for k in range(len(ligne)):
            # Vérification de la clé dans dictionnaire_legende
            if ligne[k] not in dictionnaire_legende:
                raise KeyError(f"La clé '{ligne[k]}' n'existe pas dans les données de légende.")

            # Assemble la ligne
            elements_assembles = aplatir_liste(dictionnaire_legende[ligne[k]])

            # Gère les lettres spécifiques pour assigner les matières
            matiere = "Non spécifié"  # Valeur par défaut

            if ligne[k].startswith('M'):
                matiere = "Mathématiques"
            elif ligne[k].startswith('A'):
                matiere = "Anglais"
            elif ligne[k].startswith('SI'):
                matiere = "Sciences de l'Ingénieur"
            elif ligne[k].startswith('F'):
                matiere = "Français"
            elif ligne[k].startswith('I'):
                matiere = "Informatique"
            elif ligne[k].startswith('P'):
                matiere = "Physique"
            # Ajouter d'autres conditions pour d'autres matières si nécessaire

            # Ajoute la colonne Matière à la ligne
            elements_assembles.append(matiere)
            tableau.append(elements_assembles)

    except KeyError as erreur:
        st.error(str(erreur))
        return tableau

    except IndexError as erreur:
        st.error(str(erreur))
        return tableau

    except Exception as erreur:
        st.error(f"Une erreur inattendue s'est produite : {str(erreur)}")
        return tableau

    return tableau


def calculer_semaines_ecoulees(date_debut, date_actuelle):
    """Calcule le nombre de semaines passées depuis la date de début"""
    delta = date_actuelle - date_debut
    semaines_ecoulees = delta.days // 7
    return semaines_ecoulees


def afficher_donnees():
    """Affiche les données dans un tableau Streamlit"""
    groupe = st.session_state.groupe
    semaine = st.session_state.semaine
    classe = st.session_state.classe

    enregistrer_parametres(groupe, semaine, classe)

    try:
        semaine = int(semaine)
        if semaine < 1 or semaine > 30:
            st.error("La Semaine doit être entre 1 et 30.")
            return
    except ValueError:
        st.error("Veuillez entrer une Semaine valide entre 1 et 30.")
        return

    try:
        numero_groupe = int(groupe[1:])
        if numero_groupe < 0 or numero_groupe > 20:
            st.error("Le Groupe doit être entre 1 et 20.")
            return
    except ValueError:
        st.error("Veuillez entrer un Groupe valide entre 1 et 20.")
        return

    dictionnaire_donnees, dictionnaire_legende = charger_donnees(classe)

    donnees = creer_tableau(groupe, semaine, dictionnaire_donnees, dictionnaire_legende)

    # Colonnes mises à jour pour inclure la Matière
    df = pd.DataFrame(donnees, columns=["Professeur", "Jour", "Heure", "Salle", "Matière"])
    df.index = ['' for _ in range(len(df))]

    st.table(df.style.hide(axis='index'))


def principal():
    """Fonction principale de l'application Streamlit"""
    if st.sidebar.button('EDT EPS'):
        st.image("EPS_page-0001.jpg", caption="EDT EPS TSI1")
        st.image("EPS_page-0002.jpg", caption="EDT EPS TSI2")

    st.sidebar.header("Sélection")

    # Date de début de la première semaine
    date_debut = datetime.strptime("16/09/2024", "%d/%m/%Y")
    date_actuelle = datetime.now()

    # Calculer le nombre de semaines passées
    semaines_ecoulees = calculer_semaines_ecoulees(date_debut, date_actuelle)
    date_actuelle_str = date_actuelle.strftime("%d/%m")

    st.sidebar.write(f"**Semaine en cours** : {semaines_ecoulees}")
    st.sidebar.write(f"**Date** :  {date_actuelle_str}")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value=charger_parametres()[0])
    semaine = st.sidebar.selectbox("Semaine", options=[str(i) for i in range(1, 31)], index=int(charger_parametres()[1]) - 1)

    if st.sidebar.button("Afficher", on_click=afficher_donnees):
        st.info("Veuillez vérifier votre colloscope papier pour éviter les erreurs.", icon="⚠️")

    st.markdown(
        """
        <div style="position: fixed ; center: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.groupe = groupe
    st.session_state.semaine = semaine
    st.session_state.classe = classe


if __name__ == "__main__":
    principal()
