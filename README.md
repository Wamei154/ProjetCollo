# Projet Streamlit - Gestion de Colloscope

Ce projet est une application Streamlit permettant de gérer et d'afficher les informations d'un colloscope (emploi du temps des groupes d'élèves), avec une fonctionnalité de téléchargement et une interface simple pour sélectionner le groupe, la semaine et la classe.

## Fonctionnalités

- **Sélection de la Classe** : L'utilisateur peut choisir entre différentes classes (TSI 1 ou TSI 2).
- **Sélection du Groupe et de la Semaine** : L'utilisateur peut saisir le groupe et la semaine pour afficher les données correspondantes.
- **Affichage des Données** : Les informations du colloscope sont affichées sous forme de tableau avec les colonnes Professeur, Jour, Heure et Salle.
- **Gestion des Erreurs** : Le programme vérifie les entrées de l'utilisateur et affiche des messages d'erreur en cas d'erreur de saisie (groupe ou semaine invalides).
- **Téléchargement de fichier** : Un bouton pour télécharger un fichier .exe via un lien Google Drive (en construction).
  
## Dépendances

Les bibliothèques nécessaires sont les suivantes :

- `streamlit`
- `openpyxl`
- `pandas`
- `smtplib` (pour les notifications par e-mail si besoin)
- `email` (pour la gestion des emails)
- `pytz` (pour la gestion des fuseaux horaires)

Ces bibliothèques peuvent être installées en exécutant :

```bash
pip install streamlit openpyxl pandas pytz
