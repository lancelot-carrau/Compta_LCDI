# 🔧 Documentation Technique - LCDI Facturation

## Architecture de l'application

### Structure du projet
```
Compta LCDI V2/
├── app.py                  # Application Flask principale
├── templates/
│   └── index.html         # Interface utilisateur
├── static/                # Fichiers statiques (créé automatiquement)
├── uploads/               # Fichiers temporaires (créé automatiquement)
├── output/                # Fichiers générés (créé automatiquement)
├── test_data/             # Données de test (créé par test_app.py)
├── requirements.txt       # Dépendances Python
├── .env.example          # Configuration d'exemple
├── .gitignore            # Fichiers à ignorer par Git
├── start.bat             # Script de démarrage Windows
├── test_app.py           # Script de test
└── README.md             # Documentation utilisateur
```

## Fonctions principales

### `generate_consolidated_billing_table(orders_file, transactions_file, journal_file)`

Fonction principale qui traite les trois fichiers CSV et génère le tableau consolidé.

**Paramètres :**
- `orders_file` : Chemin vers le fichier des commandes
- `transactions_file` : Chemin vers le fichier des transactions  
- `journal_file` : Chemin vers le fichier journal

**Retourne :** DataFrame pandas avec le tableau consolidé

**Étapes de traitement :**
1. Chargement des fichiers CSV avec encodage UTF-8-sig
2. Nettoyage des données texte (suppression espaces)
3. Formatage des dates au format jj/mm/aaaa
4. Conversion des colonnes monétaires en numérique
5. Agrégation des transactions par commande
6. Fusion des DataFrames (jointures à gauche)
7. Création du tableau final avec 16 colonnes
8. Traitement des méthodes de paiement
9. Nettoyage final des valeurs manquantes

### `clean_text_data(df, text_columns)`

Nettoie les colonnes de texte utilisées comme clés de jointure.

### `format_date_to_french(date_str)`

Convertit différents formats de date vers le format français jj/mm/aaaa.

**Formats supportés :**
- YYYY-MM-DD
- DD/MM/YYYY
- MM/DD/YYYY  
- YYYY-MM-DD HH:MM:SS
- DD-MM-YYYY
- YYYY/MM/DD

### `categorize_payment_method(payment_method, ttc_value)`

Analyse la méthode de paiement et répartit le montant TTC.

**Méthodes supportées :**
- Virement bancaire (recherche "virement")
- ALMA (recherche "alma")
- Younited (recherche "younited")
- PayPal (recherche "paypal")

## API Flask

### Routes

#### `GET /`
Affiche la page d'accueil avec le formulaire de téléchargement.

#### `POST /process`
Traite les fichiers téléchargés et génère le tableau consolidé.

**Paramètres form-data :**
- `orders_file` : Fichier CSV des commandes
- `transactions_file` : Fichier CSV des transactions
- `journal_file` : Fichier CSV du journal

**Réponse :** 
- Succès : Téléchargement automatique du fichier CSV généré
- Erreur : Redirection vers la page d'accueil avec message d'erreur

### Gestion des erreurs

#### `@app.errorhandler(413)`
Gère les fichiers trop volumineux (> 16MB).

## Configuration

### Variables Flask
```python
app.secret_key = 'votre_cle_secrete_ici_changez_en_production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### Dossiers
```python
UPLOAD_FOLDER = 'uploads'      # Fichiers temporaires
OUTPUT_FOLDER = 'output'       # Fichiers générés
ALLOWED_EXTENSIONS = {'csv'}   # Extensions autorisées
```

## Sécurité

### Validation des fichiers
- Vérification de l'extension (.csv uniquement)
- Limitation de la taille (16MB max)
- Noms de fichiers sécurisés avec `secure_filename()`
- Nettoyage automatique des fichiers temporaires

### Protection contre les attaques
- Secret key pour les sessions Flask
- Validation des entrées utilisateur
- Gestion des erreurs sans exposition d'informations sensibles

## Performance

### Optimisations
- Utilisation de pandas pour le traitement efficace des données
- Agrégation des transactions pour éviter les doublons
- Jointures à gauche pour préserver toutes les commandes
- Nettoyage automatique des fichiers temporaires

### Limitations
- Taille maximale des fichiers : 16MB
- Formats supportés : CSV uniquement
- Mémoire requise proportionnelle à la taille des fichiers

## Déploiement

### Développement
```bash
python app.py
```
Accès : http://localhost:5000

### Production
Utiliser un serveur WSGI comme Gunicorn :
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Variables d'environnement
Copier `.env.example` vers `.env` et configurer :
- `SECRET_KEY` : Clé secrète unique
- `FLASK_ENV` : production
- `HOST` et `PORT` : Configuration réseau

## Tests

### Script de test automatisé
```bash
python test_app.py
```

**Tests effectués :**
- Vérification des dépendances
- Création de données de test
- Test de la logique de traitement
- Validation du format de sortie
- Statistiques du tableau généré

### Données de test
Le script crée automatiquement des fichiers de test dans `test_data/` :
- 5 commandes avec différents statuts
- 6 transactions (avec doublons pour tester l'agrégation)
- 3 entrées journal (pour tester les jointures partielles)

## Maintenance

### Logs
L'application affiche des messages de debug dans la console :
- Étapes de traitement
- Statistiques des données
- Erreurs éventuelles

### Monitoring
Surveiller :
- Espace disque (dossiers uploads/ et output/)
- Mémoire utilisée (pour gros fichiers)
- Temps de traitement

### Sauvegarde
Sauvegarder régulièrement :
- Code source
- Configuration
- Fichiers générés importants

## Dépannage

### Erreurs courantes

#### "Colonnes manquantes"
Vérifier que les noms de colonnes dans les CSV correspondent exactement.

#### "Erreur d'encodage"
S'assurer que les fichiers CSV sont encodés en UTF-8.

#### "Fichier trop volumineux"
Diviser les gros fichiers ou augmenter `MAX_CONTENT_LENGTH`.

#### "Erreur de date"
Vérifier le format des dates dans la colonne "Fulfilled at".

### Debug
Activer le mode debug Flask pour plus d'informations :
```python
app.run(debug=True)
```

## Extensions possibles

### Fonctionnalités avancées
- Support de formats Excel (.xlsx)
- Sauvegarde en base de données
- API REST pour intégration
- Traitement par lot
- Historique des traitements
- Export en différents formats

### Interface utilisateur
- Aperçu des données avant traitement
- Progress bar pour gros fichiers
- Validation en temps réel
- Mode sombre
- Responsif mobile

### Administration
- Interface d'administration
- Gestion des utilisateurs
- Logs détaillés
- Métriques de performance
