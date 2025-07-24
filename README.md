# Projet Streamlit - Gestion de Colloscope

Ce projet est une application Streamlit permettant de gérer et d'afficher les informations d'un colloscope (emploi du temps des groupes de kholle), avec une interface simple pour sélectionner le groupe, la semaine et la classe.

## Fonctionnalités

- **Sélection de la Classe** : L'utilisateur peut choisir entre différentes classes (TSI 1 ou TSI 2).
- **Sélection du Groupe et de la Semaine** : L'utilisateur peut saisir le groupe et la semaine pour afficher les données correspondantes.
- **Affichage des Données** : Les informations du colloscope sont affichées sous forme de tableau avec les colonnes Professeur, Jour, Heure et Salle.
- **Gestion des Erreurs** : Le programme vérifie les entrées de l'utilisateur et affiche des messages d'erreur en cas d'erreur de saisie (groupe ou semaine invalides).
- **Affichage de la semaine en cours** : Affiche la semaine en cours en comptant le nombre de semaine passée depuis le debut des kholles.
  
# Tutoriel : Modifier les fichiers Excel pour le Colloscope

Ce tutoriel vous guide pour mettre à jour ou modifier les fichiers Excel utilisés par votre application de colloscope Streamlit, vous pouvez prendre exemple avec les fichiers excels déjà existant, il faut que les nouveaux fichier excels soit les mêmes que ceux existant sinon le programme ne fonctionnera pas.

---
Suivez ces étapes simples pour transformer votre PDF en Excel :

1.  **Accéder à l'outil iLovePDF :** Ouvrez votre navigateur web et rendez-vous sur la page de conversion PDF vers Excel d'iLovePDF :
    [https://www.ilovepdf.com/fr/pdf_vers_excel](https://www.ilovepdf.com/fr/pdf_vers_excel)

2.  **Sélectionner votre fichier PDF :**
    * Cliquez sur le bouton rouge "Sélectionner le fichier PDF".
    * Une fenêtre s'ouvrira, vous permettant de naviguer sur votre ordinateur. Sélectionnez le fichier PDF que vous souhaitez convertir et cliquez sur "Ouvrir".
    * Vous pouvez également faire glisser et déposer votre fichier PDF directement dans la zone désignée sur la page web.

3.  **Lancer la conversion :**
    * Une fois votre fichier PDF téléchargé, cliquez sur le bouton rouge "Convertir en EXCEL" situé en bas à droite de la page.

4.  **Télécharger le fichier Excel :**
    * Après un court instant, iLovePDF aura converti votre fichier.
    * Cliquez sur le bouton rouge "Télécharger EXCEL" pour enregistrer le fichier `.xlsx` sur votre ordinateur.

## 📂 **Structure des fichiers Excel**
### **1. Fichiers nécessaires :**
- **Colloscope\<classe>.xlsx**  
  Contient les données d’organisation hebdomadaire pour chaque groupe (horaires, professeurs, salles, etc.).
  
- **Legende\<classe>.xlsx**  
  Fournit la légende associée aux éléments utilisés dans le colloscope (ex. matière, professeur).

---

### **2. Format des fichiers :**
#### **Colloscope\<classe>.xlsx**
| **Groupe** | **Semaine 1** | **Semaine 2** | **...** | **Semaine N** |
|------------|---------------|---------------|---------|---------------|
| G1         | SI1           | SI2           | ...     | M1            |
| G2         | M1            | A1            | ...     | F1            |

- **Colonne 1 (Groupe) :** Nom des groupes (ex. G1, G2, etc.).
- **Colonnes suivantes :** Contiennent les clés correspondant aux entrées dans le fichier légende.

#### **Legende\<classe>.xlsx**
| **Clé** | **Professeur** | **Jour** | **Heure** | **Salle** |
|---------|----------------|----------|-----------|-----------|
| M1      | ......         | Lundi    | 8h-10h    | Salle 101 |
| SI1     | ......         | Mardi    | 10h-12h   | Salle 202 |

- **Colonne 1 (Clé) :** Identifiant unique lié à chaque cours.
- **Colonnes suivantes :** Détails associés à chaque clé :
  - Professeur
  - Jour
  - Heure
  - Salle

---

## 🛠 **Modifier les fichiers Excel**
### Étape 1 : Localisez les fichiers
1. Ouvrez le dossier contenant les fichiers Excel.  
   **Par défaut :** Ils doivent être situés dans le même répertoire que l'application Streamlit.  
   - `Colloscope1.xlsx` (TSI1)
   - `Colloscope2.xlsx` (TSI2)
   - `Legende1.xlsx` (TSI1)
   - `Legende2.xlsx` (TSI2)

2. Si les fichiers n'existent pas ou sont mal placés, l'application affichera une erreur.

---

### Étape 2 : Ouvrez les fichiers avec Excel
1. Double-cliquez sur le fichier que vous voulez modifier.
2. Assurez-vous de respecter les formats suivants :
   - Les noms des groupes et des clés doivent être **identiques** dans les deux fichiers.
   - Ne laissez aucune cellule vide dans les colonnes obligatoires (Groupe, Clé, Professeur, etc.).

---

