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
    """Parse une chaîne de date en format DD/MM/YYYY, avec support des mois en texte italien/français"""
    if not date_str:
        return ''
    
    try:
        # Dictionnaire de conversion des mois italiens
        italian_months = {
            'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
            'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
            'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
        }
        
        # Dictionnaire de conversion des mois français
        french_months = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        # Dictionnaire des mois allemands
        german_months = {
            'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
            'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
            'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
        }
        
        # Dictionnaire des mois anglais
        english_months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        # Vérifier si c'est un tuple (jour, mois_texte, année) depuis les patterns regex
        if isinstance(date_str, tuple) and len(date_str) == 3:
            day, month_text, year = date_str
            month_text = month_text.lower()
            
            # Chercher le mois dans les dictionnaires
            month_num = (italian_months.get(month_text) or 
                        french_months.get(month_text) or 
                        german_months.get(month_text) or 
                        english_months.get(month_text))
            if month_num:
                return f"{day.zfill(2)}/{month_num}/{year}"
        
        date_input = str(date_str).strip()
        
        # Traitement des dates avec mois en texte (format "DD mois YYYY")
        text_date_pattern = r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
        
        match = re.search(text_date_pattern, date_input, re.IGNORECASE)
        if match:
            day, month_text, year = match.groups()
            month_text = month_text.lower()
            
            # Chercher le mois dans tous les dictionnaires
            month_num = (italian_months.get(month_text) or 
                        french_months.get(month_text) or 
                        german_months.get(month_text) or 
                        english_months.get(month_text))
            if month_num:
                return f"{day.zfill(2)}/{month_num}/{year}"
        
        # Essayer les formats numériques classiques
        formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y', '%m.%d.%Y']
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_input, fmt)
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                continue
        
        # Si aucun format ne marche, retourner vide (pas la chaîne originale)
        return ''
        
    except Exception as e:
        logger.warning(f"Erreur lors du parsing de date '{date_str}': {e}")
        return ''

