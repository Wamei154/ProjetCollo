Projet Streamlit - Gestion de Colloscope
Ce projet est une application Streamlit intuitive conçue pour gérer et afficher les informations d'un colloscope (emploi du temps des groupes de kholle). Elle offre une interface utilisateur simple pour naviguer et consulter les données pertinentes.

Fonctionnalités Clés
Sélection de la Classe : Choisissez facilement entre différentes classes (ex: TSI 1 ou TSI 2).

Recherche par Groupe et Semaine : Saisissez le groupe et la semaine désirés pour afficher l'emploi du temps correspondant.

Affichage Clair des Données : Les informations du colloscope sont présentées dans un tableau lisible, incluant les colonnes Professeur, Jour, Heure, et Salle.

Gestion des Erreurs de Saisie : L'application vérifie vos entrées et affiche des messages d'erreur clairs si le groupe ou la semaine saisis sont invalides.

Indicateur de Semaine Actuelle : Affiche automatiquement la semaine en cours en calculant le nombre de semaines écoulées depuis le début des kholles.

📂 Structure des Fichiers Excel
L'application repose sur deux types de fichiers Excel essentiels pour fonctionner correctement. Il est impératif que les nouveaux fichiers Excel que vous créerez respectent ce format pour que le programme fonctionne. Vous pouvez vous baser sur les fichiers existants comme modèles.

1. Fichiers Nécessaires
Colloscope<classe>.xlsx : Ce fichier contient l'organisation hebdomadaire des kholles pour chaque groupe.

Exemples : Colloscope1.xlsx (pour TSI1), Colloscope2.xlsx (pour TSI2).

Legende<classe>.xlsx : Ce fichier sert de base de données pour les détails de chaque séance (professeur, jour, heure, salle) identifiés par une "Clé" unique.

Exemples : Legende1.xlsx (pour TSI1), Legende2.xlsx (pour TSI2).

2. Format Attendu des Fichiers
Colloscope<classe>.xlsx
Ce tableau liste les "clés" de séance pour chaque groupe et semaine.

Groupe	S1 (XX/XX)	S2 (XX/XX)	...	SN (XX/XX)
G1	SI1	SI2	...	M1
G2	M1	A1	...	F1

Exporter vers Sheets
Legende<classe>.xlsx
Ce tableau fournit les informations détaillées associées à chaque "Clé" trouvée dans le Colloscope.

Clé	Professeur	Jour	Heure	Salle
M1	Dupont	Lundi	8h-10h	Salle 101
SI1	Martin	Mardi	10h-12h	Salle 202

Exporter vers Sheets
🛠 Tutoriel : Mettre à Jour les Fichiers Excel
Ce guide vous expliquera comment convertir vos PDFs en Excel et comment formater correctement le fichier Legende<classe>.xlsx.

Étape 1 : Convertir un PDF en Excel (avec iLovePDF)
Si vous avez un nouveau colloscope en format PDF, commencez par le convertir en Excel :

Ouvrez iLovePDF : Accédez à l'outil de conversion PDF vers Excel sur https://www.ilovepdf.com/fr/pdf_en_excel.

Sélectionnez votre PDF :

Cliquez sur le bouton rouge "Sélectionner le fichier PDF" et choisissez votre fichier sur votre ordinateur.

Alternativement, vous pouvez glisser-déposer votre fichier PDF directement sur la zone indiquée.

Lancez la conversion :

IMPORTANT : Sous l'option "Mise en page", sélectionnez "Une feuille". Cela garantit que toutes les données soient sur une seule feuille Excel, ce qui est crucial pour le bon fonctionnement de l'application.

Puis, cliquez sur le bouton rouge "Convertir en EXCEL".

Téléchargez le fichier Excel :

Une fois la conversion terminée, cliquez sur le bouton rouge "Télécharger EXCEL" pour sauvegarder le fichier .xlsx sur votre ordinateur.

Étape 2 : Préparer et Formater le Fichier Legende<classe>.xlsx
Le fichier Legende<classe>.xlsx nécessite un formatage précis pour être correctement lu par l'application.

2.1. Localisation des Fichiers
Assurez-vous que vos fichiers Excel sont bien situés dans le même répertoire que votre application Streamlit. Par défaut, ils devraient être nommés :

Colloscope1.xlsx

Colloscope2.xlsx

Legende1.xlsx

Legende2.xlsx

Si les fichiers sont absents ou mal nommés, l'application affichera une erreur.

2.2. Alignement des Données
Ouvrez le fichier Legende<classe>.xlsx (par exemple Legende1.xlsx) avec Excel.

Vérifiez que toutes les données sont correctement alignées dans leurs colonnes respectives (Clé, Professeur, Jour, Heure, Salle). Assurez-vous qu'il n'y a pas de cellules fusionnées de manière incorrecte ou d'espaces superflus qui pourraient décaler les informations.

2.3. Séparer le "Jour" et l'"Heure" en Deux Colonnes Distinctes
La colonne "Jour" contient souvent à la fois le jour de la semaine et la plage horaire (ex: "Lundi 8h-10h"). Nous allons les séparer en deux colonnes distinctes pour une meilleure clarté.

Voici comment faire dans Excel :

Sélectionnez la colonne "Jour" :

Cliquez sur l'en-tête de la colonne (la lettre en haut, comme "C") pour sélectionner toutes les cellules de cette colonne.

Utilisez l'outil "Convertir" :

Allez dans l'onglet "Données" du ruban Excel.

Dans le groupe "Outils de données", cliquez sur le bouton "Convertir" (souvent une icône avec une flèche).

Assistant de Conversion (Étape 1/3) : Type de données

Dans la fenêtre "Assistant Conversion", choisissez l'option "Délimité".

Cliquez sur "Suivant".

Assistant de Conversion (Étape 2/3) : Choisir le séparateur

Sous "Séparateurs", cochez uniquement la case "Espace".

Vérifiez l'aperçu en bas pour vous assurer que vos données seront bien séparées (ex: "Lundi" dans une colonne, "8h-10h" dans l'autre).

Cliquez sur "Suivant".

Assistant de Conversion (Étape 3/3) : Format et Destination

Pour les "Formats des données en colonne", laissez "Standard" pour les deux colonnes (Jour et Heure).

Très important pour la "Destination" : Cliquez sur la petite flèche à côté du champ "Destination" et sélectionnez la première cellule vide de la colonne juste à droite de votre colonne "Jour" actuelle (par exemple, si "Jour" est en colonne C, choisissez la cellule D1). Cela évitera d'écraser des données existantes.

Cliquez sur "Terminer".

Votre colonne "Jour" affichera maintenant uniquement le jour de la semaine, et une nouvelle colonne aura été créée contenant les plages horaires. Vous pouvez ensuite renommer cette nouvelle colonne en "Heure" si ce n'est pas déjà fait.
