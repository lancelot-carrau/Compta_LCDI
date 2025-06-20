from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import os
from datetime import datetime
import tempfile
from werkzeug.utils import secure_filename
import io
import chardet
import re
import logging
import sys
import webbrowser
import threading
import time
import uuid
from logging.handlers import RotatingFileHandler
# Bibliothèques pour l'extraction PDF
import PyPDF2
import pdfplumber
try:
    import tabula
except ImportError:
    tabula = None
try:
    import camelot
except ImportError:
    camelot = None
try:
    import openpyxl
except ImportError:
    openpyxl = None

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration du logging
def setup_logging():
    """Configure le système de logging"""
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configuration du format de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger principal de l'application
    app_logger = logging.getLogger('LCDI_APP')
    app_logger.setLevel(logging.DEBUG)
    
    # Handler pour fichier avec rotation
    file_handler = RotatingFileHandler(
        'logs/lcdi_app.log', 
        maxBytes=10*1024*1024,  # 10MB max par fichier
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # Ajouter les handlers
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    
    # Logger Flask
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    return app_logger

# Initialiser le logging
logger = setup_logging()
logger.info("=== DÉMARRAGE DE L'APPLICATION LCDI ===")
logger.info(f"Version Python: {sys.version}")
logger.info(f"Répertoire de travail: {os.getcwd()}")

# Configuration des dossiers - utilisation de chemins absolus
base_dir = os.getcwd()
UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')
OUTPUT_FOLDER = os.path.join(base_dir, 'output')
ALLOWED_EXTENSIONS = {'csv', 'pdf'}  # Ajouter 'pdf' pour les factures Amazon

logger.info(f"Répertoire de base: {base_dir}")
logger.info(f"Dossier upload: {UPLOAD_FOLDER}")
logger.info(f"Dossier output: {OUTPUT_FOLDER}")

# Créer les dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Dossier créé: {folder}")
    else:
        logger.debug(f"Dossier existant: {folder}")

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    is_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    logger.debug(f"Vérification fichier {filename}: {'Autorisé' if is_allowed else 'Non autorisé'}")
    return is_allowed

# =====================================================================
# FONCTIONS POUR L'EXTRACTION PDF AMAZON
# =====================================================================

def extract_pdf_text(pdf_path):
    """Extrait le texte d'un fichier PDF en utilisant PyPDF2"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte avec PyPDF2: {e}")
    
    return text.strip()

def extract_pdf_tables_pdfplumber(pdf_path):
    """Extrait les tableaux d'un fichier PDF en utilisant pdfplumber"""
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de tableaux avec pdfplumber: {e}")
    
    return tables

def process_pdf_extraction(pdf_path, extraction_method='auto'):
    """
    Traite l'extraction d'un fichier PDF de facture Amazon
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        extraction_method: Méthode d'extraction ('auto', 'text', 'tables')
    
    Returns:
        dict: Résultats de l'extraction avec success, text, tables, errors
    """
    logger.info(f"Extraction PDF: {pdf_path} avec méthode {extraction_method}")
    
    result = {
        'success': False,
        'text': '',
        'tables': [],
        'errors': []
    }
    
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(pdf_path):
            result['errors'].append(f"Fichier non trouvé: {pdf_path}")
            return result
        
        # Extraction du texte
        text = extract_pdf_text(pdf_path)
        if text:
            result['text'] = text
            result['success'] = True
            logger.info(f"Texte extrait: {len(text)} caractères")
        else:
            result['errors'].append("Aucun texte extrait")
        
        # Extraction des tableaux
        tables = extract_pdf_tables_pdfplumber(pdf_path)
        if tables:
            result['tables'] = tables
            result['success'] = True
            logger.info(f"Tableaux extraits: {len(tables)} tableaux")
        
        if not result['success']:
            result['errors'].append("Aucune donnée extraite du PDF")
        
    except Exception as e:
        error_msg = f"Erreur lors de l'extraction PDF: {str(e)}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
    
    return result

def parse_date_string(date_str):
    """Parse une chaîne de date en format DD/MM/YYYY"""
    if not date_str:
        return ''
    
    try:
        # Essayer différents formats
        formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                continue
        
        # Si aucun format ne marche, retourner la chaîne originale
        return str(date_str)
        
    except Exception as e:
        logger.warning(f"Erreur lors du parsing de date '{date_str}': {e}")
        return str(date_str) if date_str else ''

def parse_amazon_invoice_data(text, debug_mode=False):
    """
    Parse les données d'une facture Amazon à partir du texte extrait
    Retourne un dictionnaire avec les données structurées
    """
    debug_info = []
    
    try:
        if debug_mode:
            debug_info.append(f"Texte à parser (longueur: {len(text)})")
            debug_info.append(f"Début du texte: {text[:200]}...")
        
        # Initialiser les données de la facture
        invoice_data = {
            'id_amazon': '',
            'facture_amazon': '',
            'date_facture': '',
            'pays': '',
            'nom_contact': '',
            'ht': 0.0,
            'tva': 0.0,
            'taux_tva': '',
            'total': 0.0,
            'debug_info': debug_info if debug_mode else []
        }
        
        # Patterns de recherche pour les données Amazon
        patterns = {
            'order_id': [
                r'Order\s*[#:]?\s*([0-9]{3}-[0-9]{7}-[0-9]{7})',
                r'Commande\s*[#:]?\s*([0-9]{3}-[0-9]{7}-[0-9]{7})',
                r'([0-9]{3}-[0-9]{7}-[0-9]{7})'
            ],
            'invoice_number': [
                r'Invoice\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'Facture\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'(FR[0-9A-Z]+)'
            ],
            'date': [
                r'Invoice\s*Date[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{4})',
                r'Date[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{4})',
                r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{4})'
            ],
            'country': [
                r'Ship\s*to[:\s]+.*?([A-Z]{2})\s*[0-9]',
                r'Livraison[:\s]+.*?([A-Z]{2})\s*[0-9]',
                r'Address[:\s]+.*?([A-Z]{2})\s*[0-9]',
                r'\b(BE|IT|DE|ES|NL|MT|PT|LU)\b(?!\w)',
                r'\b(FR)\b(?![0-9])'
            ],
            'customer_name': [
                r'Ship\s*to[:\s]+([A-Za-z\s]+)',
                r'Livraison[:\s]+([A-Za-z\s]+)',
                r'Bill\s*to[:\s]+([A-Za-z\s]+)',
                r'Facturation[:\s]+([A-Za-z\s]+)'
            ],
            'total_amount': [
                r'(?<!Sub)Total[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'Grand\s*Total[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'Amount[:\s]+[€$]?([0-9,]+\.?[0-9]*)'
            ],
            'tax_amount': [
                r'Tax[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'TVA[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'VAT[:\s]+[€$]?([0-9,]+\.?[0-9]*)'
            ],
            'subtotal': [
                r'Subtotal[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'Sous-total[:\s]+[€$]?([0-9,]+\.?[0-9]*)',
                r'Sub-total[:\s]+[€$]?([0-9,]+\.?[0-9]*)'
            ]
        }
        
        # Extraire les données avec les patterns
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if debug_mode:
                        debug_info.append(f"Pattern '{key}' trouvé: {value}")
                    
                    if key == 'order_id':
                        invoice_data['id_amazon'] = value
                    elif key == 'invoice_number':
                        invoice_data['facture_amazon'] = value
                    elif key == 'date':
                        parsed_date = parse_date_string(value)
                        if parsed_date:
                            invoice_data['date_facture'] = parsed_date
                    elif key == 'country':
                        invoice_data['pays'] = value.upper()
                    elif key == 'customer_name':
                        name = re.sub(r'[0-9\n\r]+', ' ', value).strip()
                        if len(name) > 3:
                            invoice_data['nom_contact'] = name[:50]
                    elif key == 'total_amount':
                        try:
                            invoice_data['total'] = float(value.replace(',', ''))
                        except ValueError:
                            pass
                    elif key == 'tax_amount':
                        try:
                            invoice_data['tva'] = float(value.replace(',', ''))
                        except ValueError:
                            pass
                    elif key == 'subtotal':
                        try:
                            invoice_data['ht'] = float(value.replace(',', ''))
                        except ValueError:
                            pass
                    break
        
        # Calculer les valeurs manquantes
        if invoice_data['total'] > 0 and invoice_data['tva'] > 0 and invoice_data['ht'] == 0:
            invoice_data['ht'] = invoice_data['total'] - invoice_data['tva']
        elif invoice_data['total'] == 0 and invoice_data['ht'] > 0 and invoice_data['tva'] > 0:
            invoice_data['total'] = invoice_data['ht'] + invoice_data['tva']
        
        # Calculer le taux de TVA
        if invoice_data['ht'] > 0 and invoice_data['tva'] > 0:
            taux = (invoice_data['tva'] / invoice_data['ht']) * 100
            invoice_data['taux_tva'] = f"{taux:.2f}%"
        
        # Vérifier si on a les données minimales
        has_minimum_data = (
            invoice_data['id_amazon'] or 
            invoice_data['facture_amazon'] or 
            invoice_data['total'] > 0
        )
        
        if debug_mode:
            debug_info.append(f"Données extraites: {invoice_data}")
            debug_info.append(f"Données minimales présentes: {has_minimum_data}")
        
        if has_minimum_data:
            return invoice_data
        else:
            if debug_mode:
                debug_info.append("Échec: pas de données minimales trouvées")
            return None
            
    except Exception as e:
        if debug_mode:
            debug_info.append(f"Erreur lors du parsing: {str(e)}")
        return None

def create_structured_excel_from_invoices(invoices_data, output_path, existing_excel_path=None):
    """
    Crée un fichier Excel structuré à partir des données de factures Amazon
    
    Args:
        invoices_data: Liste des dictionnaires de données de factures
        output_path: Chemin du fichier Excel de sortie
        existing_excel_path: Chemin optionnel d'un fichier Excel existant à combiner
    
    Returns:
        dict: Résultats de l'opération avec succès/erreurs
    """
    logger.info(f"Création du fichier Excel structuré: {output_path}")
    
    try:
        # Préparer les données pour le DataFrame
        rows_data = []
        
        # Si on a un fichier existant, le charger d'abord
        if existing_excel_path and os.path.exists(existing_excel_path):
            try:
                logger.info(f"Chargement du fichier Excel existant: {existing_excel_path}")
                existing_df = pd.read_excel(existing_excel_path, header=1)  # header=1 car la première ligne contient les totaux
                
                # Vérifier si le DataFrame a les bonnes colonnes
                expected_columns = ['N°', 'ID AMAZON', 'Facture AMAZON', 'Date Facture', 'Pays', 'Nom contact', 'HT', 'TVA', 'Taux TVA', 'TOTAL']
                if all(col in existing_df.columns for col in expected_columns):
                    # Convertir les données existantes en format de liste
                    for _, row in existing_df.iterrows():
                        if pd.notna(row['N°']) and str(row['N°']).isdigit():  # Éviter les lignes de totaux
                            rows_data.append({
                                'numero': int(row['N°']),
                                'id_amazon': str(row['ID AMAZON']) if pd.notna(row['ID AMAZON']) else '',
                                'facture_amazon': str(row['Facture AMAZON']) if pd.notna(row['Facture AMAZON']) else '',
                                'date_facture': str(row['Date Facture']) if pd.notna(row['Date Facture']) else '',
                                'pays': str(row['Pays']) if pd.notna(row['Pays']) else '',
                                'nom_contact': str(row['Nom contact']) if pd.notna(row['Nom contact']) else '',
                                'ht': float(row['HT']) if pd.notna(row['HT']) else 0.0,
                                'tva': float(row['TVA']) if pd.notna(row['TVA']) else 0.0,
                                'taux_tva': str(row['Taux TVA']) if pd.notna(row['Taux TVA']) else '',
                                'total': float(row['TOTAL']) if pd.notna(row['TOTAL']) else 0.0
                            })
                    logger.info(f"Données existantes chargées: {len(rows_data)} factures")
                else:
                    logger.warning("Le fichier Excel existant n'a pas la structure attendue")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du fichier existant: {str(e)}")
        
        # Déterminer le numéro de départ
        start_numero = max([row['numero'] for row in rows_data], default=0) + 1
        
        # Ajouter les nouvelles données de factures
        for i, invoice in enumerate(invoices_data):
            rows_data.append({
                'numero': start_numero + i,
                'id_amazon': invoice.get('id_amazon', ''),
                'facture_amazon': invoice.get('facture_amazon', ''),
                'date_facture': invoice.get('date_facture', ''),
                'pays': invoice.get('pays', ''),
                'nom_contact': invoice.get('nom_contact', ''),
                'ht': invoice.get('ht', 0.0),
                'tva': invoice.get('tva', 0.0),
                'taux_tva': invoice.get('taux_tva', ''),
                'total': invoice.get('total', 0.0)
            })
        
        # Calculer les totaux
        total_ht = sum([row['ht'] for row in rows_data])
        total_tva = sum([row['tva'] for row in rows_data])
        total_ttc = sum([row['total'] for row in rows_data])
        
        logger.info(f"Totaux calculés - HT: {total_ht:.2f}, TVA: {total_tva:.2f}, TTC: {total_ttc:.2f}")
        
        # Créer le DataFrame avec la structure attendue
        df_data = []
        
        # Première ligne avec les totaux (colonnes vides pour les premières, puis les totaux)
        df_data.append(['', '', '', '', '', '', f"{total_ht:.2f}", f"{total_tva:.2f}", '', f"{total_ttc:.2f}"])
        
        # Ligne d'en-têtes
        df_data.append(['N°', 'ID AMAZON', 'Facture AMAZON', 'Date Facture', 'Pays', 'Nom contact', 'HT', 'TVA', 'Taux TVA', 'TOTAL'])
        
        # Données des factures
        for row in rows_data:
            df_data.append([
                str(row['numero']),
                row['id_amazon'],
                row['facture_amazon'],
                row['date_facture'],
                row['pays'],
                row['nom_contact'],
                f"{row['ht']:.2f}",
                f"{row['tva']:.2f}",
                row['taux_tva'],
                f"{row['total']:.2f}"
            ])
        
        # Créer le DataFrame
        df = pd.DataFrame(df_data)
        
        # Sauvegarder en Excel
        df.to_excel(output_path, index=False, header=False)
        
        logger.info(f"Fichier Excel créé avec succès: {output_path}")
        logger.info(f"Nombre total de factures dans le fichier: {len(rows_data)}")
        
        return {
            'success': True,
            'processed_invoices': len(rows_data),
            'new_invoices': len(invoices_data),
            'total_ht': total_ht,
            'total_tva': total_tva,
            'total_ttc': total_ttc,
            'errors': []
        }
        
    except Exception as e:
        error_msg = f"Erreur lors de la création du fichier Excel: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'processed_invoices': 0,
            'new_invoices': 0,
            'total_ht': 0,
            'total_tva': 0,
            'total_ttc': 0,
            'errors': [error_msg]
        }

# =====================================================================
# ROUTES FLASK
# =====================================================================

@app.route('/')
def index():
    """Page d'accueil avec les différents générateurs"""
    return render_template('index.html')

@app.route('/extract_pdf_batch', methods=['POST'])
def extract_pdf_batch():
    """Traite l'extraction en lot de plusieurs fichiers PDF de factures Amazon"""
    logger.info("=== DÉBUT DE L'EXTRACTION PDF EN LOT ===")
    
    try:
        # Vérifier si des fichiers PDF ont été uploadés
        if 'pdf_files' not in request.files:
            return jsonify({'error': 'Aucun fichier PDF sélectionné'}), 400
        
        pdf_files = request.files.getlist('pdf_files')
        if not pdf_files or all(file.filename == '' for file in pdf_files):
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier le nombre de fichiers (limite à 300)
        if len(pdf_files) > 300:
            return jsonify({'error': f'Trop de fichiers sélectionnés ({len(pdf_files)}). Maximum autorisé: 300'}), 400
        
        # Récupérer les paramètres
        processing_mode = request.form.get('pdf_processing_mode', 'new')
        extraction_method = request.form.get('extraction_method', 'amazon_smart')
        existing_excel_path = None
        
        logger.info(f"Mode de traitement: {processing_mode}")
        logger.info(f"Méthode d'extraction: {extraction_method}")
        logger.info(f"Nombre de fichiers à traiter: {len(pdf_files)}")
        
        # Si mode combine, récupérer le fichier Excel existant
        if processing_mode == 'combine':
            if 'pdf_old_file' in request.files:
                existing_excel = request.files['pdf_old_file']
                if existing_excel.filename and existing_excel.filename.endswith('.xlsx'):
                    existing_filename = secure_filename(existing_excel.filename)
                    existing_excel_path = os.path.join(UPLOAD_FOLDER, f"existing_{existing_filename}")
                    existing_excel.save(existing_excel_path)
                    logger.info(f"Fichier Excel existant sauvegardé: {existing_excel_path}")
        
        # Traiter chaque fichier PDF
        invoices_data = []
        processing_errors = []
        processed_files = []
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Vérifier l'extension
                if not pdf_file.filename.lower().endswith('.pdf'):
                    processing_errors.append(f"Fichier ignoré (non PDF): {pdf_file.filename}")
                    continue
                
                # Sauvegarder temporairement
                filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(UPLOAD_FOLDER, f"batch_{i}_{filename}")
                pdf_file.save(pdf_path)
                
                logger.info(f"Traitement du fichier {i+1}/{len(pdf_files)}: {filename}")
                
                # Extraire les données du PDF
                pdf_results = process_pdf_extraction(pdf_path, extraction_method)
                
                if pdf_results['success']:
                    # Parser les données de la facture Amazon
                    text_to_parse = pdf_results['text']
                    
                    # Si pas de texte mais des tableaux, essayer d'extraire le texte des tableaux
                    if not text_to_parse and pdf_results['tables']:
                        text_parts = []
                        for table in pdf_results['tables']:
                            try:
                                if hasattr(table, 'values'):
                                    text_parts.append(' '.join([str(cell) for row in table.values for cell in row if pd.notna(cell)]))
                                elif isinstance(table, list):
                                    text_parts.append(' '.join([str(cell) for row in table for cell in row if cell]))
                            except Exception as table_error:
                                logger.warning(f"Erreur lors de l'extraction du texte d'un tableau: {table_error}")
                                continue
                        text_to_parse = ' '.join(text_parts)
                    
                    if text_to_parse:
                        try:
                            invoice_data = parse_amazon_invoice_data(text_to_parse, debug_mode=False)
                            if invoice_data:
                                invoices_data.append(invoice_data)
                                processed_files.append(filename)
                            else:
                                processing_errors.append(f"Impossible de parser la facture: {filename}")
                        except Exception as parsing_error:
                            logger.error(f"Erreur lors du parsing de {filename}: {str(parsing_error)}")
                            processing_errors.append(f"Erreur de parsing {filename}: {str(parsing_error)}")
                    else:
                        processing_errors.append(f"Aucun texte extrait de: {filename}")
                else:
                    processing_errors.append(f"Échec extraction: {filename} - {'; '.join(pdf_results['errors'])}")
                
                # Nettoyer le fichier temporaire
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    
            except Exception as e:
                processing_errors.append(f"Erreur sur {pdf_file.filename}: {str(e)}")
                logger.error(f"Erreur traitement {pdf_file.filename}: {str(e)}")
        
        # Vérifier qu'on a au moins une facture traitée
        if not invoices_data:
            # Nettoyer le fichier existant temporaire si présent
            if existing_excel_path and os.path.exists(existing_excel_path):
                os.remove(existing_excel_path)
            
            return jsonify({
                'error': 'Aucune facture n\'a pu être traitée',
                'processing_errors': processing_errors
            }), 400
        
        # Générer le nom du fichier de sortie
        timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        output_filename = f"Compta_LCDI_Amazon_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Créer le fichier Excel structuré
        logger.info("Création du fichier Excel structuré")
        excel_results = create_structured_excel_from_invoices(
            invoices_data, 
            output_path, 
            existing_excel_path
        )
        
        # Nettoyer le fichier existant temporaire
        if existing_excel_path and os.path.exists(existing_excel_path):
            os.remove(existing_excel_path)
        
        if not excel_results['success']:
            return jsonify({
                'error': 'Erreur lors de la création du fichier Excel',
                'details': excel_results['errors']
            }), 500
        
        logger.info("=== EXTRACTION PDF EN LOT TERMINÉE AVEC SUCCÈS ===")
        
        # Retourner les résultats
        return jsonify({
            'success': True,
            'message': f'Extraction en lot terminée avec succès',
            'filename': output_filename,
            'download_url': f'/download/{output_filename}',
            'statistics': {
                'total_files': len(pdf_files),
                'processed_successfully': len(processed_files),
                'total_invoices_in_excel': excel_results['processed_invoices'],
                'errors': len(processing_errors)
            },
            'processed_files': processed_files,
            'processing_errors': processing_errors[:10] if processing_errors else []  # Limiter à 10 erreurs dans la réponse
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction PDF en lot: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Télécharge un fichier depuis le dossier output"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            logger.info(f"Téléchargement du fichier: {filename}")
            return send_file(file_path, as_attachment=True)
        else:
            logger.error(f"Fichier non trouvé: {filename}")
            return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement: {str(e)}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

def open_browser():
    """Ouvre le navigateur après un délai"""
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Lancer le navigateur dans un thread séparé
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Démarrer l'application Flask
    logger.info("Démarrage du serveur Flask...")
    app.run(debug=True, use_reloader=False, port=5000)
