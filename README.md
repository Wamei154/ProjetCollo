#Projet Streamlit - Gestion de Colloscope
Ce projet est une application Streamlit permettant de gérer et d'afficher les informations d'un colloscope (emploi du temps des groupes d'élèves), avec une fonctionnalité de téléchargement et une interface simple pour sélectionner le groupe, la semaine et la classe.

Fonctionnalités
Sélection de la Classe : L'utilisateur peut choisir entre différentes classes (TSI 1 ou TSI 2).
Sélection du Groupe et de la Semaine : L'utilisateur peut saisir le groupe et la semaine pour afficher les données correspondantes.
Affichage des Données : Les informations du colloscope sont affichées sous forme de tableau avec les colonnes Professeur, Jour, Heure et Salle.
Gestion des Erreurs : Le programme vérifie les entrées de l'utilisateur et affiche des messages d'erreur en cas d'erreur de saisie (groupe ou semaine invalides).
Téléchargement de fichier : Un bouton pour télécharger un fichier .exe via un lien Google Drive (en construction).
Dépendances
Les bibliothèques nécessaires sont les suivantes :

streamlit
openpyxl
pandas
smtplib (pour les notifications par e-mail si besoin)
email (pour la gestion des emails)
pytz (pour la gestion des fuseaux horaires)
Ces bibliothèques peuvent être installées en exécutant :

bash
Copier le code
pip install streamlit openpyxl pandas pytz
Installation et Utilisation
Cloner le projet :
bash
Copier le code
git clone https://github.com/votre-repo/colloscope-streamlit.git
cd colloscope-streamlit
Installer les dépendances :
bash
Copier le code
pip install -r requirements.txt
Lancer l'application :
bash
Copier le code
streamlit run app.py
Accéder à l'application :
L'application sera accessible à l'adresse locale http://localhost:8501/.

Organisation des fichiers
app.py : Contient le code principal de l'application Streamlit.
config.txt : Fichier de configuration pour enregistrer les choix de groupe, semaine et classe.
Colloscope1.xlsx et Legende1.xlsx : Fichiers Excel contenant les données du colloscope et la légende associée pour la classe 1 (TSI1).
Colloscope2.xlsx et Legende2.xlsx : Fichiers Excel pour la classe 2 (TSI2).
Instructions
Affichage des données : Dans la barre latérale, sélectionnez la classe, entrez le groupe (ex : G10), et la semaine (entre 1 et 30), puis cliquez sur "Afficher".
Téléchargement : Un bouton dans la barre latérale permet d'accéder à un lien Google Drive pour télécharger un fichier EXE (en construction).
Auteurs
Mael Berry
Avec l'aide de Gauthier Souvelain et Paul Dambry