def parse_amazon_invoice_data(text, debug_mode=False, filename=''):
    """
    Parse les données d'une facture Amazon à partir du texte extrait
    Retourne un dictionnaire avec les données structurées
    """
    debug_info = []
    
    try:
        if debug_mode:
            debug_info.append(f"Texte à parser (longueur: {len(text)})")
            debug_info.append(f"Début du texte: {text[:200]}...")
            debug_info.append(f"Nom de fichier: {filename}")
        
        # Vérification préalable : est-ce bien un document Amazon ?
        amazon_keywords = [
            'amazon', 'Amazon', 'AMAZON',
            'invoice', 'Invoice', 'INVOICE',
            'facture', 'Facture', 'FACTURE', 
            'fattura', 'Fattura', 'FATTURA',
            'order', 'Order', 'ORDER',
            'commande', 'Commande', 'COMMANDE',
            'ordine', 'Ordine', 'ORDINE',
            # Ajout de patterns Amazon spécifiques
            'INV-', 'FR500', 'FR199', 'EU SARL', 'amazon.com',
            'Business EU', 'Marketplace'
        ]
        
        # Vérifier si au moins un mot-clé Amazon est présent
        has_amazon_context = any(keyword in text for keyword in amazon_keywords)
        
        if not has_amazon_context:
            if debug_mode:
                debug_info.append("Document rejeté: pas de contexte Amazon détecté")
                debug_info.append(f"Mots-clés recherchés: {amazon_keywords}")
            return None
        
        if debug_mode:
            debug_info.append("Contexte Amazon détecté, début du parsing...")
            found_keywords = [kw for kw in amazon_keywords if kw in text]
            debug_info.append(f"Mots-clés Amazon trouvés: {found_keywords}")
        
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
        patterns = {            'order_id': [
                # Pattern spécifique pour les factures italiennes Amazon
                r'Contratto\s+(\d{3}-\d{7}-\d{7})',
                # Patterns existants pour les autres langues
                r'Order\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
                r'Commande\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
                r'Ordine\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
                r'Bestellung\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
                r'\b(\d{3}-\d{7}-\d{7})\b'
            ],            'invoice_number': [
                # Pattern spécifique pour les factures italiennes Amazon
                r'Numero fattura\s+([A-Z]{2}\d{4,8}[A-Z]{2,8})',
                # Patterns existants avec FR + chiffres + lettres
                r'\b(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)\b',
                r'\b([A-Z]{2}\d{4,8}[A-Z]{2,8}[A-Z0-9]*)\b',
                # Patterns pour l'encadré "Payé"
                r'Payé.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                r'Paid.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                r'Pagato.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                # Patterns pour "Numéro de la facture"
                r'Numéro\s*de\s*la\s*facture[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                r'Invoice\s*Number[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                r'Numero\s*della\s*fattura[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
                # Patterns Amazon INV existants
                r'Invoice\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'Facture\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'Fattura\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
                r'\b(INV-[A-Z]{2}-[A-Z0-9-]+)\b'
            ],            'date': [
                # Pattern spécifique pour les factures italiennes avec mois en texte
                r'Data\s*di\s*fatturazione[^0-9]*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                # Patterns existants pour les autres langues avec mois en texte
                r'Data\s*di\s*consegna.*?(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'Data\s*ordine.*?(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'Date\s*de\s*facturation.*?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'Date\s*de\s*commande.*?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                # Patterns génériques pour dates avec mois en texte
                r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                r'(\d{1,2})\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})',
                # Patterns pour dates numériques
                r'Data\s*di\s*fatturazione[:\s/]*(\d{1,2}/\d{1,2}/\d{4})',
                r'Invoice\s*Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                r'Date\s*de\s*facturation[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
                r'(\d{1,2}\.\d{1,2}\.\d{4})'
            ],            'country': [
                # Patterns spécifiques pour pays européens (en premier pour éviter les faux positifs)
                r'\b(IT|FR|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b',
                # Patterns pour codes postal + pays
                r'(\d{5})\s*\n([A-Z]{2})(?:\s|$)',
                r'(\d{5})\s*([A-Z]{2})(?:\s|$)',
                # Patterns pour codes pays seuls en fin de ligne
                r'\n([A-Z]{2})\s*$',
                r'\b([A-Z]{2})\s*$',
                # Patterns contextuels pour adresses
                r'(?:Ship\s*to|Livraison|Spedire\s*a|Address|Indirizzo)[\s\S]*?(\d{5})\s*([A-Z]{2})',
                r'(?:Ship\s*to|Livraison|Spedire\s*a|Address|Indirizzo)[\s\S]*?([A-Z]{2})\s*\d{4,5}',
                # Fallback sur les patterns d'adresse
                r'destinazione.*?([A-Z]{2})\b'
            ],'customer_name': [
                # Pattern spécifique pour les factures italiennes
                r'Totale da pagare.*?([A-Z][A-Z\s]+[A-Z])',
                # Patterns existants pour les autres langues
                r'Ship\s*to[:\s]+([A-Za-z\s]{3,50})',
                r'Livraison[:\s]+([A-Za-z\s]{3,50})',
                r'Spedire\s*a[:\s]+([A-Za-z\s]{3,50})',
                r'Bill\s*to[:\s]+([A-Za-z\s]{3,50})',
                r'Facturation[:\s]+([A-Za-z\s]{3,50})',
                r'Fatturazione[:\s]+([A-Za-z\s]{3,50})'
            ],            'total_amount': [
                # Pattern spécifique pour les factures italiennes (priorité maximale)
                r'Totale fattura\s+(\d+,\d{2})\s*€',
                # Patterns spécifiques avec contexte (priorité élevée)
                r'Total\s*de\s*la\s*facture[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'(?<!Sub)Total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Grand\s*Total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Amount\s*Due[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                # Patterns génériques (priorité plus faible)
                r'Totale\s*fattura[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Totale[:\s]+(\d+[,.]?\d{0,2})\s*[€]',
                r'(\d+[,.]?\d{2})\s*[€]?\s*(?=\s*$|\s*\n)'
            ],'tax_amount': [
                # Pattern spécifique pour les factures italiennes
                r'(\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€',
                # Patterns existants pour les autres langues
                r'IVA[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Tax[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'TVA[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'VAT[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'(?:TVA|VAT|IVA)\s*[:\s]*(\d+[,.]?\d{0,2})\s*[€%]'
            ],
            'tax_rate': [
                # Pattern spécifique pour les factures italiennes
                r'(\d+)%\s+[\d,]+\s*€\s+[\d,]+\s*€',
                # Patterns existants
                r'IVA\s*(\d+[,.]?\d*)\s*%',
                r'TVA\s*(\d+[,.]?\d*)\s*%',
                r'VAT\s*(\d+[,.]?\d*)\s*%',
                r'(\d+[,.]?\d*)\s*%'
            ],
            'subtotal': [
                # Pattern spécifique pour les factures italiennes
                r'(\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€',
                # Patterns existants
                r'Subtotale[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Subtotal[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Sous-total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Sub-total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Net\s*Amount[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'Montant\s*HT[:\s]+[€$]?(\d+[,.]?\d{0,2})',
                r'(\d+[,.]?\d{2})\s*[€]?\s*(?=.*?(?:TVA|VAT|IVA))'
            ]
        }# Extraire les données avec les patterns
        dates_found = []
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Gérer les patterns avec groupes multiples (dates italiennes)
                    if key == 'date' and len(match.groups()) > 1:
                        # Pattern avec jour, mois, année séparés
                        value = match.groups()
                        if debug_mode:
                            debug_info.append(f"Pattern '{key}' trouvé: {value}")
                        parsed_date = parse_date_string(value)
                        if parsed_date:
                            dates_found.append(parsed_date)
                            if not invoice_data['date_facture']:  # Prendre la première date trouvée
                                invoice_data['date_facture'] = parsed_date
                    else:
                        # Pattern avec un seul groupe
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
                                dates_found.append(parsed_date)
                                if not invoice_data['date_facture']:  # Prendre la première date trouvée
                                    invoice_data['date_facture'] = parsed_date
                        elif key == 'country':
                            # Pour les patterns avec deux groupes (code postal + pays)
                            if len(match.groups()) == 2:
                                # Prendre le deuxième groupe (le code pays)
                                country_code = match.groups()[1].upper()
                                if debug_mode:
                                    debug_info.append(f"Pattern country avec 2 groupes: {match.groups()}, code pays: {country_code}")
                            else:
                                # Pattern simple
                                country_code = value.upper()
                                if debug_mode:
                                    debug_info.append(f"Pattern country simple: {value}, code pays: {country_code}")
                            
                            # Valider que c'est un vrai code pays (2 lettres majuscules)
                            if len(country_code) == 2 and country_code.isalpha():
                                # Ne pas écraser si on a déjà un pays valide (premier match gagne)
                                if not invoice_data['pays']:
                                    invoice_data['pays'] = country_code
                                    if debug_mode:
                                        debug_info.append(f"Code pays défini: {country_code}")
                                    break  # Sortir de la boucle des patterns une fois qu'on a trouvé
                        elif key == 'customer_name':
                            name = re.sub(r'[0-9\n\r]+', ' ', value).strip()
                            if len(name) > 3:
                                invoice_data['nom_contact'] = name[:50]
                        elif key == 'total_amount':
                            try:
                                # Remplacer les virgules par des points et nettoyer
                                clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                invoice_data['total'] = float(clean_value)
                            except ValueError:
                                pass
                        elif key == 'tax_amount':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) == 3:
                                    # Pattern: (\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€
                                    # Groupe 3 = montant TVA
                                    clean_value = match.groups()[2].replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['tva'] = float(clean_value)
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['tva'] = float(clean_value)
                            except ValueError:
                                pass
                        elif key == 'tax_rate':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) >= 1:
                                    # Prendre le premier groupe (le taux)
                                    clean_value = match.groups()[0].replace(',', '.').replace(' ', '')
                                    rate_float = float(clean_value)
                                    invoice_data['taux_tva'] = f"{rate_float:.2f}%"
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '')
                                    rate_float = float(clean_value)
                                    invoice_data['taux_tva'] = f"{rate_float:.2f}%"
                            except ValueError:
                                pass
                        elif key == 'subtotal':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) == 3:
                                    # Pattern: (\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€
                                    # Groupe 2 = montant HT
                                    clean_value = match.groups()[1].replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['ht'] = float(clean_value)
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['ht'] = float(clean_value)
                            except ValueError:
                                pass
        
        # Si aucune date n'a été trouvée avec les patterns spécifiques, essayer d'en extraire une générique
        if not invoice_data['date_facture']:
            generic_date_patterns = [
                r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)',
                r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{1,2})-(\d{1,2})-(\d{4})',
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
            ]
            
            for pattern in generic_date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:
                        parsed_date = parse_date_string(match.groups())
                        if parsed_date:
                            invoice_data['date_facture'] = parsed_date
                            if debug_mode:
                                debug_info.append(f"Date générique trouvée: {parsed_date}")
                            break
          # Si aucun pays n'a été trouvé, utiliser fallback simple
        if not invoice_data['pays']:
            # Recherche simple des codes pays européens
            country_fallback = re.search(r'\b(IT|FR|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b', text)
            if country_fallback:
                invoice_data['pays'] = country_fallback.group(1)
                if debug_mode:
                    debug_info.append(f"Pays détecté par fallback: {country_fallback.group(1)}")
        
        if debug_mode and dates_found:
            debug_info.append(f"Toutes les dates trouvées: {dates_found}")
          # Calculer les valeurs manquantes
        if invoice_data['total'] > 0 and invoice_data['tva'] > 0 and invoice_data['ht'] == 0:
            invoice_data['ht'] = invoice_data['total'] - invoice_data['tva']
        elif invoice_data['total'] == 0 and invoice_data['ht'] > 0 and invoice_data['tva'] > 0:
            invoice_data['total'] = invoice_data['ht'] + invoice_data['tva']
        
        # Si on n'a pas de taux de TVA mais qu'on a HT et TVA, le calculer
        # Sinon, utiliser le taux détecté directement
        if not invoice_data['taux_tva'] and invoice_data['ht'] > 0 and invoice_data['tva'] > 0:
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
                  # Vérifier si le DataFrame a les bonnes colonnes (nouvelle structure sans N°)
                expected_columns = ['ID AMAZON', 'Facture AMAZON', 'Date Facture', 'Pays', 'Nom contact', 'HT', 'TVA', 'Taux TVA', 'TOTAL']
                if all(col in existing_df.columns for col in expected_columns):
                    # Convertir les données existantes en format de liste
                    for _, row in existing_df.iterrows():
                        # Éviter les lignes de totaux (vérifier que l'ID Amazon n'est pas vide)
                        if pd.notna(row['ID AMAZON']) and str(row['ID AMAZON']).strip():
                            rows_data.append({
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
        # Ajouter les nouvelles données de factures (sans numéro)
        for invoice in invoices_data:
            rows_data.append({
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
        
        logger.info(f"Totaux calculés - HT: {total_ht:.2f}, TVA: {total_tva:.2f}, TTC: {total_ttc:.2f}")        # Créer le DataFrame avec la structure attendue (sans colonne N°)
        df_data = []
        
        # Première ligne avec les totaux (exactement comme dans votre exemple CSV)
        # Structure: 5 colonnes vides + HT + TVA + colonne vide + TOTAL = 9 colonnes
        df_data.append(['', '', '', '', '', f"{total_ht:.2f}", f"{total_tva:.2f}", '', f"{total_ttc:.2f}"])
        
        # Ligne d'en-têtes (9 colonnes exactement)
        df_data.append(['ID AMAZON', 'Facture AMAZON', 'Date Facture', 'Pays', 'Nom contact', 'HT', 'TVA', 'Taux TVA', 'TOTAL'])
        
        # Données des factures (sans numéro de ligne)
        for row in rows_data:
            df_data.append([
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
                if not pdf_file.filename or not pdf_file.filename.lower().endswith('.pdf'):
                    processing_errors.append(f"Fichier ignoré (non PDF): {pdf_file.filename or 'Nom inconnu'}")
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

@app.route('/process_files', methods=['POST'])
def process_files():
    """Traite les fichiers CSV Shopify (commandes, transactions, journal)"""
    logger.info("=== DÉBUT DU TRAITEMENT CSV SHOPIFY ===")
    uploaded_files = {}
    try:
        # Vérifier le mode de traitement
        processing_mode = request.form.get('processing_mode', 'new')
        
        # Vérifier les fichiers requis
        required_files = ['commandes_file', 'transactions_file', 'journal_file']
        
        for file_key in required_files:
            if file_key not in request.files:
                return jsonify({'error': f'Fichier manquant: {file_key}'}), 400
            
            file = request.files[file_key]
            if file.filename == '' or file.filename is None:
                return jsonify({'error': f'Aucun fichier sélectionné pour: {file_key}'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': f'Type de fichier non autorisé: {file.filename}'}), 400
            
            # Sauvegarder le fichier temporairement
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, f"{file_key}_{filename}")
            file.save(file_path)
            uploaded_files[file_key] = file_path
            logger.info(f"Fichier sauvegardé: {file_key} -> {file_path}")
        
        # Traitement en mode "Nouveau fichier" ou "Combiner"
        if processing_mode == 'combine':
            # Vérifier s'il y a un fichier existant à combiner
            if 'old_file' in request.files:
                old_file = request.files['old_file']
                if old_file.filename and allowed_file(old_file.filename):
                    old_filename = secure_filename(old_file.filename)
                    old_file_path = os.path.join(UPLOAD_FOLDER, f"existing_{old_filename}")
                    old_file.save(old_file_path)
                    logger.info(f"Fichier existant sauvegardé: {old_file_path}")
                    # TODO: Implémenter la logique de combinaison
                else:
                    logger.warning("Fichier existant non valide, traitement en mode nouveau")
                    processing_mode = 'new'
        
        # Générer le nom du fichier de sortie
        timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        output_filename = f"Compta_LCDI_Shopify_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # TODO: Traiter les fichiers CSV avec la logique existante
        # Pour l'instant, créer un fichier vide en attendant l'implémentation complète
        import pandas as pd
        df_placeholder = pd.DataFrame([
            ['En cours de développement'],
            ['Les fichiers ont été reçus:'],
            [f"- Commandes: {uploaded_files.get('commandes_file', 'N/A')}"],
            [f"- Transactions: {uploaded_files.get('transactions_file', 'N/A')}"],
            [f"- Journal: {uploaded_files.get('journal_file', 'N/A')}"],
            [f"- Mode: {processing_mode}"]
        ])
        df_placeholder.to_excel(output_path, index=False, header=False)
          # Nettoyer les fichiers temporaires
        for file_path in uploaded_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        
        logger.info(f"Fichier CSV Shopify créé: {output_filename}")
        return jsonify({
            'success': True,
            'message': 'Traitement CSV Shopify terminé (version de développement)',
            'filename': output_filename,
            'download_url': f'/download/{output_filename}',
            'note': 'Cette fonctionnalité est en cours de développement. Un fichier de test a été généré.'
        })
        
    except Exception as e:
        # Nettoyer les fichiers temporaires en cas d'erreur
        try:
            # Vérifier si uploaded_files a été créé avant l'erreur
            if 'uploaded_files' in locals():
                for file_path in uploaded_files.values():
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
        
        logger.error(f"Erreur lors du traitement CSV Shopify: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@app.route('/debug_pdf_extraction', methods=['POST'])
def debug_pdf_extraction():
    """Mode debug pour analyser l'extraction PDF en détail"""
    logger.info("=== DÉBUT DU DEBUG PDF ===")
    pdf_path = None  # Initialiser la variable
    
    try:
        # Vérifier si un fichier PDF a été uploadé
        logger.debug(f"Request files: {list(request.files.keys())}")
        logger.debug(f"Request form: {dict(request.form)}")
        
        if 'debug_pdf_files' not in request.files:
            return jsonify({'error': 'Aucun fichier PDF sélectionné pour le debug'}), 400
        
        pdf_file = request.files['debug_pdf_files']
        if pdf_file.filename == '' or pdf_file.filename is None:
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier l'extension
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Le fichier doit être un PDF'}), 400
        
        # Récupérer la méthode d'extraction
        extraction_method = request.form.get('debug_extraction_method', 'auto')
        
        # Sauvegarder temporairement
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, f"debug_{filename}")
        pdf_file.save(pdf_path)
        
        logger.info(f"Debug PDF: {filename} avec méthode {extraction_method}")
        
        # Extraire les données du PDF
        pdf_results = process_pdf_extraction(pdf_path, extraction_method)
        
        # Résultats du debug
        debug_results = {
            'filename': filename,
            'extraction_method': extraction_method,
            'file_size': os.path.getsize(pdf_path),
            'extraction_success': pdf_results['success'],
            'text_extracted': bool(pdf_results.get('text')),
            'text_length': len(pdf_results.get('text', '')),
            'text_preview': pdf_results.get('text', '')[:500] if pdf_results.get('text') else '',
            'tables_found': len(pdf_results.get('tables', [])),
            'tables_preview': [],
            'errors': pdf_results.get('errors', []),
            'parsing_result': None,
            'parsing_success': False,
            'parsing_errors': []
        }
        
        # Aperçu des tableaux
        if pdf_results.get('tables'):
            for i, table in enumerate(pdf_results['tables'][:3]):  # Limiter à 3 tableaux
                try:
                    if isinstance(table, list) and table:
                        # Tableau au format liste de listes
                        table_preview = {
                            'table_index': i + 1,
                            'rows': len(table),
                            'columns': len(table[0]) if table[0] else 0,
                            'preview': table[:3] if len(table) >= 3 else table  # 3 premières lignes
                        }
                        debug_results['tables_preview'].append(table_preview)
                except Exception as e:
                    debug_results['tables_preview'].append({
                        'table_index': i + 1,
                        'error': f"Erreur lors de l'analyse du tableau: {str(e)}"                    })
        
        # Tenter le parsing Amazon si on a du texte
        if pdf_results.get('text'):
            try:
                text_to_parse = pdf_results['text']
                
                # Si pas de texte mais des tableaux, essayer d'extraire le texte des tableaux
                if not text_to_parse and pdf_results['tables']:
                    text_parts = []
                    for table in pdf_results['tables']:
                        try:
                            if isinstance(table, list):
                                text_parts.append(' '.join([str(cell) for row in table for cell in row if cell]))
                        except Exception:
                            continue
                    text_to_parse = ' '.join(text_parts)
                
                if text_to_parse:
                    parsing_result = parse_amazon_invoice_data(text_to_parse, debug_mode=True)
                    if parsing_result:
                        debug_results['parsing_result'] = parsing_result
                        debug_results['parsing_success'] = True
                        logger.info("Debug: Parsing Amazon réussi")
                    else:
                        debug_results['parsing_errors'].append("Impossible de parser les données Amazon")
                        logger.warning("Debug: Parsing Amazon échoué")
                else:
                    debug_results['parsing_errors'].append("Aucun texte disponible pour le parsing")
            except Exception as e:
                debug_results['parsing_errors'].append(f"Erreur lors du parsing: {str(e)}")
                logger.error(f"Erreur debug parsing: {str(e)}")
        else:
            debug_results['parsing_errors'].append("Aucun texte extrait du PDF")
        
        # Nettoyer le fichier temporaire
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        logger.info("=== FIN DU DEBUG PDF ===")
        
        return jsonify({
            'success': True,
            'debug_results': debug_results
        })
        
    except Exception as e:
        # Nettoyer le fichier temporaire en cas d'erreur
        try:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass  # Ignore les erreurs lors du nettoyage
        
        logger.error(f"Erreur lors du debug PDF: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

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
