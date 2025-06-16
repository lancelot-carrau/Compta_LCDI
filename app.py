from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import os
from datetime import datetime
import tempfile
from werkzeug.utils import secure_filename
import io
import chardet
import re

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici_changez_en_production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration des dossiers
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'csv'}

# Créer les dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_encoding(file_path):
    """Détecte automatiquement l'encodage d'un fichier"""
    try:
        # Lire les premiers bytes du fichier pour détecter l'encodage
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Lire les premiers 10KB
        
        # Utiliser chardet pour détecter l'encodage
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        
        print(f"Encodage détecté pour {file_path}: {encoding} (confiance: {confidence:.2f})")
        
        # Liste des encodages fallback en ordre de préférence
        fallback_encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
        
        # Si la confiance est faible ou l'encodage n'est pas détecté, essayer les fallbacks
        if not encoding or confidence < 0.7:
            print(f"Confiance faible ({confidence:.2f}), essai des encodages fallback...")
            for fallback in fallback_encodings:
                try:
                    with open(file_path, 'r', encoding=fallback) as f:
                        f.read(1000)  # Essayer de lire le début du fichier
                    print(f"Encodage fallback réussi: {fallback}")
                    return fallback
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # Si tous les fallbacks échouent, utiliser latin-1 (qui peut lire n'importe quoi)
            print("Tous les encodages ont échoué, utilisation de latin-1")
            return 'latin-1'
        
        return encoding
        
    except Exception as e:
        print(f"Erreur lors de la détection d'encodage: {e}")
        # En cas d'erreur, essayer les encodages les plus courants
        for encoding in ['utf-8', 'windows-1252', 'iso-8859-1', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)
                print(f"Encodage de secours utilisé: {encoding}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Dernier recours
        return 'latin-1'

def safe_read_csv(file_path, separator=','):
    """Lit un fichier CSV avec détection automatique de l'encodage"""
    encoding = detect_encoding(file_path)
    
    # Essayer de lire le fichier avec l'encodage détecté
    try:
        df = pd.read_csv(file_path, sep=separator, encoding=encoding)
        print(f"Fichier lu avec succès avec l'encodage {encoding}")
        return df
    except (UnicodeDecodeError, UnicodeError) as e:
        print(f"Erreur avec l'encodage {encoding}: {e}")
        
        # Essayer d'autres encodages en cas d'échec
        fallback_encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
        
        for fallback in fallback_encodings:
            if fallback == encoding:  # Skip l’encodage déjà essayé
                continue
            try:
                df = pd.read_csv(file_path, sep=separator, encoding=fallback)
                print(f"Fichier lu avec succès avec l'encodage fallback {fallback}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Si tout échoue, lever l'erreur originale
        raise e

def normalize_column_names(df, expected_columns, file_type=""):
    """Normalise les noms de colonnes en cherchant des correspondances approximatives"""
    print(f"Colonnes disponibles dans {file_type}: {list(df.columns)}")
      # Dictionnaire de mapping pour les variantes de noms de colonnes
    column_mappings = {
        # Fichier des commandes
        'Name': ['Name', 'name', 'ORDER', 'Order', 'order', 'Nom', 'nom', 'Commande', 'commande', 'Id', 'ID', 'id', '#', 'Order ID', 'Order Id'],
        'Fulfilled at': ['Fulfilled at', 'fulfilled at', 'Date', 'date', 'Date commande', 'Date_commande', 'Created at', 'created at'],
        'Billing name': ['Billing name', 'billing name', 'Client', 'client', 'Nom client', 'Nom_client', 'Billing Name', 'billing Name'],
        'Financial Status': ['Financial Status', 'financial status', 'Status', 'status', 'Statut', 'statut'],
        'Tax 1 Value': ['Tax 1 Value', 'tax 1 value', 'TVA', 'tva', 'Tax', 'tax', 'Taxe', 'Taxes', 'taxes'],
        'Outstanding Balance': ['Outstanding Balance', 'outstanding balance', 'Balance', 'balance', 'Solde', 'solde'],
        'Payment Method': ['Payment Method', 'payment method', 'Method', 'method', 'Méthode', 'méthode'],
        
        # Fichier des transactions
        'Order': ['Order', 'order', 'Name', 'name', 'Commande', 'commande', 'Id', 'ID', 'id', 'Order ID', 'Order Id'],
        'Presentment Amount': ['Presentment Amount', 'presentment amount', 'Amount', 'amount', 'Montant', 'montant', 'TTC', 'ttc', 'Total', 'total'],
        'Fee': ['Fee', 'fee', 'Frais', 'frais', 'Commission', 'commission'],
        'Net': ['Net', 'net', 'Net Amount', 'net amount', 'Montant net', 'montant net'],
          # Fichier journal
        'Piece': ['Piece', 'piece', 'Pièce', 'pièce', 'Reference', 'reference', 'Ref', 'ref', 'Order', 'order', 'Commande', 'Id', 'ID', 'id', 'Référence externe', 'référence externe', 'Reference externe', 'reference externe', 'Externe', 'externe'],
        'Référence LMB': ['Référence LMB', 'référence lmb', 'Reference LMB', 'reference lmb', 'LMB', 'lmb', 'Ref LMB', 'ref lmb']
    }
    
    # Créer un mapping des colonnes actuelles vers les noms standardisés
    column_mapping = {}
    missing_columns = []
    
    for expected_col in expected_columns:
        found = False
        if expected_col in column_mappings:
            for variant in column_mappings[expected_col]:
                if variant in df.columns:
                    column_mapping[variant] = expected_col
                    print(f"✓ Colonne trouvée: '{variant}' -> '{expected_col}'")
                    found = True
                    break
        
        if not found:
            missing_columns.append(expected_col)
      # Afficher les colonnes manquantes
    if missing_columns:
        print(f"⚠️ Colonnes manquantes dans {file_type}: {missing_columns}")
        print("Colonnes disponibles:", list(df.columns))
        
        # Essayer une correspondance approximative pour les colonnes manquantes
        for missing_col in missing_columns:
            found_match = False
            
            # Vérification exacte des mots-clés
            keywords_mapping = {
                'Name': ['id', 'order', 'commande', 'numero', 'number'],
                'Fulfilled at': ['date', 'created', 'fulfill', 'livr'],
                'Billing name': ['billing', 'client', 'nom', 'name'],
                'Financial Status': ['status', 'statut', 'financial', 'etat'],
                'Tax 1 Value': ['tax', 'tva', 'taxe', 'impot'],
                'Outstanding Balance': ['balance', 'solde', 'outstanding', 'restant'],
                'Payment Method': ['payment', 'method', 'paiement', 'methode'],
                'Order': ['order', 'id', 'commande', 'numero', 'name'],
                'Presentment Amount': ['amount', 'total', 'montant', 'ttc', 'presentment'],
                'Fee': ['fee', 'frais', 'commission'],
                'Net': ['net', 'montant', 'amount'],                'Piece': ['piece', 'reference', 'ref', 'order', 'id', 'commande', 'externe', 'external'],
                'Référence LMB': ['lmb', 'reference', 'ref']
            }
            
            if missing_col in keywords_mapping:
                keywords = keywords_mapping[missing_col]
                for col in df.columns:
                    col_lower = col.lower()
                    # Vérifier si un des mots-clés est dans le nom de la colonne
                    if any(keyword in col_lower for keyword in keywords):
                        print(f"🔍 Correspondance trouvée: '{col}' pour '{missing_col}' (mot-clé détecté)")
                        column_mapping[col] = missing_col
                        found_match = True
                        break
            
            # Si toujours pas trouvé, essayer une correspondance plus flexible
            if not found_match:
                for col in df.columns:
                    # Vérification de similarité (contient une partie du nom)
                    if any(part.lower() in col.lower() for part in missing_col.lower().split() if len(part) > 2):
                        print(f"🔍 Correspondance approximative: '{col}' pour '{missing_col}'")
                        # Demander confirmation via un message de debug
                        print(f"   -> Voulez-vous utiliser '{col}' pour '{missing_col}' ? (automatiquement accepté)")
                        column_mapping[col] = missing_col
                        found_match = True
                        break
    
    # Renommer les colonnes
    if column_mapping:
        df = df.rename(columns=column_mapping)
        print(f"✓ Colonnes renommées: {column_mapping}")
    
    return df

def validate_required_columns(df, required_columns, file_type=""):
    """Valide que toutes les colonnes requises sont présentes"""
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        available_cols = list(df.columns)
        error_msg = f"""
        Colonnes manquantes dans {file_type}: {missing_columns}
        
        Colonnes disponibles dans le fichier: {available_cols}
        
        Vérifiez que votre fichier {file_type} contient bien les colonnes requises.
        """
        raise ValueError(error_msg)
    
    print(f"✓ Toutes les colonnes requises sont présentes dans {file_type}")
    return True

def clean_text_data(df, text_columns):
    """Nettoie les données texte en supprimant les espaces superflus"""
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

def format_date_to_french(date_str):
    """Convertit une date en format français jj/mm/aaaa"""
    try:
        if pd.isna(date_str) or str(date_str).lower() in ['nan', 'none', '']:
            return ''
        
        # Essayer différents formats de date d'entrée
        date_formats = [
            '%Y-%m-%d',           # 2024-12-25
            '%d/%m/%Y',           # 25/12/2024
            '%m/%d/%Y',           # 12/25/2024
            '%Y-%m-%d %H:%M:%S',  # 2024-12-25 10:30:00
            '%d-%m-%Y',           # 25-12-2024
            '%Y/%m/%d'            # 2024/12/25
        ]
        
        for fmt in date_formats:
            try:
                dt = pd.to_datetime(date_str, format=fmt)
                return dt.strftime('%d/%m/%Y')
            except:
                continue
                
        # Si aucun format ne marche, essayer la conversion automatique pandas
        try:
            dt = pd.to_datetime(date_str)
            return dt.strftime('%d/%m/%Y')
        except:
            return str(date_str)
            
    except Exception as e:
        print(f"Erreur lors du formatage de la date '{date_str}': {e}")
        return str(date_str) if date_str else ''

def categorize_payment_method(payment_method, ttc_value):
    """Catégorise les méthodes de paiement et retourne les montants par catégorie"""
    if pd.isna(payment_method) or pd.isna(ttc_value):
        return {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    payment_method_lower = str(payment_method).lower()
    ttc_amount = float(ttc_value) if not pd.isna(ttc_value) else 0
    
    # Initialiser toutes les catégories à 0
    result = {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    # Vérifier chaque méthode de paiement
    if 'virement' in payment_method_lower:
        result['Virement bancaire'] = ttc_amount
    elif 'alma' in payment_method_lower:
        result['ALMA'] = ttc_amount
    elif 'younited' in payment_method_lower:
        result['Younited'] = ttc_amount
    elif 'paypal' in payment_method_lower:
        result['PayPal'] = ttc_amount
    
    return result

def calculate_corrected_amounts(df_merged_final):
    """
    Calcule les montants HT, TVA, TTC avec correction logique.
    Principe: Il ne devrait pas y avoir de TVA si il n'y a pas de prix TTC.
    """
    # Récupérer les montants bruts
    ttc_amounts = df_merged_final['Presentment Amount'].fillna(0)
    tva_amounts = df_merged_final['Tax 1 Value'].fillna(0)
    
    # CORRECTION: Si pas de TTC, alors pas de TVA non plus
    # Évite les HT négatifs causés par TVA > 0 et TTC = 0
    corrected_tva = tva_amounts.copy()
    corrected_tva[ttc_amounts == 0] = 0  # Forcer TVA = 0 quand TTC = 0
    
    # Calculer HT corrigé
    corrected_ht = ttc_amounts - corrected_tva  # HT = TTC - TVA (corrigée)
    
    return {
        'HT': corrected_ht,
        'TVA': corrected_tva,
        'TTC': ttc_amounts
    }

def generate_consolidated_billing_table(orders_file, transactions_file, journal_file):
    """
    Fonction principale pour générer le tableau de facturation consolidé
    """
    try:
        print("=== DÉBUT DU TRAITEMENT ===")        # ÉTAPE 1: Chargement des fichiers CSV
        print("1. Chargement des fichiers CSV...")
        
        # Chargement du fichier des commandes (séparateur virgule)
        df_orders = safe_read_csv(orders_file, separator=',')
        print(f"   - Commandes chargées: {len(df_orders)} lignes")
        
        # Chargement du fichier des transactions (séparateur virgule)  
        df_transactions = safe_read_csv(transactions_file, separator=',')
        print(f"   - Transactions chargées: {len(df_transactions)} lignes")
        
        # Chargement du fichier journal (séparateur point-virgule)
        df_journal = safe_read_csv(journal_file, separator=';')
        print(f"   - Journal chargé: {len(df_journal)} lignes")
        
        # Vérification et normalisation des colonnes requises
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 
                               'Tax 1 Value', 'Outstanding Balance', 'Payment Method']
        required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        required_journal_cols = ['Piece', 'Référence LMB']
        
        print("\n2. Vérification et normalisation des colonnes...")
        
        # Normaliser les colonnes
        df_orders = normalize_column_names(df_orders, required_orders_cols, "fichier des commandes")
        df_transactions = normalize_column_names(df_transactions, required_transactions_cols, "fichier des transactions")
        df_journal = normalize_column_names(df_journal, required_journal_cols, "fichier journal")
          # Valider que toutes les colonnes requises sont présentes
        validate_required_columns(df_orders, required_orders_cols, "fichier des commandes")
        validate_required_columns(df_transactions, required_transactions_cols, "fichier des transactions")
        validate_required_columns(df_journal, required_journal_cols, "fichier journal")
        
        print("3. Nettoyage et formatage des données...")
        
        # Nettoyage des colonnes de texte utilisées comme clés de jointure
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name', 'Financial Status', 'Payment Method'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        # Formatage des dates - conversion en format français jj/mm/aaaa
        df_orders['Fulfilled at'] = df_orders['Fulfilled at'].apply(format_date_to_french)
          # Formatage des colonnes monétaires en type numérique
        monetary_cols_orders = ['Tax 1 Value', 'Outstanding Balance']
        monetary_cols_transactions = ['Presentment Amount', 'Fee', 'Net']
        
        for col in monetary_cols_orders:
            if col in df_orders.columns:
                df_orders[col] = pd.to_numeric(df_orders[col], errors='coerce').fillna(0)
        
        for col in monetary_cols_transactions:
            if col in df_transactions.columns:
                df_transactions[col] = pd.to_numeric(df_transactions[col], errors='coerce').fillna(0)
        
        print("3.5. Agrégation des commandes pour éviter les doublons...")
        
        # IMPORTANT: Grouper les commandes par Name pour éviter les doublons
        # (cas où il y a plusieurs lignes de produits par commande)
        print(f"   - Nombre de lignes avant agrégation des commandes: {len(df_orders)}")
        
        # Colonnes à garder telles quelles (prendre la première valeur)
        first_value_cols = ['Fulfilled at', 'Billing name', 'Financial Status', 'Payment Method']
        
        # Colonnes à sommer (montants, quantités, etc.)
        sum_cols = ['Tax 1 Value', 'Outstanding Balance']
        
        # Détecter automatiquement d'autres colonnes numériques qui pourraient nécessiter une sommation
        for col in df_orders.columns:
            if col not in first_value_cols and col != 'Name':
                # Si c'est une colonne numérique, on la somme
                if df_orders[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df_orders[col]):
                    if col not in sum_cols:
                        sum_cols.append(col)
                        print(f"   - Colonne numérique détectée pour sommation: {col}")
                # Sinon, on prend la première valeur
                elif col not in first_value_cols:
                    first_value_cols.append(col)
        
        # Préparer les opérations d'agrégation
        agg_operations = {}
        
        # Pour les colonnes de texte/dates, prendre la première valeur
        for col in first_value_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'first'
          # Pour les colonnes monétaires, faire la somme
        for col in sum_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'sum'
        
        # Grouper par Name (identifiant unique de la commande)
        if agg_operations:
            df_orders_aggregated = df_orders.groupby('Name').agg(agg_operations).reset_index()
        else:
            # Si pas d'opérations d'agrégation, juste dédupliquer
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
        
        print(f"   - Nombre de lignes après agrégation des commandes: {len(df_orders_aggregated)}")
        
        # Note: Un même client peut avoir plusieurs commandes distinctes
        # Chaque commande doit apparaître sur une ligne séparée
        
        # Remplacer df_orders par la version agrégée
        df_orders = df_orders_aggregated
        
        # ÉTAPE 2: Agrégation des transactions par commande
        print("4. Agrégation des transactions par commande...")
        
        # Grouper par Order et sommer les montants pour éviter les doublons
        df_transactions_aggregated = df_transactions.groupby('Order').agg({
            'Presentment Amount': 'sum',
            'Fee': 'sum',
            'Net': 'sum'
        }).reset_index()
        
        print(f"   - Transactions après agrégation: {len(df_transactions_aggregated)} lignes")
          # ÉTAPE 3: Fusion des DataFrames
        print("5. Fusion des DataFrames...")
        
        # Première fusion: Commandes + Transactions agrégées (jointure à gauche)
        df_merged_step1 = pd.merge(df_orders, df_transactions_aggregated, 
                                  left_on='Name', right_on='Order', how='left')
        print(f"   - Après fusion commandes-transactions: {len(df_merged_step1)} lignes")
        
        # Diagnostic avant fusion avec journal
        print("   - Diagnostic avant fusion avec journal:")
        print(f"     * Commandes uniques dans df_merged_step1: {df_merged_step1['Name'].nunique()} ({list(df_merged_step1['Name'].unique()[:5])}...)")
        print(f"     * Références uniques dans journal: {df_journal['Piece'].nunique()} ({list(df_journal['Piece'].unique()[:5])}...)")
          # Vérifier les correspondances
        commandes_dans_journal = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
        print(f"     * Commandes qui ont une correspondance dans le journal: {commandes_dans_journal}/{len(df_merged_step1)}")
          # Deuxième fusion: Résultat + Journal (jointure à gauche)
        # TOUJOURS essayer d'améliorer les correspondances avec normalisation
        print("DEBUG: Début de la logique de fusion avec journal")
        print(f"DEBUG: commandes_dans_journal = {commandes_dans_journal}, len(df_merged_step1) = {len(df_merged_step1)}")
        if commandes_dans_journal < len(df_merged_step1):  # Si pas 100% de correspondances
            print("     🔧 Application de la normalisation des références...")
            df_merged_step1_improved = improve_journal_matching(df_merged_step1, df_journal)
            
            # Utiliser les données améliorées
            df_merged_final = df_merged_step1_improved
        else:
            print("     ✅ Toutes les correspondances trouvées, fusion standard")
            # Fusion standard si toutes les correspondances sont déjà trouvées
            df_merged_final = pd.merge(df_merged_step1, df_journal, 
                                      left_on='Name', right_on='Piece', how='left')
        print(f"   - Après fusion avec journal: {len(df_merged_final)} lignes")
        
        # Diagnostic après fusion
        ref_lmb_non_nulles = df_merged_final['Référence LMB'].notna().sum()
        print(f"   - Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_merged_final)} ({ref_lmb_non_nulles/len(df_merged_final)*100:.1f}%)")
          # ÉTAPE 4: Création du tableau final avec les 16 colonnes
        print("6. Création du tableau final...")
        
        df_final = pd.DataFrame()
        
        # Colonnes du tableau final dans l'ordre requis
        df_final['Centre de profit'] = 'lcdi.fr'  # Valeur statique
        df_final['Réf.WEB'] = df_merged_final['Name']
        df_final['Réf. LMB'] = df_merged_final['Référence LMB'].fillna('')
        df_final['Date Facture'] = df_merged_final['Fulfilled at']
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('')
        df_final['Client'] = df_merged_final['Billing name'].fillna('')
        
        # Calculs des montants
        corrected_amounts = calculate_corrected_amounts(df_merged_final)
        
        df_final['HT'] = corrected_amounts['HT']
        df_final['TVA'] = corrected_amounts['TVA']
        df_final['TTC'] = corrected_amounts['TTC']
        df_final['reste'] = df_merged_final['Outstanding Balance'].fillna(0)
        df_final['Shopify'] = df_merged_final['Net'].fillna(0)
        df_final['Frais de commission'] = df_merged_final['Fee'].fillna(0)
        
        # Traitement des méthodes de paiement
        print("7. Traitement des méthodes de paiement...")
        payment_categorization = df_merged_final.apply(
            lambda row: categorize_payment_method(row['Payment Method'], row['Presentment Amount']), 
            axis=1
        )
        
        df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]
        df_final['Younited'] = [pm['Younited'] for pm in payment_categorization]
        df_final['PayPal'] = [pm['PayPal'] for pm in payment_categorization]
          # NETTOYAGE FINAL: Indiquer les informations manquantes
        print("8. Nettoyage final des données...")
        
        # Appliquer les indicateurs d'informations manquantes
        df_final = fill_missing_data_indicators(df_final, df_merged_final)
        
        # S'assurer que "Centre de profit" est toujours "lcdi.fr" (forcer après toutes les fusions)
        df_final['Centre de profit'] = 'lcdi.fr'
        
        # Indicateurs de données manquantes
        df_final = fill_missing_data_indicators(df_final, df_merged_final)
        
        print(f"=== TRAITEMENT TERMINÉ ===")
        print(f"Tableau final généré avec {len(df_final)} lignes et {len(df_final.columns)} colonnes")
        
        return df_final
        
    except Exception as e:
        print(f"ERREUR lors du traitement: {str(e)}")
        raise e

def process_dataframes_directly(df_orders, df_transactions, df_journal):
    """
    Fonction auxiliaire pour traiter directement des DataFrames (utilisée pour les tests)
    """
    try:
        print("=== DÉBUT DU TRAITEMENT (DataFrames) ===")
        
        # ÉTAPE 1: Les DataFrames sont déjà chargés
        print("1. DataFrames déjà chargés...")
        print(f"   - Commandes: {len(df_orders)} lignes")
        print(f"   - Transactions: {len(df_transactions)} lignes")
        print(f"   - Journal: {len(df_journal)} lignes")
          # ÉTAPE 2: Vérification et normalisation des colonnes
        print("2. Vérification et normalisation des colonnes...")
        
        # Normaliser les noms de colonnes pour les commandes
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method']
        df_orders = normalize_column_names(df_orders, required_orders_cols, 'commandes')
        validate_required_columns(df_orders, required_orders_cols, "fichier des commandes")
        
        # Normaliser les noms de colonnes pour les transactions
        required_trans_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        df_transactions = normalize_column_names(df_transactions, required_trans_cols, 'transactions')
        validate_required_columns(df_transactions, required_trans_cols, "fichier des transactions")
        
        # Normaliser les noms de colonnes pour le journal
        required_journal_cols = ['Piece', 'Référence LMB']
        df_journal = normalize_column_names(df_journal, required_journal_cols, 'journal')
        validate_required_columns(df_journal, required_journal_cols, "fichier journal")
          # ÉTAPE 3: Nettoyage et formatage des données
        print("3. Nettoyage et formatage des données...")
        
        # Nettoyage des colonnes de texte utilisées comme clés de jointure
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name', 'Financial Status', 'Payment Method'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        # Formatage des dates - conversion en format français jj/mm/aaaa
        df_orders['Fulfilled at'] = df_orders['Fulfilled at'].apply(format_date_to_french)
        
        # Formatage des colonnes monétaires en type numérique
        monetary_cols_orders = ['Tax 1 Value', 'Outstanding Balance']
        monetary_cols_transactions = ['Presentment Amount', 'Fee', 'Net']
        
        for col in monetary_cols_orders:
            if col in df_orders.columns:
                df_orders[col] = pd.to_numeric(df_orders[col], errors='coerce').fillna(0)
        
        for col in monetary_cols_transactions:
            if col in df_transactions.columns:
                df_transactions[col] = pd.to_numeric(df_transactions[col], errors='coerce').fillna(0)
        
        # ÉTAPE 3.5: Agrégation des commandes pour éviter les doublons par commande
        print("3.5. Agrégation des commandes pour éviter les doublons...")
        print(f"   - Nombre de lignes avant agrégation des commandes: {len(df_orders)}")
        
        # Définir les colonnes pour l'agrégation
        first_cols = ['Fulfilled at', 'Billing name', 'Financial Status', 'Payment Method', 'Email', 'Lineitem name']
        sum_cols = ['Tax 1 Value', 'Outstanding Balance']
        
        # Construire le dictionnaire d'opérations d'agrégation
        agg_operations = {}
        
        # Détecter automatiquement les colonnes numériques pour la sommation
        for col in df_orders.columns:
            if col not in first_cols and col != 'Name':  # Name est la clé de groupement
                if df_orders[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df_orders[col]):
                    if col not in sum_cols:
                        sum_cols.append(col)
                        print(f"   - Colonne numérique détectée pour sommation: {col}")
                elif col not in first_cols:
                    first_cols.append(col)
        
        # Configurer les opérations d'agrégation
        for col in first_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'first'
        
        # Pour les colonnes monétaires, faire la somme
        for col in sum_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'sum'
        
        # Grouper par Name (identifiant unique de la commande)
        if agg_operations:
            df_orders_aggregated = df_orders.groupby('Name').agg(agg_operations).reset_index()
        else:
            # Si pas d'opérations d'agrégation, juste dédupliquer
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
        
        print(f"   - Nombre de lignes après agrégation des commandes: {len(df_orders_aggregated)}")
        
        # Note: Un même client peut avoir plusieurs commandes distinctes
        # Chaque commande doit apparaître sur une ligne séparée
        
        # Remplacer df_orders par la version agrégée
        df_orders = df_orders_aggregated
        
        # ÉTAPE 4: Agrégation des transactions par commande
        print("4. Agrégation des transactions par commande...")
        
        # Grouper par Order et sommer les montants pour éviter les doublons
        df_transactions_aggregated = df_transactions.groupby('Order').agg({
            'Presentment Amount': 'sum',
            'Fee': 'sum',
            'Net': 'sum'
        }).reset_index()
        
        print(f"   - Transactions après agrégation: {len(df_transactions_aggregated)} lignes")
          # ÉTAPE 5: Fusion des DataFrames
        print("5. Fusion des DataFrames...")
        
        # Première fusion: Commandes + Transactions agrégées (jointure à gauche)
        df_merged_step1 = pd.merge(df_orders, df_transactions_aggregated, 
                                  left_on='Name', right_on='Order', how='left')
        print(f"   - Après fusion commandes-transactions: {len(df_merged_step1)} lignes")
        
        # Diagnostic avant fusion avec journal
        print("   - Diagnostic avant fusion avec journal:")
        print(f"     * Commandes uniques dans df_merged_step1: {df_merged_step1['Name'].nunique()} ({list(df_merged_step1['Name'].unique()[:5])}...)")
        print(f"     * Références uniques dans journal: {df_journal['Piece'].nunique()} ({list(df_journal['Piece'].unique()[:5])}...)")
          # Vérifier les correspondances
        commandes_dans_journal = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
        print(f"     * Commandes qui ont une correspondance dans le journal: {commandes_dans_journal}/{len(df_merged_step1)}")
        
        # Deuxième fusion: Résultat + Journal (jointure à gauche)
        # TOUJOURS essayer d'améliorer les correspondances avec normalisation
        print("DEBUG: Version 2 - Début de la logique de fusion avec journal")
        print(f"DEBUG: Version 2 - commandes_dans_journal = {commandes_dans_journal}, len(df_merged_step1) = {len(df_merged_step1)}")
        if commandes_dans_journal < len(df_merged_step1):  # Si pas 100% de correspondances
            print("     🔧 [V2] Application de la normalisation des références...")
            df_merged_step1_improved = improve_journal_matching(df_merged_step1, df_journal)
            
            # Utiliser les données améliorées
            df_merged_final = df_merged_step1_improved
        else:
            print("     ✅ [V2] Toutes les correspondances trouvées, fusion standard")
            # Fusion standard si toutes les correspondances sont déjà trouvées
            df_merged_final = pd.merge(df_merged_step1, df_journal, 
                                      left_on='Name', right_on='Piece', how='left')
        print(f"   - Après fusion avec journal: {len(df_merged_final)} lignes")
        
        # Diagnostic après fusion
        ref_lmb_non_nulles = df_merged_final['Référence LMB'].notna().sum()
        print(f"   - Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_merged_final)} ({ref_lmb_non_nulles/len(df_merged_final)*100:.1f}%)")
          # ÉTAPE 6: Création du tableau final avec les 16 colonnes
        print("6. Création du tableau final...")
        
        df_final = pd.DataFrame()
        
        # Colonnes du tableau final dans l'ordre requis
        df_final['Centre de profit'] = 'lcdi.fr'  # Valeur statique
        df_final['Réf.WEB'] = df_merged_final['Name']
        df_final['Réf. LMB'] = df_merged_final['Référence LMB'].fillna('')
        df_final['Date Facture'] = df_merged_final['Fulfilled at']
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('')
        df_final['Client'] = df_merged_final['Billing name'].fillna('')
        
        # Calculs des montants
        corrected_amounts = calculate_corrected_amounts(df_merged_final)
        
        df_final['HT'] = corrected_amounts['HT']
        df_final['TVA'] = corrected_amounts['TVA']
        df_final['TTC'] = corrected_amounts['TTC']
        df_final['reste'] = df_merged_final['Outstanding Balance'].fillna(0)
        df_final['Shopify'] = df_merged_final['Net'].fillna(0)
        df_final['Frais de commission'] = df_merged_final['Fee'].fillna(0)
        
        # Traitement des méthodes de paiement
        print("7. Traitement des méthodes de paiement...")
        payment_categorization = df_merged_final.apply(
            lambda row: categorize_payment_method(row['Payment Method'], row['Presentment Amount']), 
            axis=1
        )
        
        df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]
        df_final['Younited'] = [pm['Younited'] for pm in payment_categorization]
        df_final['PayPal'] = [pm['PayPal'] for pm in payment_categorization]
        
        # ÉTAPE 8: Nettoyage final et création du DataFrame final
        print("8. Nettoyage final des données...")
        
        # Remplacer les NaN par des chaînes vides pour les colonnes texte
        text_columns = ['Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client']
        for col in text_columns:
            df_final[col] = df_final[col].fillna('')
        
        # Arrondir les montants à 2 décimales
        numeric_columns = ['HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission', 
                          'Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        for col in numeric_columns:
            df_final[col] = df_final[col].round(2)
        
        # Créer le DataFrame final avec les colonnes dans l'ordre spécifié
        ordered_columns = [
            'Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client',
            'HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission',
            'Virement bancaire', 'ALMA', 'Younited', 'PayPal'
        ]
        
        result_df = df_final[ordered_columns].copy()
        
        # Renommer les colonnes pour correspondre aux attentes des tests
        result_df.rename(columns={
            'Client': 'Nom',
            'Réf.WEB': 'Référence'
        }, inplace=True)
        
        print("=== TRAITEMENT TERMINÉ ===")
        print(f"Tableau final généré avec {len(result_df)} lignes et {len(result_df.columns)} colonnes")
        
        return result_df
        
    except Exception as e:
        print(f"ERREUR lors du traitement: {e}")
        raise e

def process_dataframes_with_normalization(df_orders, df_transactions, df_journal):
    """
    Version améliorée qui utilise toujours la normalisation des références
    """
    try:
        print("=== DÉBUT DU TRAITEMENT AVEC NORMALISATION ===")
        
        # ÉTAPE 1: Les DataFrames sont déjà chargés
        print("1. DataFrames déjà chargés...")
        print(f"   - Commandes: {len(df_orders)} lignes")
        print(f"   - Transactions: {len(df_transactions)} lignes")
        print(f"   - Journal: {len(df_journal)} lignes")
          # ÉTAPE 2: Vérification et normalisation des colonnes
        print("2. Vérification et normalisation des colonnes...")
        
        # Définir les colonnes requises
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method']
        required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        required_journal_cols = ['Piece', 'Référence LMB']
        
        # Normaliser les noms de colonnes pour les commandes
        df_orders = normalize_column_names(df_orders, 'commandes')
        validate_required_columns(df_orders, required_orders_cols, "fichier des commandes")
        
        # Normaliser les noms de colonnes pour les transactions
        df_transactions = normalize_column_names(df_transactions, 'transactions')
        validate_required_columns(df_transactions, required_transactions_cols, "fichier des transactions")
        
        # Normaliser les noms de colonnes pour le journal
        df_journal = normalize_column_names(df_journal, 'journal')
        validate_required_columns(df_journal, required_journal_cols, "fichier journal")
        
        # ÉTAPE 3: Nettoyage et formatage des données
        print("3. Nettoyage et formatage des données...")
        
        # Nettoyage des colonnes de texte utilisées comme clés de jointure
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name', 'Financial Status', 'Payment Method'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        # Formatage des dates - conversion en format français jj/mm/aaaa
        df_orders['Fulfilled at'] = df_orders['Fulfilled at'].apply(format_date_to_french)
        
        # Formatage des colonnes monétaires en type numérique
        monetary_cols_orders = ['Tax 1 Value', 'Outstanding Balance']
        monetary_cols_transactions = ['Presentment Amount', 'Fee', 'Net']
        
        for col in monetary_cols_orders:
            if col in df_orders.columns:
                df_orders[col] = pd.to_numeric(df_orders[col], errors='coerce').fillna(0)
        
        for col in monetary_cols_transactions:
            if col in df_transactions.columns:
                df_transactions[col] = pd.to_numeric(df_transactions[col], errors='coerce').fillna(0)
        
        # ÉTAPE 3.5: Agrégation des commandes pour éviter les doublons
        print("3.5. Agrégation des commandes pour éviter les doublons...")
        print(f"   - Nombre de lignes avant agrégation des commandes: {len(df_orders)}")
        
        # Définir les colonnes pour l'agrégation
        first_cols = ['Fulfilled at', 'Billing name', 'Financial Status', 'Payment Method', 'Email', 'Lineitem name']
        sum_cols = ['Tax 1 Value', 'Outstanding Balance']
        
        # Construire le dictionnaire d'opérations d'agrégation
        agg_operations = {}
        
        # Détecter automatiquement les colonnes numériques pour la sommation
        for col in df_orders.columns:
            if col not in first_cols and col != 'Name':  # Name est la clé de groupement
                if df_orders[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df_orders[col]):
                    if col not in sum_cols:
                        sum_cols.append(col)
                        print(f"   - Colonne numérique détectée pour sommation: {col}")
                elif col not in first_cols:
                    first_cols.append(col)
        
        # Configurer les opérations d'agrégation
        for col in first_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'first'
        
        # Pour les colonnes monétaires, faire la somme
        for col in sum_cols:
            if col in df_orders.columns:
                agg_operations[col] = 'sum'
        
        # Grouper par Name (identifiant unique de la commande)
        if agg_operations:
            df_orders_aggregated = df_orders.groupby('Name').agg(agg_operations).reset_index()
        else:
            # Si pas d'opérations d'agrégation, juste dédupliquer
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
        
        print(f"   - Nombre de lignes après agrégation des commandes: {len(df_orders_aggregated)}")
        
        # Note: Un même client peut avoir plusieurs commandes distinctes
        # Chaque commande doit apparaître sur une ligne séparée
        
        # Remplacer df_orders par la version agrégée
        df_orders = df_orders_aggregated
        
        # ÉTAPE 4: Agrégation des transactions par commande
        print("4. Agrégation des transactions par commande...")
        
        # Grouper par Order et sommer les montants pour éviter les doublons
        df_transactions_aggregated = df_transactions.groupby('Order').agg({
            'Presentment Amount': 'sum',
            'Fee': 'sum',
            'Net': 'sum'
        }).reset_index()
        
        print(f"   - Transactions après agrégation: {len(df_transactions_aggregated)} lignes")
          # ÉTAPE 5: Fusion des DataFrames
        print("5. Fusion des DataFrames...")
        
        # Première fusion: Commandes + Transactions agrégées (jointure à gauche)
        df_merged_step1 = pd.merge(df_orders, df_transactions_aggregated, 
                                  left_on='Name', right_on='Order', how='left')
        print(f"   - Après fusion commandes-transactions: {len(df_merged_step1)} lignes")
        
        # Diagnostic avant fusion avec journal
        print("   - Diagnostic avant fusion avec journal:")
        print(f"     * Commandes uniques dans df_merged_step1: {df_merged_step1['Name'].nunique()} ({list(df_merged_step1['Name'].unique()[:5])}...)")
        print(f"     * Références uniques dans journal: {df_journal['Piece'].nunique()} ({list(df_journal['Piece'].unique()[:5])}...)")
        
        # Vérifier les correspondances
        commandes_dans_journal = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
        print(f"     * Commandes qui ont une correspondance dans le journal: {commandes_dans_journal}/{len(df_merged_step1)}")
        
        # TOUJOURS essayer d'améliorer les correspondances avec normalisation
        if commandes_dans_journal < len(df_merged_step1):  # Si pas 100% de correspondances
            print("     🔧 Application de la normalisation des références...")
            df_merged_step1_improved = improve_journal_matching(df_merged_step1, df_journal)
            
            # Utiliser les données améliorées
            df_merged_final = df_merged_step1_improved
        else:
            print("     ✅ Toutes les correspondances trouvées, fusion standard")
            # Fusion standard si toutes les correspondances sont déjà trouvées
            df_merged_final = pd.merge(df_merged_step1, df_journal, 
                                      left_on='Name', right_on='Piece', how='left')
        
        print(f"   - Après fusion avec journal: {len(df_merged_final)} lignes")
        
        # Diagnostic après fusion
        ref_lmb_non_nulles = df_merged_final['Référence LMB'].notna().sum()
        print(f"   - Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_merged_final)} ({ref_lmb_non_nulles/len(df_merged_final)*100:.1f}%)")
          # ÉTAPE 6: Création du tableau final avec les 16 colonnes
        print("6. Création du tableau final...")
        
        df_final = pd.DataFrame()
        
        # Colonnes du tableau final dans l'ordre requis
        df_final['Centre de profit'] = 'lcdi.fr'  # Valeur statique
        df_final['Réf.WEB'] = df_merged_final['Name']
        df_final['Réf. LMB'] = df_merged_final['Référence LMB'].fillna('')
        df_final['Date Facture'] = df_merged_final['Fulfilled at']
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('')
        df_final['Client'] = df_merged_final['Billing name'].fillna('')
        
        # Calculs des montants
        corrected_amounts = calculate_corrected_amounts(df_merged_final)
        
        df_final['HT'] = corrected_amounts['HT']
        df_final['TVA'] = corrected_amounts['TVA']
        df_final['TTC'] = corrected_amounts['TTC']
        df_final['reste'] = df_merged_final['Outstanding Balance'].fillna(0)
        df_final['Shopify'] = df_merged_final['Net'].fillna(0)
        df_final['Frais de commission'] = df_merged_final['Fee'].fillna(0)
        
        # Traitement des méthodes de paiement
        print("7. Traitement des méthodes de paiement...")
        payment_categorization = df_merged_final.apply(
            lambda row: categorize_payment_method(row['Payment Method'], row['Presentment Amount']), 
            axis=1
        )
        
        df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]
        df_final['Younited'] = [pm['Younited'] for pm in payment_categorization]
        df_final['PayPal'] = [pm['PayPal'] for pm in payment_categorization]
        
        # ÉTAPE 8: Nettoyage final et création du DataFrame final
        print("8. Nettoyage final des données...")
        
        # Remplacer les NaN par des chaînes vides pour les colonnes texte
        text_columns = ['Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client']
        for col in text_columns:
            df_final[col] = df_final[col].fillna('')
        
        # Arrondir les montants à 2 décimales
        numeric_columns = ['HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission', 
                          'Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        for col in numeric_columns:
            df_final[col] = df_final[col].round(2)
        
        # Créer le DataFrame final avec les colonnes dans l'ordre spécifié
        ordered_columns = [
            'Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client',
            'HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission',
            'Virement bancaire', 'ALMA', 'Younited', 'PayPal'
        ]
        
        result_df = df_final[ordered_columns].copy()
        
        # Renommer les colonnes pour correspondre aux attentes des tests
        result_df.rename(columns={
            'Client': 'Nom',
            'Réf.WEB': 'Référence'
        }, inplace=True)
        
        print("=== TRAITEMENT TERMINÉ ===")
        print(f"Tableau final généré avec {len(result_df)} lignes et {len(result_df.columns)} colonnes")
        
        return result_df
        
    except Exception as e:
        print(f"ERREUR lors du traitement: {e}")
        raise e

def normalize_reference_format(ref):
    """
    Normalise le format des références pour améliorer les correspondances
    Gère les formats LCDI-XXXX, #LCDI-XXXX, #lcdi-xxxx, etc.
    """
    if pd.isna(ref) or ref == '':
        return ref
    
    ref_str = str(ref).strip().upper()
    
    # Pattern pour capturer LCDI-XXXX avec ou sans #
    lcdi_pattern = r'#?LCDI[-_]?(\d+)'
    matches = re.findall(lcdi_pattern, ref_str)
    
    if matches:
        # Retourner au format standard #LCDI-XXXX
        return f"#LCDI-{matches[0]}"
    
    # Si pas de pattern LCDI, essayer de capturer juste les chiffres
    numbers = re.findall(r'\d+', ref_str)
    if numbers:
        return f"#{numbers[0]}"
    
    return ref_str

def normalize_reference_with_multiples(ref):
    """
    Normalise les références en gérant les cas de références multiples
    Ex: "LCDI-1020 LCDI-1021" -> ["#LCDI-1020", "#LCDI-1021"]
    """
    if pd.isna(ref) or ref == '':
        return []
    
    ref_str = str(ref).strip().upper()
    
    # Pattern pour capturer toutes les références LCDI-XXXX
    lcdi_pattern = r'#?LCDI[-_]?(\d+)'
    matches = re.findall(lcdi_pattern, ref_str)
    
    if matches:
        return [f"#LCDI-{match}" for match in matches]
    
    # Si pas de pattern LCDI, essayer de capturer juste les chiffres
    numbers = re.findall(r'\d+', ref_str)
    if numbers:
        return [f"#{num}" for num in numbers]
    
    return [ref_str]

def improve_journal_matching(df_orders, df_journal):
    """
    Améliore les correspondances entre commandes et journal en normalisant les références
    Gère les cas de références multiples dans le journal
    """
    print("   - Amélioration des correspondances avec le journal...")
    
    # Sauvegarder les DataFrames originaux
    df_orders_copy = df_orders.copy()
    df_journal_expanded = []
    
    # Normaliser les références des commandes
    df_orders_copy['Name_normalized'] = df_orders_copy['Name'].apply(normalize_reference_format)
    
    # Traiter le journal en gérant les références multiples
    for idx, row in df_journal.iterrows():
        refs = normalize_reference_with_multiples(row['Piece'])
        
        if len(refs) > 1:
            # Cas de références multiples : créer une ligne pour chaque référence
            for ref in refs:
                new_row = row.copy()
                new_row['Piece_normalized'] = ref
                df_journal_expanded.append(new_row)
        else:
            # Cas normal : une seule référence
            new_row = row.copy()
            new_row['Piece_normalized'] = refs[0] if refs else normalize_reference_format(row['Piece'])
            df_journal_expanded.append(new_row)
    
    df_journal_copy = pd.DataFrame(df_journal_expanded)
    
    print(f"     - Journal élargi : {len(df_journal)} -> {len(df_journal_copy)} lignes")
    print(f"     - Échantillon des références normalisées (commandes) : {df_orders_copy['Name_normalized'].head(5).tolist()}")
    print(f"     - Échantillon des références normalisées (journal) : {df_journal_copy['Piece_normalized'].head(5).tolist()}")
      # Fusionner sur les références normalisées
    # Exclure la colonne "Centre de profit" du journal pour éviter de l'écraser avec des NaN
    journal_cols_for_merge = [col for col in df_journal_copy.columns if col != 'Centre de profit']
    df_journal_for_merge = df_journal_copy[journal_cols_for_merge]
    
    df_merged = pd.merge(
        df_orders_copy, 
        df_journal_for_merge, 
        left_on='Name_normalized', 
        right_on='Piece_normalized', 
        how='left'
    )
    
    # Statistiques des correspondances
    correspondances_trouvees = df_merged['Référence LMB'].notna().sum()
    total_commandes = len(df_orders_copy)
    print(f"     - Correspondances trouvées : {correspondances_trouvees}/{total_commandes} ({correspondances_trouvees/total_commandes*100:.1f}%)")
    
    # Diagnostics
    correspondances_originales = df_orders['Name'].isin(df_journal['Piece']).sum()
    correspondances_normalisees = df_orders_copy['Name_normalized'].isin(df_journal_copy['Piece_normalized']).sum()
    
    print(f"     * Correspondances originales: {correspondances_originales}/{len(df_orders)}")
    print(f"     * Correspondances après normalisation: {correspondances_normalisees}/{len(df_orders)}")
    
    if correspondances_normalisees > correspondances_originales:
        print(f"     ✅ Amélioration: +{correspondances_normalisees - correspondances_originales} correspondances")
        
        # Effectuer la jointure avec les références normalisées
        df_merged = pd.merge(df_orders_copy, df_journal_copy,
                           left_on='Name_normalized', right_on='Piece_normalized', 
                           how='left', suffixes=('', '_journal'))
        
        # Garder les colonnes importantes du journal
        for col in df_journal.columns:
            if col not in df_orders.columns:
                df_orders[col] = df_merged[col]
        
        return df_orders
    else:
        print("     ⚠️ Pas d'amélioration, utilisation de la méthode standard")
        return df_orders

def fill_missing_data_indicators(df_final, df_merged_final):
    """
    Ajoute une colonne de statut simple : COMPLET ou INCOMPLET
    Laisse les cellules vides sans marqueur (le formatage conditionnel sera appliqué sur les cellules vides/NaN).
    """
    # 1. Nettoyer les colonnes numériques: remplacer NaN par 0
    numeric_columns = ['HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission',
                      'Virement bancaire', 'ALMA', 'Younited', 'PayPal']
    
    for col in numeric_columns:
        if col in df_final.columns:
            df_final[col] = df_final[col].fillna(0)
    
    # 2. Déterminer le statut : COMPLET ou INCOMPLET
    has_transaction = df_merged_final['Presentment Amount'].fillna(0) > 0
    
    status_info = []
    for idx, row in df_final.iterrows():
        # Une ligne est COMPLÈTE si elle a :
        # - Une référence LMB (pas vide/NaN)
        # - Une transaction (TTC > 0)  
        # - Une date de facture (pas vide/NaN)
        
        has_lmb = pd.notna(row['Réf. LMB']) and str(row['Réf. LMB']).strip() != ''
        has_ttc = has_transaction.iloc[idx] if idx < len(has_transaction) else False
        has_date = pd.notna(row['Date Facture']) and str(row['Date Facture']).strip() != ''
        
        if has_lmb and has_ttc and has_date:
            status_info.append("COMPLET")
        else:
            status_info.append("INCOMPLET")
    
    # 3. Ajouter la colonne de statut
    df_final['Statut'] = status_info
    
    return df_final

@app.route('/')
def index():
    """Page d'accueil avec le formulaire de téléchargement"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    """Traite les fichiers uploadés et génère le tableau consolidé"""
    try:
        # Vérification de la présence de tous les fichiers
        required_files = ['orders_file', 'transactions_file', 'journal_file']
        files = {}
        
        for file_key in required_files:
            if file_key not in request.files:
                flash(f'Le fichier {file_key.replace("_", " ")} est manquant.')
                return redirect(url_for('index'))
            
            file = request.files[file_key]
            if file.filename == '':
                flash(f'Veuillez sélectionner un fichier pour {file_key.replace("_", " ")}.')
                return redirect(url_for('index'))
            
            if not allowed_file(file.filename):
                flash(f'Le fichier {file.filename} doit être un fichier CSV.')
                return redirect(url_for('index'))
            
            files[file_key] = file
        
        # Sauvegarde temporaire des fichiers
        temp_paths = {}
        try:
            for file_key, file in files.items():
                filename = secure_filename(file.filename)
                temp_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(temp_path)
                temp_paths[file_key] = temp_path
            
            # Génération du tableau consolidé
            df_result = generate_consolidated_billing_table(
                temp_paths['orders_file'],                temp_paths['transactions_file'], 
                temp_paths['journal_file']
            )
            
            # Création du fichier de sortie avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'tableau_facturation_final_{timestamp}.csv'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
              # Sauvegarde avec formatage conditionnel (Excel) ou CSV si pas possible
            final_path, is_excel = save_with_conditional_formatting(df_result, output_path)
            
            if is_excel:
                flash(f'Tableau Excel généré avec succès! {len(df_result)} lignes traitées. Les informations manquantes sont en rouge clair.', 'success')
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                download_filename = os.path.basename(final_path)
            else:
                flash(f'Tableau CSV généré avec succès! {len(df_result)} lignes traitées.', 'success')
                mimetype = 'text/csv'
                download_filename = os.path.basename(final_path)
            
            # Téléchargement automatique du fichier
            return send_file(
                final_path, 
                as_attachment=True, 
                download_name=download_filename,
                mimetype=mimetype
            )
            
        finally:
            # Nettoyage des fichiers temporaires
            for temp_path in temp_paths.values():
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        
    except Exception as e:
        flash(f'Erreur lors du traitement: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    """Gestion des fichiers trop volumineux"""
    flash('Le fichier est trop volumineux. Taille maximale: 16MB.', 'error')
    return redirect(url_for('index'))

def save_with_conditional_formatting(df_result, output_path):
    """
    Sauvegarde le DataFrame en Excel avec formatage conditionnel rouge clair 
    pour les cellules vides/manquantes
    """
    try:
        # Essayer d'importer openpyxl pour Excel
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill
        from openpyxl.utils.dataframe import dataframe_to_rows
        import pandas as pd
        
        # Créer un nouveau classeur Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Tableau Facturation"
        
        # Ajouter les données du DataFrame
        for r in dataframe_to_rows(df_result, index=False, header=True):
            ws.append(r)        # Définir les styles de formatage
        # Rouge plus sombre pour les cellules manquantes et INCOMPLET
        missing_fill = PatternFill(start_color='FFB3B3', end_color='FFB3B3', fill_type='solid')  # Rouge plus sombre
        incomplete_fill = PatternFill(start_color='FFB3B3', end_color='FFB3B3', fill_type='solid')  # Même rouge
        # Vert clair pour COMPLET
        complete_fill = PatternFill(start_color='B3FFB3', end_color='B3FFB3', fill_type='solid')  # Vert clair
        
        # Colonnes où vérifier les données manquantes (exclure les colonnes numériques qui sont à 0)
        important_columns = ['Réf. LMB', 'Date Facture', 'Etat', 'Client']
        header_row = [cell.value for cell in ws[1]]
          # Trouver l'index de la colonne Statut
        statut_col_idx = None
        for idx, col_name in enumerate(header_row):
            if col_name == 'Statut':
                statut_col_idx = idx
                break
        
        # Appliquer le formatage aux cellules
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=0):
            for col_idx, cell in enumerate(row):
                # 1. Formatage des cellules vides dans les colonnes importantes
                if col_idx < len(header_row) and header_row[col_idx] in important_columns:
                    # Vérifier si la cellule correspondante dans le DataFrame est vide/NaN
                    df_value = df_result.iloc[row_idx, col_idx]
                    
                    # Appliquer le formatage si la valeur est NaN, None, ou chaîne vide
                    if pd.isna(df_value) or df_value == '' or df_value is None:
                        cell.fill = missing_fill
                        # Laisser la cellule vide (pas de texte)
                        cell.value = None
                
                # 2. Formatage de la colonne Statut
                elif col_idx == statut_col_idx and statut_col_idx is not None:
                    if cell.value == 'COMPLET':
                        cell.fill = complete_fill
                    elif cell.value == 'INCOMPLET':
                        cell.fill = incomplete_fill
        
        # Ajuster la largeur des colonnes
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value is not None and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Max 50 caractères
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Changer l'extension pour Excel
        excel_path = output_path.replace('.csv', '.xlsx')
        
        # Sauvegarder le fichier Excel
        wb.save(excel_path)
        
        return excel_path, True
        
    except ImportError:
        # Si openpyxl n'est pas disponible, sauvegarder en CSV normal
        print("⚠️ openpyxl non disponible, sauvegarde en CSV")
        df_result.to_csv(output_path, sep=';', decimal=',', index=False, encoding='utf-8-sig')
        return output_path, False
    except Exception as e:
        # En cas d'erreur avec Excel, fallback vers CSV
        print(f"⚠️ Erreur lors de la création Excel : {e}")
        df_result.to_csv(output_path, sep=';', decimal=',', index=False, encoding='utf-8-sig')
        return output_path, False

if __name__ == '__main__':
    print("=== DÉMARRAGE DE L'APPLICATION ===")
    print("Application de génération de tableau de facturation LCDI")
    print("Accès: http://localhost:5000")
    print("======================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
