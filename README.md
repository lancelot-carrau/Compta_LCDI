# 📊 Générateur de Tableau de Facturation LCDI

Application web Flask pour générer automatiquement un tableau de facturation consolidé à partir de trois fichiers CSV.

## 🚀 Fonctionnalités

- **Interface web moderne** avec glisser-déposer
- **Traitement automatisé** de trois fichiers CSV
- **Validation des données** avec nettoyage automatique
- **Téléchargement automatique** du fichier généré
- **Gestion des erreurs** complète
- **Format de sortie personnalisé** (séparateur `;` et décimal `,`)

## 📁 Fichiers d'entrée requis

### 1. Fichier des commandes (ex: `orders_export.csv`)
- **Séparateur :** virgule (`,`)
- **Colonnes requises :**
  - `Name` - Référence de la commande
  - `Fulfilled at` - Date de traitement
  - `Billing name` - Nom du client
  - `Financial Status` - Statut financier
  - `Tax 1 Value` - Montant de la TVA
  - `Outstanding Balance` - Solde restant
  - `Payment Method` - Méthode de paiement

### 2. Fichier des transactions (ex: `payment_transactions_export.csv`)
- **Séparateur :** virgule (`,`)
- **Colonnes requises :**
  - `Order` - Référence de la commande
  - `Presentment Amount` - Montant TTC
  - `Fee` - Frais de commission
  - `Net` - Montant net reçu

### 3. Fichier Journal (ex: `20250604-Journal.csv`)
- **Séparateur :** point-virgule (`;`)
- **Colonnes requises :**
  - `Piece` - Référence de la pièce
  - `Référence LMB` - Référence comptable

## 📋 Structure du tableau de sortie

Le fichier généré `tableau_facturation_final_YYYYMMDD_HHMMSS.csv` contient 16 colonnes :

1. **Centre de profit** - Valeur fixe : "lcdi.fr"
2. **Réf.WEB** - Référence web de la commande
3. **Réf. LMB** - Référence comptable
4. **Date Facture** - Date au format jj/mm/aaaa
5. **Etat** - Statut de la commande
6. **Client** - Nom du client
7. **HT** - Montant hors taxes (TTC - TVA)
8. **TVA** - Montant de la TVA
9. **TTC** - Montant toutes taxes comprises
10. **reste** - Solde restant dû
11. **Shopify** - Montant net Shopify
12. **Frais de commission** - Frais prélevés
13. **Virement bancaire** - Montant si paiement par virement
14. **ALMA** - Montant si paiement ALMA
15. **Younited** - Montant si paiement Younited
16. **PayPal** - Montant si paiement PayPal

## 🛠 Installation

1. **Cloner le projet :**
   ```bash
   git clone <url-du-repo>
   cd "Compta LCDI V2"
   ```

2. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

3. **Lancer l'application :**
   ```bash
   python app.py
   ```

4. **Ouvrir dans le navigateur :**
   ```
   http://localhost:5000
   ```

## 💻 Utilisation

1. **Accéder à l'interface web** via `http://localhost:5000`
2. **Sélectionner les 3 fichiers CSV** requis
3. **Cliquer sur "Générer le tableau consolidé"**
4. **Le fichier se télécharge automatiquement** une fois le traitement terminé

## 🔧 Traitement des données

### Nettoyage automatique :
- ✅ Suppression des espaces superflus
- ✅ Conversion des dates au format français (jj/mm/aaaa)
- ✅ Formatage des colonnes monétaires en numérique
- ✅ Agrégation des transactions multiples par commande
- ✅ Remplacement des valeurs manquantes

### Logique de fusion :
1. **Fusion commandes + transactions** (jointure gauche sur `Name` = `Order`)
2. **Fusion résultat + journal** (jointure gauche sur `Name` = `Piece`)
3. **Conservation de toutes les commandes** même sans correspondance

### Répartition des paiements :
- Analyse automatique du champ `Payment Method`
- Répartition du montant TTC selon la méthode détectée
- Support : Virement bancaire, ALMA, Younited, PayPal

## 📊 Format de sortie

- **Séparateur de colonnes :** point-virgule (`;`)
- **Séparateur décimal :** virgule (`,`)
- **Encodage :** UTF-8 avec BOM
- **Nom du fichier :** `tableau_facturation_final_YYYYMMDD_HHMMSS.csv`

## ⚠️ Limitations

- Taille maximale par fichier : **16 MB**
- Formats acceptés : **CSV uniquement**
- Les noms de colonnes doivent correspondre exactement

## 🐛 Gestion des erreurs

L'application gère automatiquement :
- Fichiers manquants ou corrompus
- Colonnes manquantes dans les CSV
- Erreurs de format de date
- Valeurs manquantes ou invalides
- Problèmes d'encodage

## 👨‍💻 Développement

### Structure du projet :
```
Compta LCDI V2/
├── app.py              # Application Flask principale
├── templates/
│   └── index.html      # Interface utilisateur
├── uploads/            # Dossier temporaire (créé automatiquement)
├── output/             # Fichiers générés (créé automatiquement)
├── requirements.txt    # Dépendances Python
└── README.md          # Cette documentation
```

### Variables de configuration :
```python
UPLOAD_FOLDER = 'uploads'      # Dossier des fichiers temporaires
OUTPUT_FOLDER = 'output'       # Dossier des fichiers générés
MAX_CONTENT_LENGTH = 16 MB     # Taille max des fichiers
```

## 📞 Support

Pour toute question ou problème, contactez l'équipe de développement LCDI.

---

**Développé avec ❤️ pour LCDI**
