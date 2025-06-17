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
    print(f"Colonnes disponibles dans {file_type}: {list(df.columns)}")    # Dictionnaire de mapping pour les variantes de noms de colonnes
    column_mappings = {
        # Fichier des commandes
        'Name': ['Name', 'name', 'ORDER', 'Order', 'order', 'Nom', 'nom', 'Commande', 'commande', 'Id', 'ID', 'id', '#', 'Order ID', 'Order Id'],
        'Fulfilled at': ['Fulfilled at', 'fulfilled at', 'Date', 'date', 'Date commande', 'Date_commande'],
        'Billing name': ['Billing name', 'billing name', 'Client', 'client', 'Nom client', 'Nom_client', 'Billing Name', 'billing Name'],
        'Financial Status': ['Financial Status', 'financial status', 'Status', 'status', 'Statut', 'statut'],
        'Tax 1 Value': ['Tax 1 Value', 'tax 1 value', 'TVA', 'tva', 'Tax', 'tax', 'Taxe'],
        'Outstanding Balance': ['Outstanding Balance', 'outstanding balance', 'Balance', 'balance', 'Solde', 'solde'],
        'Payment Method': ['Payment Method', 'payment method', 'Method', 'method', 'Méthode', 'méthode'],
        # IMPORTANT: Colonnes pour le nouveau calcul HT/TVA/TTC
        'Total': ['Total', 'total'],  # TTC - UNIQUEMENT la vraie colonne Total !
        'Taxes': ['Taxes', 'taxes'],  # TVA - UNIQUEMENT la vraie colonne Taxes !
        
        # Fichier des transactions
        'Order': ['Order', 'order', 'Name', 'name', 'Commande', 'commande', 'Id', 'ID', 'id', 'Order ID', 'Order Id'],
        'Presentment Amount': ['Presentment Amount', 'presentment amount', 'Amount', 'amount', 'Montant', 'montant'],
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
                'Tax 1 Value': ['tax', 'tva', 'taxe', 'impot'],                'Outstanding Balance': ['balance', 'solde', 'outstanding', 'restant'],
                'Payment Method': ['payment', 'method', 'paiement', 'methode'],
                'Order': ['order', 'id', 'commande', 'numero', 'name'],
                'Presentment Amount': ['amount', 'montant', 'presentment'],
                'Fee': ['fee', 'frais', 'commission'],
                'Net': ['net', 'montant', 'amount'],
                # IMPORTANT: Pas de mapping approximatif pour Total et Taxes !
                # 'Total': sera géré par mapping exact uniquement
                # 'Taxes': sera géré par mapping exact uniquement
                'Piece': ['piece', 'reference', 'ref', 'order', 'id', 'commande', 'externe', 'external'],
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
                    # PROTECTION: Empêcher que "Subtotal" soit mappé vers "Total"
                    if missing_col == 'Total' and 'subtotal' in col.lower():
                        print(f"❌ REJETÉ: '{col}' ne peut pas être mappé vers 'Total' (doit être la vraie colonne Total)")
                        continue
                    
                    # PROTECTION: Empêcher que d'autres colonnes soient mappées vers "Taxes"
                    if missing_col == 'Taxes' and col.lower() not in ['taxes', 'tax']:
                        continue
                    
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

def categorize_payment_method(payment_method, ttc_value, fallback_amount=None):
    """Catégorise les méthodes de paiement et retourne les montants par catégorie"""
    if pd.isna(payment_method):
        return {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    # Utiliser le montant principal, sinon le fallback
    amount_to_use = ttc_value
    if pd.isna(ttc_value) and fallback_amount is not None and not pd.isna(fallback_amount):
        amount_to_use = fallback_amount
        print(f"DEBUG: Utilisation fallback amount {fallback_amount} pour méthode '{payment_method}'")
    
    # Si aucun montant valide, retourner 0 partout
    if pd.isna(amount_to_use):
        print(f"DEBUG: Aucun montant valide pour méthode '{payment_method}', retour 0")
        return {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    payment_method_lower = str(payment_method).lower()
    ttc_amount = float(amount_to_use)
    
    # Initialiser toutes les catégories à 0
    result = {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    # Améliorer la détection des méthodes de paiement selon les vraies données
    if 'virement' in payment_method_lower or 'wire' in payment_method_lower:
        result['Virement bancaire'] = ttc_amount
    elif 'alma' in payment_method_lower:
        result['ALMA'] = ttc_amount
    elif 'younited' in payment_method_lower:
        result['Younited'] = ttc_amount
    elif 'paypal' in payment_method_lower:
        result['PayPal'] = ttc_amount
    elif 'shopify payments' in payment_method_lower:
        # Shopify Payments = PayPal/CB généralement
        result['PayPal'] = ttc_amount
    elif 'custom' in payment_method_lower:
        # Custom = souvent virement bancaire
        result['Virement bancaire'] = ttc_amount
    else:
        # Méthode non reconnue, on peut la logger ou l'attribuer par défaut
        print(f"DEBUG: Méthode de paiement non reconnue: '{payment_method}' -> attribuée à PayPal")
        result['PayPal'] = ttc_amount
    
    return result

def calculate_corrected_amounts(df_merged_final):
    """
    Calcule les montants HT, TVA, TTC avec logique stricte.
    PRIORITÉ UNIQUE: Utilise les colonnes du Journal ("Montant du document TTC", "Montant du document HT")
    Si pas de données Journal, laisse la cellule vide (NaN) pour formatage conditionnel rouge
    """
    # Debug: afficher les colonnes disponibles
    print(f"DEBUG: Colonnes disponibles: {list(df_merged_final.columns)}")
    
    # Vérifier s'il y a des doublons
    column_counts = df_merged_final.columns.value_counts()
    duplicates = column_counts[column_counts > 1]
    if not duplicates.empty:
        print(f"DEBUG: Colonnes dupliquées trouvées: {duplicates.to_dict()}")
        # Supprimer les doublons en gardant la première occurrence
        df_merged_final = df_merged_final.loc[:, ~df_merged_final.columns.duplicated()]
        print(f"DEBUG: Colonnes après suppression des doublons: {list(df_merged_final.columns)}")
    
    # Initialiser toutes les séries avec NaN (cellules vides) et le bon index
    ttc_amounts = pd.Series([None] * len(df_merged_final), dtype=float, index=df_merged_final.index)
    ht_amounts = pd.Series([None] * len(df_merged_final), dtype=float, index=df_merged_final.index)
    tva_amounts = pd.Series([None] * len(df_merged_final), dtype=float, index=df_merged_final.index)
    
    # PRIORITÉ 1: Utiliser les montants du Journal si disponibles
    journal_ttc_available = 'Montant du document TTC' in df_merged_final.columns
    journal_ht_available = 'Montant du document HT' in df_merged_final.columns
    
    if journal_ttc_available:
        print("DEBUG: Utilisation des montants TTC du Journal (strict - pas de fallback)")
        # Convertir les montants français (virgule) en format numérique
        ttc_col = df_merged_final['Montant du document TTC'].astype(str).str.replace(',', '.').str.replace(' ', '')
        ttc_amounts_journal = pd.to_numeric(ttc_col, errors='coerce')
        
        # Utiliser uniquement les montants du journal (pas de fallback)
        ttc_amounts = ttc_amounts_journal.copy()
        
        if journal_ht_available:
            print("DEBUG: Utilisation des montants HT du Journal (strict)")
            # Convertir les montants français (virgule) en format numérique
            ht_col = df_merged_final['Montant du document HT'].astype(str).str.replace(',', '.').str.replace(' ', '')
            ht_amounts_journal = pd.to_numeric(ht_col, errors='coerce')
            
            # Utiliser uniquement les montants HT du journal
            ht_amounts = ht_amounts_journal.copy()
            
            # Calculer TVA = TTC - HT (seulement là où on a les deux)
            mask_both_available = ttc_amounts.notna() & ht_amounts.notna()
            tva_amounts.loc[mask_both_available] = ttc_amounts.loc[mask_both_available] - ht_amounts.loc[mask_both_available]
        else:
            print("DEBUG: Pas de montants HT dans le Journal - cellules HT et TVA restent vides")
            # Laisser HT et TVA vides si pas dans le journal
    else:
        print("DEBUG: Pas de montants TTC dans le Journal - utilisation des montants commandes uniquement là où journal absent")
        # Si pas de colonne TTC journal du tout, utiliser les commandes pour les lignes sans journal
        if 'Total' in df_merged_final.columns:
            # Détecter les lignes qui ont une Réf. LMB (donc potentiellement des données journal)
            has_lmb = df_merged_final['Référence LMB'].notna() & (df_merged_final['Référence LMB'] != '')
            # Pour les lignes SANS Réf. LMB, utiliser les montants des commandes
            mask_no_lmb = ~has_lmb
            
            ttc_from_orders = pd.to_numeric(df_merged_final['Total'], errors='coerce')
            ttc_amounts.loc[mask_no_lmb] = ttc_from_orders.loc[mask_no_lmb]
            
            if 'Taxes' in df_merged_final.columns:
                tva_from_orders = pd.to_numeric(df_merged_final['Taxes'], errors='coerce')
                tva_amounts.loc[mask_no_lmb] = tva_from_orders.loc[mask_no_lmb]
                
                # Calculer HT = TTC - TVA pour les lignes sans journal
                mask_calc_ht = mask_no_lmb & ttc_amounts.notna() & tva_amounts.notna()
                ht_amounts.loc[mask_calc_ht] = ttc_amounts.loc[mask_calc_ht] - tva_amounts.loc[mask_calc_ht]
    
    # Statistiques finales
    ttc_filled = ttc_amounts.notna().sum()
    ht_filled = ht_amounts.notna().sum()
    tva_filled = tva_amounts.notna().sum()
    n_rows = len(df_merged_final)
    
    print(f"DEBUG: Cellules remplies - TTC: {ttc_filled}/{n_rows}, HT: {ht_filled}/{n_rows}, TVA: {tva_filled}/{n_rows}")
    print(f"DEBUG: Cellules vides (formatage rouge) - TTC: {n_rows - ttc_filled}, HT: {n_rows - ht_filled}, TVA: {n_rows - tva_filled}")
    print(f"DEBUG: Échantillon TTC: {ttc_amounts.head().tolist()}")
    print(f"DEBUG: Échantillon HT: {ht_amounts.head().tolist()}")
    print(f"DEBUG: Échantillon TVA: {tva_amounts.head().tolist()}")
    
    return {
        'HT': ht_amounts,
        'TVA': tva_amounts,
        'TTC': ttc_amounts
    }

def calculate_invoice_dates(df_merged_final):
    """
    Calcule les dates de facture avec logique de priorité.
    PRIORITÉ 1: Utilise "Date du document" du Journal si disponible
    PRIORITÉ 2: Utilise "Fulfilled at" des commandes (date de livraison/expédition)
    """
    print(f"DEBUG: Calcul des dates de facture...")
    
    # Vérifier les colonnes disponibles
    journal_date_available = 'Date du document' in df_merged_final.columns
    fulfilled_date_available = 'Fulfilled at' in df_merged_final.columns
    
    # Initialiser la série des dates
    invoice_dates = pd.Series([None] * len(df_merged_final))
    
    if journal_date_available:
        print("DEBUG: Utilisation prioritaire des dates du Journal")
        # Convertir les dates du journal 
        journal_dates = df_merged_final['Date du document'].copy()
        
        # Pour les lignes avec données Journal, utiliser la date du journal
        mask_journal_available = journal_dates.notna() & (journal_dates != '') & (journal_dates != 'nan')
        if mask_journal_available.any():
            # Convertir format DD/MM/YYYY HH:MM:SS vers DD/MM/YYYY
            for idx in journal_dates[mask_journal_available].index:
                date_str = str(journal_dates[idx])
                if ' ' in date_str:
                    # Enlever la partie heure
                    date_part = date_str.split(' ')[0]
                    invoice_dates[idx] = date_part
                else:
                    invoice_dates[idx] = date_str
            print(f"DEBUG: {mask_journal_available.sum()} dates récupérées du Journal")
    
    if fulfilled_date_available:
        print("DEBUG: Utilisation fallback des dates Fulfilled at")
        # Pour les lignes sans date Journal, utiliser Fulfilled at
        fulfilled_dates = df_merged_final['Fulfilled at'].copy()
        
        # Masque pour les lignes qui n'ont pas encore de date
        mask_need_fulfilled = invoice_dates.isna() & fulfilled_dates.notna() & (fulfilled_dates != '') & (fulfilled_dates != 'nan')
        
        if mask_need_fulfilled.any():
            # Convertir format ISO vers format MM/DD/YYYY
            for idx in fulfilled_dates[mask_need_fulfilled].index:
                date_str = str(fulfilled_dates[idx])
                if 'T' in date_str or '+' in date_str:
                    # Format: 2025-05-19 11:11:57 +0200 ou 2025-05-19T11:11:57+02:00
                    try:
                        # Enlever timezone et heure
                        if '+' in date_str:
                            date_str = date_str.split('+')[0]
                        if 'T' in date_str:
                            date_str = date_str.split('T')[0]
                        elif ' ' in date_str:
                            date_str = date_str.split(' ')[0]
                          # Convertir YYYY-MM-DD vers DD/MM/YYYY (format français)
                        from datetime import datetime
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        invoice_dates[idx] = date_obj.strftime('%d/%m/%Y')
                    except:
                        # En cas d'erreur, garder la date originale
                        invoice_dates[idx] = date_str
                else:
                    invoice_dates[idx] = date_str
            print(f"DEBUG: {mask_need_fulfilled.sum()} dates récupérées de Fulfilled at")
    
    # Compter les résultats
    dates_found = invoice_dates.notna().sum()
    print(f"DEBUG: Total dates de facture trouvées: {dates_found}/{len(df_merged_final)}")
    
    # Échantillon de résultats
    sample_dates = invoice_dates[invoice_dates.notna()].head(5)
    print(f"DEBUG: Échantillon dates: {sample_dates.tolist()}")
    
    return invoice_dates

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
                               'Tax 1 Value', 'Outstanding Balance', 'Payment Method', 'Total', 'Taxes']
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
          # Détecter automatiquement d'autres colonnes numériques qui pourraient nécessiter une sommation        # Temporairement désactiver l'auto-détection pour éviter les erreurs pandas
        # for col in df_orders.columns:
        #     if col not in first_value_cols and col != 'Name':
        #         try:
        #             # Si c'est une colonne numérique, on la somme
        #             if pd.api.types.is_numeric_dtype(df_orders[col]):
        #                 if col not in sum_cols:
        #                     sum_cols.append(col)
        #                     print(f"   - Colonne numérique détectée pour sommation: {col}")
        #             # Sinon, on prend la première valeur
        #             elif col not in first_value_cols:
        #                 first_value_cols.append(col)
        #         except Exception as e:
        #             print(f"   - Erreur lors de l'analyse de la colonne {col}: {e}")
        #             # En cas d'erreur, traiter comme une colonne de première valeur
        #             if col not in first_value_cols:
        #                 first_value_cols.append(col)
        
        # Ajouter toutes les autres colonnes aux first_value_cols pour éviter les erreurs
        for col in df_orders.columns:
            if col not in first_value_cols and col not in sum_cols and col != 'Name':
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
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
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
        print(f"   - Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_merged_final)} ({ref_lmb_non_nulles/len(df_merged_final)*100:.1f}%)")        # ÉTAPE 4: Création du tableau final avec les 16 colonnes
        print("6. Création du tableau final...")
        
        df_final = pd.DataFrame()
        
        # Colonnes du tableau final dans l'ordre requis
        df_final['Centre de profit'] = 'lcdi.fr'  # Valeur statique
        df_final['Réf.WEB'] = df_merged_final['Name']
        df_final['Réf. LMB'] = df_merged_final['Référence LMB'].fillna('')
        df_final['Date Facture'] = calculate_invoice_dates(df_merged_final)
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('').apply(translate_financial_status)
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
            lambda row: categorize_payment_method(
                row['Payment Method'], 
                row['Presentment Amount'], 
                fallback_amount=row.get('Total', 0)  # Utiliser le montant de la commande si pas de transaction
            ), 
            axis=1
        )
        
        df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]
        df_final['Younited'] = [pm['Younited'] for pm in payment_categorization]
        df_final['PayPal'] = [pm['PayPal'] for pm in payment_categorization]
          # NETTOYAGE FINAL: Indiquer les informations manquantes
        df_final['Statut'] = df_merged_final.apply(
            lambda row: 'COMPLET' if pd.notna(row['Référence LMB']) and row['Outstanding Balance'] == 0 else 'INCOMPLET',
            axis=1
        )
        
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
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method', 'Total', 'Taxes']
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
        
        # Définir les colonnes pour l'agrégation        # Listes de base pour l'agrégation
        first_cols = ['Fulfilled at', 'Billing name', 'Financial Status', 'Payment Method', 'Email', 'Lineitem name']
        sum_cols = ['Tax 1 Value', 'Outstanding Balance']
        
        # Colonnes monétaires spécifiques à sommer (éviter l'auto-détection problématique)
        predefined_sum_cols = ['Total', 'Taxes', 'Shipping', 'Discount Amount', 'Refunded Amount', 
                              'Lineitem price', 'Lineitem quantity', 'Outstanding Balance']
        
        for col in predefined_sum_cols:
            if col in df_orders.columns and col not in sum_cols:
                try:
                    # Vérifier que la colonne contient réellement des valeurs numériques
                    non_null_values = df_orders[col].dropna()
                    if len(non_null_values) > 0:
                        # Tenter de convertir en numérique
                        pd.to_numeric(non_null_values, errors='raise')
                        sum_cols.append(col)
                        print(f"   - Colonne prédéfinie ajoutée pour sommation: {col}")
                except Exception:
                    # Si conversion échoue, traiter comme première valeur
                    if col not in first_cols:
                        first_cols.append(col)
                        print(f"   - Colonne {col} traitée comme 'first' (non numérique)")
        
        # Ajouter les autres colonnes non numériques à first_cols
        for col in df_orders.columns:
            if col not in sum_cols and col not in first_cols and col != 'Name':
                first_cols.append(col)
        
        # Construire le dictionnaire d'opérations d'agrégation
        agg_operations = {}
        
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
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
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
        df_final['Date Facture'] = calculate_invoice_dates(df_merged_final)
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('').apply(translate_financial_status)
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
            lambda row: categorize_payment_method(
                row['Payment Method'], 
                row['Presentment Amount'], 
                fallback_amount=row.get('Total', 0)  # Utiliser le montant de la commande si pas de transaction
            ), 
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
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method', 'Total', 'Taxes']
        required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        required_journal_cols = ['Piece', 'Référence LMB']
          # Normaliser les noms de colonnes pour les commandes
        df_orders = normalize_column_names(df_orders, required_orders_cols, 'commandes')
        validate_required_columns(df_orders, required_orders_cols, "fichier des commandes")
        
        # Normaliser les noms de colonnes pour les transactions
        df_transactions = normalize_column_names(df_transactions, required_transactions_cols, 'transactions')
        validate_required_columns(df_transactions, required_transactions_cols, "fichier des transactions")
        
        # Normaliser les noms de colonnes pour le journal
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
            df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
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
        df_final['Date Facture'] = calculate_invoice_dates(df_merged_final)
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('').apply(translate_financial_status)
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
            lambda row: categorize_payment_method(
                row['Payment Method'], 
                row['Presentment Amount'], 
                fallback_amount=row.get('Total', 0)  # Utiliser le montant de la commande si pas de transaction
            ), 
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

def translate_financial_status(status):
    """
    Traduit les statuts financiers anglais en français
    """
    if pd.isna(status) or status == '':
        return ''
    
    status_str = str(status).lower().strip()
    
    # Dictionnaire de traduction
    translations = {
        'paid': 'payée',
        'pending': 'en attente',
        'partially_paid': 'payée partiellement',
        'refunded': 'remboursée',
        'partially_refunded': 'remboursée partiellement',
        'voided': 'annulée'
    }
    
    return translations.get(status_str, status_str)

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
    Fusion améliorée avec gestion des références multiples
    Gère les formats #LCDI-XXXX vs LCDI-XXXX et les références multiples comme 'LCDI-1020 LCDI-1021'
    """
    print("   - Fusion avec normalisation et gestion des références multiples...")
    
    # Copier les DataFrames pour éviter de modifier les originaux
    df_orders_copy = df_orders.copy()
    df_journal_copy = df_journal.copy()
    
    # Trouver la colonne de référence dans le journal (peut être 'Piece' après normalisation)
    journal_ref_col = 'Piece'  # Nom standardisé après normalize_column_names
    
    if journal_ref_col not in df_journal_copy.columns:
        print(f"❌ Erreur: Colonne '{journal_ref_col}' non trouvée dans le journal")
        print(f"Colonnes disponibles: {list(df_journal_copy.columns)}")
        return df_orders_copy  # Retourner les commandes sans fusion
    
    # Normaliser les références des commandes : toujours au format #LCDI-XXXX
    df_orders_copy['Name_normalized'] = df_orders_copy['Name'].apply(
        lambda x: x if str(x).startswith('#') else f"#{x}" if pd.notna(x) else None
    )
    
    # Créer un dictionnaire de mapping : référence normalisée -> données journal
    journal_mapping = {}
    
    # Pour chaque ligne du journal
    for journal_idx, journal_row in df_journal_copy.iterrows():
        journal_ref = journal_row[journal_ref_col]
        if pd.isna(journal_ref):
            continue
            
        journal_ref_str = str(journal_ref).strip()
        
        # Cas 1: Référence simple (ex: LCDI-1038 ou #LCDI-1038)
        if ' ' not in journal_ref_str:
            # Normaliser la référence
            journal_normalized = journal_ref_str if journal_ref_str.startswith('#') else f"#{journal_ref_str}"
            journal_mapping[journal_normalized] = journal_row          # Cas 2: Référence multiple (ex: LCDI-1020 LCDI-1021) 
        else:
            import re
            # Extraire tous les numéros de commandes
            numbers = re.findall(r'LCDI-(\d+)', journal_ref_str)
            
            if numbers:
                print(f"     - Référence multiple détectée: '{journal_ref_str}' -> commandes {numbers}")
                
                # Pour les références multiples, on doit répartir les montants
                # Stratégie: calculer le poids de chaque commande et répartir proportionnellement
                
                # Récupérer les montants totaux des commandes concernées pour calculer les proportions
                command_totals = {}
                total_sum = 0
                
                for num in numbers:
                    target_ref = f"#LCDI-{num}"
                    # Trouver la commande correspondante dans df_orders_copy
                    matching_orders = df_orders_copy[df_orders_copy['Name_normalized'] == target_ref]
                    if not matching_orders.empty:
                        order_total = pd.to_numeric(matching_orders.iloc[0]['Total'], errors='coerce')
                        if pd.notna(order_total):
                            command_totals[target_ref] = order_total
                            total_sum += order_total
                        else:
                            command_totals[target_ref] = 0
                    else:
                        command_totals[target_ref] = 0
                
                print(f"       - Totaux des commandes : {command_totals}, somme: {total_sum}")
                
                # Récupérer les montants du journal
                journal_ttc = journal_row.get('Montant du document TTC', None)
                journal_ht = journal_row.get('Montant du document HT', None)
                journal_marge = journal_row.get('Montant marge HT', None)
                
                # Convertir les montants du journal au format numérique
                if pd.notna(journal_ttc):
                    try:
                        journal_ttc_num = float(str(journal_ttc).replace(',', '.').replace(' ', ''))
                    except:
                        journal_ttc_num = None
                else:
                    journal_ttc_num = None
                    
                if pd.notna(journal_ht):
                    try:
                        journal_ht_num = float(str(journal_ht).replace(',', '.').replace(' ', ''))
                    except:
                        journal_ht_num = None
                else:
                    journal_ht_num = None
                    
                if pd.notna(journal_marge):
                    try:
                        journal_marge_num = float(str(journal_marge).replace(',', '.').replace(' ', ''))
                    except:
                        journal_marge_num = None
                else:
                    journal_marge_num = None
                
                print(f"       - Montants journal : TTC={journal_ttc_num}, HT={journal_ht_num}, Marge={journal_marge_num}")
                
                # Répartir les montants proportionnellement
                for num in numbers:
                    target_ref = f"#LCDI-{num}"
                    
                    # Créer une copie de la ligne journal pour cette commande
                    proportional_journal_data = journal_row.copy()
                    
                    # Calculer la proportion de cette commande
                    if total_sum > 0 and command_totals[target_ref] > 0:
                        proportion = command_totals[target_ref] / total_sum
                        print(f"       - {target_ref}: proportion = {proportion:.3f}")
                        
                        # Répartir les montants
                        if journal_ttc_num is not None:
                            proportional_ttc = journal_ttc_num * proportion
                            proportional_journal_data['Montant du document TTC'] = f"{proportional_ttc:.2f}".replace('.', ',')
                        
                        if journal_ht_num is not None:
                            proportional_ht = journal_ht_num * proportion
                            proportional_journal_data['Montant du document HT'] = f"{proportional_ht:.2f}".replace('.', ',')
                        
                        if journal_marge_num is not None:
                            proportional_marge = journal_marge_num * proportion
                            proportional_journal_data['Montant marge HT'] = f"{proportional_marge:.2f}".replace('.', ',')
                            
                        print(f"         - Montants répartis : TTC={proportional_ttc:.2f}, HT={proportional_ht:.2f}")
                    else:
                        # Si pas de proportion calculable, distribuer équitablement
                        equal_proportion = 1.0 / len(numbers)
                        print(f"       - {target_ref}: proportion égale = {equal_proportion:.3f}")
                        
                        if journal_ttc_num is not None:
                            equal_ttc = journal_ttc_num * equal_proportion
                            proportional_journal_data['Montant du document TTC'] = f"{equal_ttc:.2f}".replace('.', ',')
                        
                        if journal_ht_num is not None:
                            equal_ht = journal_ht_num * equal_proportion
                            proportional_journal_data['Montant du document HT'] = f"{equal_ht:.2f}".replace('.', ',')
                        
                        if journal_marge_num is not None:
                            equal_marge = journal_marge_num * equal_proportion
                            proportional_journal_data['Montant marge HT'] = f"{equal_marge:.2f}".replace('.', ',')
                    
                    # Stocker le mapping
                    journal_mapping[target_ref] = proportional_journal_data
                    print(f"       - Mapped {target_ref} -> {proportional_journal_data['Référence LMB']} (montants répartis)")
    
    # Appliquer le mapping aux commandes
    journal_data = []
    for idx, row in df_orders_copy.iterrows():
        order_ref = row['Name_normalized']
        if order_ref in journal_mapping:
            journal_data.append(journal_mapping[order_ref])
        else:
            # Créer une ligne vide avec les mêmes colonnes
            empty_row = pd.Series(index=df_journal_copy.columns, dtype=object)
            journal_data.append(empty_row)
    
    # Convertir en DataFrame
    df_journal_mapped = pd.DataFrame(journal_data, index=df_orders_copy.index)
    
    # Concaténer horizontalement
    df_merged = pd.concat([df_orders_copy, df_journal_mapped], axis=1)
    
    # Compter les correspondances
    correspondances = df_merged['Référence LMB'].notna().sum()
    total = len(df_merged)
    
    print(f"     - Correspondances trouvées : {correspondances}/{total} ({correspondances/total*100:.1f}%)")
    
    return df_merged

def fill_missing_data_indicators(df_final, df_merged_final):
    """
    Ajoute une colonne de statut simple : COMPLET ou INCOMPLET
    Laisse les cellules vides sans marqueur pour les montants principaux (HT, TVA, TTC)
    afin que le formatage conditionnel rouge s'applique.
    """    # 1. Nettoyer SEULEMENT les colonnes numériques secondaires (pas HT, TVA, TTC, ni les méthodes de paiement)
    # Les colonnes HT, TVA, TTC gardent leurs NaN pour le formatage conditionnel rouge
    # Les colonnes de méthodes de paiement gardent leurs valeurs calculées
    secondary_numeric_columns = ['reste', 'Shopify', 'Frais de commission']
    
    for col in secondary_numeric_columns:
        if col in df_final.columns:
            df_final[col] = df_final[col].fillna(0)
      # 2. Déterminer le statut : COMPLET ou INCOMPLET
    status_info = []
    for idx, row in df_final.iterrows():
        # Une ligne est COMPLÈTE si elle a :
        # - Une référence LMB (pas vide/NaN)
        # - Au moins une méthode de paiement avec un montant > 0
        # - Une date de facture (pas vide/NaN)
        
        has_lmb = pd.notna(row['Réf. LMB']) and str(row['Réf. LMB']).strip() != ''
        has_date = pd.notna(row['Date Facture']) and str(row['Date Facture']).strip() != ''
        
        # Vérifier toutes les méthodes de paiement
        payment_methods = ['Virement bancaire', 'ALMA', 'Younited', 'PayPal', 'Shopify']
        has_payment = False
        
        for method in payment_methods:
            if method in row and pd.notna(row[method]):
                try:
                    amount = float(row[method])
                    if abs(amount) > 0.01:  # Tolérance pour les erreurs d'arrondi
                        has_payment = True
                        break
                except (ValueError, TypeError):
                    continue
        
        if has_lmb and has_payment and has_date:
            status_info.append("COMPLET")
        else:
            status_info.append("INCOMPLET")
    
    # 3. Ajouter la colonne de statut
    df_final['Statut'] = status_info    
    print(f"DEBUG: Cellules NaN conservées pour formatage rouge - HT, TVA, TTC")
    print(f"DEBUG: Cellules conservées (valeurs calculées) - Virement bancaire, ALMA, Younited, PayPal")
    print(f"DEBUG: Cellules nettoyées (NaN->0) - colonnes secondaires: {secondary_numeric_columns}")
    
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
        # Rouge encore plus profond pour les cellules manquantes et INCOMPLET
        missing_fill = PatternFill(start_color='CC0000', end_color='CC0000', fill_type='solid')  # Rouge encore plus profond
        incomplete_fill = PatternFill(start_color='CC0000', end_color='CC0000', fill_type='solid')  # Même rouge encore plus profond        # Vert plus profond pour COMPLET
        complete_fill = PatternFill(start_color='66CC66', end_color='66CC66', fill_type='solid')  # Vert plus profond
        
        # Style pour les en-têtes (gras)
        from openpyxl.styles import Font
        header_font = Font(bold=True)
        
        # Style pour la colonne Shopify (texte rouge)
        shopify_font = Font(color='FF0000', bold=True)  # Rouge pour l'en-tête
        shopify_content_font = Font(color='FF0000')  # Rouge pour le contenu
        
        # Colonnes où vérifier les données manquantes (exclure les colonnes numériques qui sont à 0)
        important_columns = ['Réf. LMB', 'Date Facture', 'Etat', 'Client']
        header_row = [cell.value for cell in ws[1]]
        
        # Appliquer le formatage gras aux en-têtes (première ligne)
        for col_idx, cell in enumerate(ws[1]):
            if col_idx < len(header_row) and header_row[col_idx] == 'Shopify':
                # En-tête Shopify en rouge gras
                cell.font = shopify_font
            else:
                # Autres en-têtes en gras normal
                cell.font = header_font
        
        # Trouver l'index de la colonne Statut et Shopify
        statut_col_idx = None
        shopify_col_idx = None
        for idx, col_name in enumerate(header_row):
            if col_name == 'Statut':
                statut_col_idx = idx
            elif col_name == 'Shopify':
                shopify_col_idx = idx
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
                
                # 3. Formatage de la colonne Shopify (texte rouge)
                elif col_idx == shopify_col_idx and shopify_col_idx is not None:
                    if cell.value is not None and cell.value != 0:
                        cell.font = shopify_content_font
        
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
        
        # Figer la première ligne (en-têtes de colonnes) pour qu'elle reste visible lors du défilement
        ws.freeze_panes = 'A2'  # Fige tout ce qui est au-dessus de la ligne 2 (donc la ligne 1 avec les en-têtes)
        
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
