# Tutoriel : Modifier les fichiers Excel pour le Colloscope

Ce tutoriel vous guide pour mettre à jour ou modifier les fichiers Excel utilisés par votre application de colloscope Streamlit.

---

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
| M1      | Dupont         | Lundi    | 8h-10h    | Salle 101 |
| SI1     | Martin         | Mardi    | 10h-12h   | Salle 202 |

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

### Étape 3 : Mettez à jour les données
- **Ajouter un groupe :** Ajoutez une nouvelle ligne dans le fichier `Colloscope`. Assurez-vous d’ajouter des clés valides qui existent dans le fichier `Legende`.
- **Ajouter une légende :** Ajoutez une nouvelle ligne dans le fichier `Legende` avec une clé unique et ses détails.

---

### Étape 4 : Sauvegardez les fichiers
1. Cliquez sur **Fichier** > **Enregistrer sous**.
2. **IMPORTANT :** Conservez le format `.xlsx` et ne changez pas le nom du fichier.

---
