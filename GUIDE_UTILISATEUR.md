# 📖 GUIDE UTILISATEUR - APPLICATION LCDI

## 🎯 Objectif
Générer automatiquement un tableau de facturation consolidé à partir des données Shopify, avec possibilité de compléter un fichier existant.

## 🚀 Démarrage rapide

### 1. Lancer l'application
```bash
cd "c:\Code\Apps\Compta LCDI V2"
python app.py
```

### 2. Ouvrir dans le navigateur
```
http://localhost:5000
```

## 📁 Préparation des fichiers

### Fichiers requis (3 fichiers CSV) :
1. **Fichier des commandes** - Export Shopify des commandes
2. **Fichier des transactions** - Export Shopify des transactions
3. **Fichier journal** - Export du journal comptable

### Formats acceptés :
- **Nouveaux fichiers** : CSV uniquement
- **Ancien fichier** (mode combinaison) : CSV ou Excel (.xlsx)

## ⚙️ Modes d'utilisation

### 🆕 Mode "Nouveau fichier"
**Utilisation :** Générer un nouveau tableau consolidé

**Étapes :**
1. Sélectionner "Nouveau fichier"
2. Charger les 3 fichiers CSV requis
3. Cliquer sur "Générer le tableau consolidé"
4. Téléchargement automatique du fichier Excel

**Fichier généré :** `Compta_LCDI_Shopify_DD_MM_YYYY.xlsx`

### 🔄 Mode "Combiner avec ancien fichier"
**Utilisation :** Ajouter de nouvelles données à un fichier existant

**Étapes :**
1. Sélectionner "Combiner avec ancien fichier"
2. Charger les 3 fichiers CSV avec les nouvelles données
3. Charger l'ancien fichier Excel/CSV à compléter
4. Cliquer sur "Combiner avec l'ancien fichier"
5. Téléchargement du fichier fusionné

**Fichier généré :** `Compta_LCDI_Shopify_COMBINE_DD_MM_YYYY.xlsx`

**⚠️ Important :** Les doublons sont automatiquement évités basé sur la colonne "Réf.WEB"

## 📊 Colonnes générées

### Informations de base :
- **Réf.WEB** : Référence de la commande
- **Date** : Date de traitement
- **Client** : Nom du client
- **Statut facturation** : Statut Shopify

### Montants (priorité au journal comptable) :
- **TTC** : Montant toutes taxes comprises
- **HT** : Montant hors taxes  
- **TVA** : Montant de la TVA

### Répartition par méthode de paiement :
- **Virement bancaire**
- **Carte bancaire** (inclut Shopify Payments)
- **PayPal**
- **ALMA** (financement)
- **Younited** (financement)

### Colonnes techniques :
- **Statut** : COMPLET / INCOMPLET (formule Excel dynamique)
- **Solde restant**
- **Frais de transaction**
- **Montant net**

## 🎨 Formatage Excel

### Formatage conditionnel :
- 🟢 **Vert** : Statut COMPLET
- 🔴 **Rouge** : Statut INCOMPLET
- 🟡 **Jaune clair** : Données manquantes (NaN)

### Police et style :
- **Police** : Arial
- **Formules dynamiques** : Calcul automatique du statut
- **Largeur des colonnes** : Ajustée automatiquement

## ⚠️ Gestion des erreurs

### Messages d'information :
- **Succès** : "Tableau généré avec succès! X lignes traitées"
- **Combinaison** : "X nouvelles lignes ajoutées. Total: Y lignes"
- **Doublons** : Évités automatiquement et signalés

### Erreurs courantes :
- **Fichier manquant** : Vérifier que tous les fichiers sont sélectionnés
- **Format incorrect** : Utiliser uniquement CSV pour les nouveaux fichiers
- **Fichier trop volumineux** : Limite de 16MB par fichier
- **Encodage** : Détection automatique, fallback sur plusieurs encodages

## 💡 Conseils d'utilisation

### Pour de meilleurs résultats :
1. **Cohérence des noms** : S'assurer que les colonnes des fichiers CSV ont des noms cohérents
2. **Qualité des données** : Vérifier que la colonne "Réf.WEB" est présente et unique
3. **Ordre chronologique** : Traiter les fichiers dans l'ordre chronologique pour le mode combinaison
4. **Sauvegarde** : Toujours conserver une sauvegarde avant de remplacer un fichier existant

### Optimisation :
- **Gros volumes** : L'application gère efficacement les gros fichiers
- **Mémoire** : Nettoyage automatique des fichiers temporaires
- **Performance** : Traitement optimisé avec pandas

## 🔧 Dépannage

### Si l'application ne démarre pas :
```bash
# Vérifier Python
python --version

# Installer les dépendances
pip install -r requirements.txt

# Redémarrer l'application
python app.py
```

### Si le navigateur ne s'ouvre pas :
- Vérifier que l'application indique "Running on http://127.0.0.1:5000"
- Ouvrir manuellement : http://localhost:5000

### En cas d'erreur de traitement :
- Vérifier le format des fichiers CSV
- S'assurer que les colonnes essentielles sont présentes
- Consulter les messages d'erreur détaillés

## 📞 Support

En cas de problème persistant :
1. Vérifier les messages d'erreur dans l'interface
2. Consulter les fichiers de log (affichés dans le terminal)
3. Vérifier la documentation technique (DOCUMENTATION_TECHNIQUE.md)

## 🎉 Résultat attendu

Un fichier Excel professionnel avec :
- ✅ Toutes les données consolidées et formatées
- ✅ Pas de doublons (en mode combinaison)
- ✅ Statuts calculés automatiquement
- ✅ Formatage conditionnel pour identifier les données manquantes
- ✅ Nommage standardisé avec date
