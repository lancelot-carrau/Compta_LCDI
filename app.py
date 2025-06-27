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
    """Convertir différents formats de date vers DD/MM/YYYY"""
    
    if not date_str:
        return None
    
    logger.info(f"   [DATE_PARSE] Format reçu: {date_str}")
    
    # Dictionnaire des mois italiens
    italian_months = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
    }
    
    # Dictionnaire des mois français
    french_months = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
    }
    
    # Dictionnaire des mois espagnols
    spanish_months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    # Dictionnaire des mois néerlandais
    dutch_months = {
        'januari': '01', 'februari': '02', 'maart': '03', 'april': '04',
        'mei': '05', 'juni': '06', 'juli': '07', 'augustus': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
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
                    spanish_months.get(month_text) or 
                    dutch_months.get(month_text) or 
                    german_months.get(month_text) or 
                    english_months.get(month_text))
        if month_num:
            return f"{day.zfill(2)}/{month_num}/{year}"
    
    date_input = str(date_str).strip()
    
    # Traitement des dates avec mois en texte (format "DD mois YYYY")
    text_date_pattern = r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
    
    match = re.search(text_date_pattern, date_input, re.IGNORECASE)
    if match:
        day, month_text, year = match.groups()
        month_text = month_text.lower()
        
        # Chercher le mois dans tous les dictionnaires
        month_num = (italian_months.get(month_text) or 
                    french_months.get(month_text) or 
                    spanish_months.get(month_text) or 
                    dutch_months.get(month_text) or 
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
    
    logger.info(f"   [DATE_PARSE] Échec parsing: {date_str}")
    return None

def extract_date_from_paid_box(text):
    """Extraire la date de facture avec priorité à 'Data di fatturazione' puis fallback sur 'Payé/Remboursé'"""
    
    # Dictionnaire des mois en différentes langues
    months_dict = {
        # Français
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12',
        
        # Anglais
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        
        # Allemand
        'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
        'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12',
        
        # Italien
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
        
        # Espagnol
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        
        # Néerlandais
        'januari': '01', 'februari': '02', 'maart': '03', 'april': '04',
        'mei': '05', 'juni': '06', 'juli': '07', 'augustus': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'december': '12',
        
        # Versions courtes communes
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # PRIORITÉ 1: Recherche de "Data di fatturazione" / "Date de facture" / etc.
    invoice_date_keywords = [
        'Data di fatturazione', 'Date de la facture', 'Invoice date', 'Fecha de la factura',
        'Factuurdatum', 'Rechnungsdatum', 'Data fattura', 'Date facture'
    ]
    
    # PRIORITÉ 0 (ABSOLUE): Recherche des dates d'émission de notes de crédit / avoirs (POUR REMBOURSEMENTS)
    credit_note_date_keywords = [
        'Date d\'émission de l\'avoir', 'Creditnotadatum', 'Data emissione nota di credito',
        'Fecha de emisión de la nota de crédito', 'Credit note date', 'Gutschrift Datum',
        'Datum van de creditnota', 'Date de la note de crédit', 'Data nota di credito',
        'émission de l\'avoir', 'émission.*?avoir'  # Patterns plus flexibles pour FR5000FSHCVZJC
    ]
    
    # PRIORITÉ ABSOLUE : Dates d'émission de notes de crédit (remboursements)
    for keyword in credit_note_date_keywords:
        # Pattern plus flexible - peut aussi chercher directement les dates après le mot-clé  
        if keyword == 'émission de l\'avoir' or keyword == 'émission.*?avoir':
            # Pattern spécial pour extraire directement "Date d'émission de l'avoir 05 mai 2025"
            # Utiliser . pour capturer n'importe quel type d'apostrophe
            special_pattern = r"Date\s+d.émission\s+de\s+l.avoir\s+(\d{1,2}\s+[a-zA-ZÀ-ÿ]+\s+\d{4})"
            special_matches = re.finditer(special_pattern, text, re.IGNORECASE)
            for match in special_matches:
                date_str = match.group(1)
                logger.info(f"   [CREDIT_NOTE_DATE] Pattern spécial trouvé: {date_str}")
                formatted_date = parse_date_string(date_str)
                if formatted_date:
                    logger.info(f"   [CREDIT_NOTE_DATE] Formaté: {formatted_date}")
                    return formatted_date
        
        keyword_pattern = re.escape(keyword)
        for keyword_match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            # Récupérer 200 caractères après le mot-clé
            start = keyword_match.end()
            end = min(len(text), start + 200)
            context = text[start:end]
            
            # Recherche du pattern DD Month YYYY dans ce contexte
            date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            date_matches = re.findall(date_pattern, context, re.IGNORECASE)
            
            for day, month_name, year in date_matches:
                month_lower = month_name.lower().strip()
                
                # Vérifier si le mois est dans notre dictionnaire
                if month_lower in months_dict:
                    logger.info(f"   [CREDIT_NOTE_DATE] Trouvé dans contexte '{keyword}': {day} {month_name} {year}")
                    
                    # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
                    date_tuple = (day, month_name, year)
                    formatted_date = parse_date_string(date_tuple)
                    
                    if formatted_date:
                        logger.info(f"   [CREDIT_NOTE_DATE] Formaté: {formatted_date}")
                        return formatted_date
            
            # Recherche de dates numériques DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
            numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
            numeric_matches = re.findall(numeric_date_pattern, context)
            
            for day, month, year in numeric_matches:
                logger.info(f"   [CREDIT_NOTE_DATE] Date numérique trouvée dans contexte '{keyword}': {day}-{month}-{year}")
                
                # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
                numeric_date = f"{day}-{month}-{year}"
                formatted_date = parse_date_string(numeric_date)
                
                if formatted_date:
                    logger.info(f"   [CREDIT_NOTE_DATE] Formaté: {formatted_date}")
                    return formatted_date
    
    # PRIORITÉ 1: Recherche de "Data di fatturazione" / "Date de facture" / etc. (POUR FACTURES NORMALES)
    for keyword in invoice_date_keywords:
        keyword_pattern = re.escape(keyword)
        for keyword_match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            # Récupérer 200 caractères après le mot-clé
            start = keyword_match.end()
            end = min(len(text), start + 200)
            context = text[start:end]
            
            # Recherche du pattern DD Month YYYY dans ce contexte
            date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            date_matches = re.findall(date_pattern, context, re.IGNORECASE)
            
            for day, month_name, year in date_matches:
                month_lower = month_name.lower().strip()
                
                # Vérifier si le mois est dans notre dictionnaire
                if month_lower in months_dict:
                    logger.info(f"   [INVOICE_DATE] Trouvé dans contexte '{keyword}': {day} {month_name} {year}")
                    
                    # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
                    date_tuple = (day, month_name, year)
                    formatted_date = parse_date_string(date_tuple)
                    
                    if formatted_date:
                        logger.info(f"   [INVOICE_DATE] Formaté: {formatted_date}")
                        return formatted_date
            
            # Recherche de dates numériques DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
            numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
            numeric_matches = re.findall(numeric_date_pattern, context)
            
            for day, month, year in numeric_matches:
                logger.info(f"   [INVOICE_DATE] Date numérique trouvée dans contexte '{keyword}': {day}-{month}-{year}")
                
                # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
                numeric_date = f"{day}-{month}-{year}"
                formatted_date = parse_date_string(numeric_date)
                
                if formatted_date:
                    logger.info(f"   [INVOICE_DATE] Formaté: {formatted_date}")
                    return formatted_date
    
    # PRIORITÉ 2: Fallback sur les termes "Payé" ou "Remboursé" (ancienne logique)
    paid_keywords = [
        'payé', 'paid', 'betaald', 'pagato', 'pagado', 'bezahlt',
        'remboursé', 'refunded', 'terugbetaald', 'rimborsato', 'reembolsado', 'erstattet'
    ]
    
    # Construire le pattern pour les mots-clés
    keywords_pattern = '|'.join(paid_keywords)
    
    # Recherche du contexte autour des mots-clés avec date
    for keyword_match in re.finditer(f'({keywords_pattern})', text, re.IGNORECASE):
        # Récupérer 200 caractères autour du mot-clé
        start = max(0, keyword_match.start() - 100)
        end = min(len(text), keyword_match.end() + 100)
        context = text[start:end]
        
        # Recherche du pattern DD Month YYYY dans ce contexte
        date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
        date_matches = re.findall(date_pattern, context, re.IGNORECASE)
        
        for day, month_name, year in date_matches:
            month_lower = month_name.lower().strip()
            
            # Vérifier si le mois est dans notre dictionnaire
            if month_lower in months_dict:
                logger.info(f"   [PAID_BOX_DATE] Trouvé dans contexte '{keyword_match.group()}': {day} {month_name} {year}")
                
                # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
                date_tuple = (day, month_name, year)
                formatted_date = parse_date_string(date_tuple)
                
                if formatted_date:
                    logger.info(f"   [PAID_BOX_DATE] Formaté: {formatted_date}")
                    return formatted_date
        
        # Recherche de dates numériques DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
        numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
        numeric_matches = re.findall(numeric_date_pattern, context)
        
        for day, month, year in numeric_matches:
            logger.info(f"   [PAID_BOX_DATE] Date numérique trouvée dans contexte '{keyword_match.group()}': {day}-{month}-{year}")
            
            # Utiliser parse_date_string pour assurer un formatage uniforme DD/MM/YYYY
            numeric_date = f"{day}-{month}-{year}"
            formatted_date = parse_date_string(numeric_date)
            
            if formatted_date:
                logger.info(f"   [PAID_BOX_DATE] Formaté: {formatted_date}")
                return formatted_date
    
    logger.info(f"   [DATE_EXTRACTION] Aucune date trouvée dans les sections de date de facture")
    return None

def extract_data_from_filename(filename):
    """
    Extrait les données disponibles depuis le nom du fichier (SANS la date).
    La date sera récupérée depuis l'encadré "Payé"/"Remboursé" dans le PDF.
    
    Formats supportés:
    - Standard ancien: "1774 TVA 21,00% BE 2025-01-03 FR500003HCVZJU 1103,97€.pdf"
    - Format BE UOSS: "INV-FR-UOSS-20250114-BE-AMAZON_EU_0193797666666_20250114_233_408-932-5843251_VF.pdf"
    - Format Standard Amazon: "INVOICE-ES-2024-12-20-ES-AMAZON_EU_ES12345678901_456-789-1234567.pdf"
    
    Args:
        filename: Nom du fichier PDF
        
    Returns:
        dict: Données extraites (country, invoice_number, amount, vat_rate) - PAS de date
    """
    try:
        import re
        
        result = {
            'pays': "",
            'facture_amazon': "",
            'montant_total': "",
            'taux_tva': ""
        }
        
        # PATTERN 1: Format BE UOSS - "INV-FR-UOSS-YYYYMMDD-BE-AMAZON_EU_..."
        pattern_be_uoss = r'(INV-FR-UOSS-(\d{8})-BE)-AMAZON_EU_[A-Z0-9]+_\d+_\d+_[\d-]+_VF\.pdf'
        match_be = re.search(pattern_be_uoss, filename, re.IGNORECASE)
        if match_be:
            facture_number = match_be.group(1)  # INV-FR-UOSS-20250114-BE
            
            result['pays'] = 'BE'
            result['facture_amazon'] = facture_number
            
            logger.info(f"Extraction BE UOSS réussie: pays=BE, facture={facture_number}")
            return result
        
        # PATTERN 2: Format Standard Amazon - "INVOICE-XX-YYYY-MM-DD-XX-AMAZON_EU_..."
        pattern_standard = r'INVOICE-([A-Z]{2})-(\d{4})-(\d{2})-(\d{2})-\1-AMAZON_EU_([A-Z0-9]+)_[\d-]+\.pdf'
        match_std = re.search(pattern_standard, filename, re.IGNORECASE)
        if match_std:
            pays = match_std.group(1).upper()
            invoice_id = match_std.group(5)
            
            # Vérifier que c'est un code pays valide
            valid_countries = ['FR', 'IT', 'ES', 'NL', 'BE', 'DE', 'MT', 'LU', 'AT', 'PT']
            if pays in valid_countries:
                result['pays'] = pays
                
                # Construction du numéro de facture pour les pays non-BE
                if pays != 'BE':
                    year = match_std.group(2)
                    month = match_std.group(3)
                    day = match_std.group(4)
                    result['facture_amazon'] = f"INVOICE-{pays}-{year}-{month}-{day}"
                
                logger.info(f"Extraction Amazon standard réussie: pays={pays}")
                return result
        
        # PATTERN 3: Format ancien avec TVA - "NUMERO_TVA_XX_PAYS_DATE_FACTURE_MONTANT.pdf" (après secure_filename)
        pattern_ancien_secure = r'(\d+)_TVA_(\d+)_([A-Z]{2})_(\d{4}-\d{2}-\d{2})_((?:INV-FR-UOSS-[\d-]+(?:-[A-Z]{2})?|FR\w+))_(\d+)\.pdf'
        match_ancien_secure = re.search(pattern_ancien_secure, filename, re.IGNORECASE)
        if match_ancien_secure:
            numero = match_ancien_secure.group(1)
            taux_tva_num = match_ancien_secure.group(2)
            pays = match_ancien_secure.group(3).upper()
            facture = match_ancien_secure.group(5)
            montant = match_ancien_secure.group(6)
            
            # Reconstituer le taux de TVA avec %
            taux_tva = f"{int(taux_tva_num)/100:.0f}%"
            
            # Vérifier que c'est un code pays valide
            valid_countries = ['FR', 'IT', 'ES', 'NL', 'BE', 'DE', 'MT', 'LU', 'AT', 'PT']
            if pays in valid_countries:
                result['pays'] = pays
            
            # Extraire la facture (UOSS ou FRXXXXX)
            result['facture_amazon'] = facture
            result['montant_total'] = montant
            result['taux_tva'] = taux_tva
            
            logger.info(f"Extraction ancien format secure réussie: pays={pays}, facture={result['facture_amazon']}")
            return result
        
        # PATTERN 4: Format ancien avec TVA - "NUMERO TVA XX,XX% PAYS DATE FACTURE MONTANT€.pdf" (format original)
        pattern_ancien = r'(\d+)\s+TVA\s+(\d+(?:,\d+)?%)\s+([A-Z]{2})\s+(\d{4}-\d{2}-\d{2})\s+((?:INV-FR-UOSS-[\d-]+(?:-[A-Z]{2})?|FR\w+))\s+([0-9,.-]+)€\.pdf'
        match_ancien = re.search(pattern_ancien, filename, re.IGNORECASE)
        if match_ancien:
            numero = match_ancien.group(1)
            taux_tva = match_ancien.group(2)
            pays = match_ancien.group(3).upper()
            facture = match_ancien.group(5)
            montant = match_ancien.group(6)
            
            # Vérifier que c'est un code pays valide
            valid_countries = ['FR', 'IT', 'ES', 'NL', 'BE', 'DE', 'MT', 'LU', 'AT', 'PT']
            if pays in valid_countries:
                result['pays'] = pays
            
            # Extraire la facture (UOSS ou FRXXXXX)
            result['facture_amazon'] = facture
            result['montant_total'] = montant
            result['taux_tva'] = taux_tva
            
            logger.info(f"Extraction ancien format réussie: pays={pays}, facture={result['facture_amazon']}")
            return result
        
        # Fallback: extraction individuelle du pays seulement
        pattern_country = r'TVA\s+\d+(?:,\d+)?%\s+([A-Z]{2})\b'
        match_country = re.search(pattern_country, filename, re.IGNORECASE)
        if match_country:
            country_code = match_country.group(1).upper()
            valid_countries = ['FR', 'IT', 'ES', 'NL', 'BE', 'DE', 'MT', 'LU', 'AT', 'PT']
            if country_code in valid_countries:
                result['pays'] = country_code
                logger.info(f"Extraction pays seul depuis nom fichier: {country_code}")
        
        return result
        
    except Exception as e:
        logger.warning(f"Erreur lors de l'extraction depuis le nom de fichier '{filename}': {e}")
        return {'pays': None, 'facture_amazon': None, 'date_facture': None, 'montant_total': None, 'taux_tva': None}

def extract_country_from_filename(filename):
    """
    Fonction de compatibilité - utilise extract_data_from_filename
    """
    data = extract_data_from_filename(filename)
    return data['pays']

def parse_amazon_invoice_data(text, debug_mode=False, filename='', pdf_path=None):
    """
    Parse les données d'une facture Amazon avec séparation stricte des méthodes :
    - MONTANTS (HT, TVA, TOTAL, taux TVA) : Analyse spatiale pdfplumber
    - AUTRES CHAMPS (ID Amazon, facture, date, pays, nom) : Extraction regex classique
    
    Args:
        text: Texte brut extrait du PDF
        debug_mode: Mode debug pour affichage détaillé  
        filename: Nom du fichier pour les logs
        pdf_path: Chemin vers le fichier PDF pour analyse spatiale
    
    Returns:
        dict: Données extraites ou None si échec
    """
    try:
        # Vérification rapide des mots-clés Amazon
        amazon_keywords = [
            'amazon', 'Amazon', 'AMAZON', 'amazon.', 
            'fattura', 'Fattura', 'FATTURA',
            'invoice', 'Invoice', 'INVOICE',
            'facture', 'Facture', 'FACTURE',
            'FR500', 'FR199', 'INV-', 'ASIN'
        ]
        
        if not any(keyword in text for keyword in amazon_keywords):
            return None
        
        # Données de la facture
        invoice_data = {
            'id_amazon': '',
            'facture_amazon': '',
            'date_facture': '',
            'pays': '',
            'nom_contact': '',
            'ht': 0.0,
            'tva': 0.0,
            'taux_tva': '',
            'total': 0.0
        }
        
        # === EXTRACTION DES DONNÉES DEPUIS LE NOM DE FICHIER (PRIORITAIRE) ===
        filename_data = {}
        if filename:
            filename_data = extract_data_from_filename(filename)
            
            # Code pays (prioritaire)
            if filename_data['pays']:
                invoice_data['pays'] = filename_data['pays']
                if debug_mode:
                    logger.info(f"   [FILENAME] Code pays extrait: {filename_data['pays']}")
            # Date : PRIORITÉ à l'encadré "Payé"/"Remboursé", puis regex comme fallback
            paid_box_date = extract_date_from_paid_box(text)
            if paid_box_date:
                invoice_data['date_facture'] = paid_box_date
                if debug_mode:
                    logger.info(f"   [PAID_BOX] Date extraite depuis encadré: {paid_box_date}")
            
            # Numéro de facture Amazon (prioritaire)
            if filename_data['facture_amazon']:
                invoice_data['facture_amazon'] = filename_data['facture_amazon']
                if debug_mode:
                    logger.info(f"   [FILENAME] Facture Amazon extraite: {filename_data['facture_amazon']}")
        
        # === ANALYSE SPATIALE AVEC PDFPLUMBER - MONTANTS UNIQUEMENT ===
        if pdf_path and pdf_path.lower().endswith('.pdf'):
            try:
                import pdfplumber
                if debug_mode:
                    logger.info(f"   [SPATIAL] Démarrage analyse spatiale pour: {pdf_path}")
                spatial_result = _extract_with_spatial_analysis(pdf_path, debug_mode)
                if debug_mode:
                    logger.info(f"   [SPATIAL] Résultat: {spatial_result}")
                if spatial_result:
                    # Fusionner UNIQUEMENT les montants issus de l'analyse spatiale
                    for key, value in spatial_result.items():
                        if value is not None and key in ['ht', 'tva', 'total', 'taux_tva']:  # Restriction aux montants
                            invoice_data[key] = value
                            if debug_mode:
                                logger.info(f"   [SPATIAL] {key}: {value}")
            except Exception as e:
                if debug_mode:
                    logger.warning(f"   Analyse spatiale échouée: {e}")
                    import traceback
                    logger.warning(f"   Traceback: {traceback.format_exc()}")
        
        # === PATTERNS REGEX POUR CHAMPS NON-MONTANTS ===
        regex_patterns = {
            'id_amazon': [
                r'Numéro de la commande[:\s]+(\d{3}-\d{7}-\d{7})',
                r'Order number[:\s]+(\d{3}-\d{7}-\d{7})',
                r'Numero dell\'ordine[:\s]+(\d{3}-\d{7}-\d{7})',
                r'(?:Commande|Order|Ordine)[:\s#]*(\d{3}-\d{7}-\d{7})',
                r'(?:Commande Amazon|Amazon Order)[:\s#]*(\d{3}-\d{7}-\d{7})',
                r'(\d{3}-\d{7}-\d{7})',  # Pattern général en dernier
                r'\b(\d{3}-\d{7}-\d{7})\b'
            ],
            'facture_amazon': [
                # PRIORITÉ 0: Numéros de notes de crédit / avoirs (pour remboursements)
                r'Numéro de l\'avoir[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Nummer creditnota[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Numero della nota di credito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Número de la nota de crédito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Credit note number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Gutschrift Nummer[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                
                # PRIORITÉ 1: Numéros de factures normales
                r'Numéro de la facture[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Invoice number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Numero della fattura[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'(?:Facture|Invoice|Fattura)[:\s#]*([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'\b(FR\d{3,8}[A-Z0-9]{2,8})\b',
                r'\b(IT\d{3,8}[A-Z0-9]{2,8})\b',
                r'\b(MT\d{3,8}[A-Z0-9]{2,8})\b',
                r'\b(DE\d{3,8}[A-Z0-9]{2,8})\b',
                r'\b(ES\d{3,8}[A-Z0-9]{2,8})\b'
            ],
            'date_facture': [
                # Dates avec mots-clés français
                r'Date de la facture[:\s]*(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'(?:Date|du)[:\s]*(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                # Dates avec mots-clés italiens
                r'Data della fattura[:\s]*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'(?:Data|del)[:\s]*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                # Dates avec mots-clés espagnols
                r'Fecha de la factura[:\s]*(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})',
                r'Fecha de la nota de crédito[:\s]*(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})',
                r'(?:Fecha|del)[:\s]*(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})',
                # Dates avec mots-clés néerlandais
                r'Factuurdatum[:\s]*(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})',
                r'(?:Datum|van)[:\s]*(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})',
                # Dates avec mois en anglais
                r'Invoice date[:\s]*(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                # Patterns plus flexibles avec mois texte (multilangue)
                r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})',
                r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})',
                r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                # Formats numériques avec contexte
                r'(?:Date|Data|Fecha|Factuurdatum|Invoice date)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
                # Format numérique sans contexte (en dernier)
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})'
            ],
            'pays': [
                # Patterns qui capturent le CODE PAYS (2 lettres), pas le code postal
                r'\d{4,5}[A-Z]{2}\s+(NL)\b',  # Code postal néerlandais suivi du code pays
                r'\d{5}\s+(FR|IT|MT|DE|ES)\b',  # Code postal suivi du code pays
                r'\b(FR|IT|MT|DE|ES|NL|BE)\s+\d{4,5}\b',  # Code pays suivi du code postal
                r'\b(FR|IT|MT|DE|ES|NL|BE)\b(?!\d)',  # Code pays seul (pas suivi de chiffres)
                # Patterns avec noms de pays complets
                r'\d{5}\s+(?:France|FRANCE)\s*.*?\b(FR)\b',
                r'\d{5}\s+(?:Italia|ITALIA|Italy)\s*.*?\b(IT)\b',
                r'\d{5}\s+(?:Malta|MALTA)\s*.*?\b(MT)\b',
                r'\d{5}\s+(?:Deutschland|DEUTSCHLAND|Germany)\s*.*?\b(DE)\b',
                r'\d{5}\s+(?:España|ESPAÑA|Spain)\s*.*?\b(ES)\b',
                r'\d{4}[A-Z]{2}\s+(?:Nederland|NEDERLAND|Netherlands)\s*.*?\b(NL)\b',
                r'\d{4}\s+(?:België|BELGIË|Belgium|Belgique)\s*.*?\b(BE)\b',
                # Fallback : recherche directe du code pays
                r'(?:France|FRANCE).*?(FR)',
                r'(?:Italia|ITALIA|Italy).*?(IT)',
                r'(?:Malta|MALTA).*?(MT)',
                r'(?:Deutschland|DEUTSCHLAND|Germany).*?(DE)',
                r'(?:España|ESPAÑA|Spain).*?(ES)',
                r'(?:Nederland|NEDERLAND|Netherlands).*?(NL)',
                r'(?:België|BELGIË|Belgium|Belgique).*?(BE)'
            ],
            'nom_contact': [
                # PRIORITÉ 0: Nouveaux patterns pour noms collés aux montants (PRIORITÉ ABSOLUE)
                r'Total\s+(?:pendiente|à payer|te betalen|da pagare)\s+[€-]?[\d,\.]+\s*€?\s*([A-Z][A-Za-z\s]+?)(?=\s*\n|\s*$)',
                r'Total\s+(?:pendiente|à payer|te betalen|da pagare)\s+[\d,\.]+\s*€([A-Z][A-Z\s]+?)(?=\s*\n|\s*$)',
                r'(?:Total|Totale)\s+(?:pendiente|à payer|te betalen|da pagare)\s+[\d,\.]+[\s\xa0]*€[\s\xa0]*([A-Z][A-Z\s]+?)(?=\s*\n|\s*$)',
                
                # PRIORITÉ 1: Noms directement après numéro de facture (patterns spécifiques par langue)
                r'Número de la factura [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)',  # Espagnol
                r'Factuurnummer [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)',  # Néerlandais
                r'Numero della fattura [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)',  # Italien
                r'Numéro de la facture [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)',  # Français
                r'Numéro de l\'avoir [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)',  # Français avoir
                
                # PRIORITÉ 2: Noms en majuscules dans le texte (comme "DAVE")
                r'Btw-nummer [A-Z0-9]+\s*\n\s*([A-Z][A-Z\s]*[A-Z])\s*\n\s*Factuurdatum',  # Néerlandais
                r'IVA [A-Z0-9]+\s*\n\s*([A-Z][A-Z\s]*[A-Z])\s*\n\s*Fecha',  # Espagnol
                r'([A-Z]{3,}(?:\s+[A-Z]{3,})*)\s*\n\s*Número de la nota de crédito',  # Espagnol note de crédit
                r'([A-Z]{3,}(?:\s+[A-Z]{3,})*)\s*\n\s*Numéro de l\'avoir',  # Français avoir
                
                # PRIORITÉ 3: Noms dans les sections d'adresse (après mots-clés, avant adresse)
                r'Adresse de facturation\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n\s*[0-9]',  # Français
                r'Dirección de facturación\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n\s*[A-Z]',  # Espagnol
                r'Factuuradres\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n\s*[A-Z]',  # Néerlandais
                r'Indirizzo di fatturazione\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n\s*[A-Z]',  # Italien
                
                # PRIORITÉ 4: Noms en majuscules avant l'adresse de facturation (format direct)
                r'([A-Z]+\s+[A-Z]+(?:\s+[A-Z]+)?)\s*\n\s*(?:VIA|RUE|STREET|STRADA|CALLE|PASEO)',
                
                # PRIORITÉ 6: Patterns classiques améliorés (éviter Amazon Locker)
                r'Commandé par[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Ordinato da[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Ordered by[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                
                # PRIORITÉ 7: Noms en minuscules spécifiques (cas particuliers comme "xiaolai jin")
                r'Dirección de envío\s*\n\s*([a-z][a-z\s]+)\s*\n',  # Espagnol
                r'Bezorgadres\s*\n\s*([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s*\n',  # Néerlandais
                r'Adresse de livraison\s*\n\s*([A-Z][a-z]+(?:\s+[a-z]+)*)\s*\n',  # Français
                
                # PRIORITÉ 8: Patterns de livraison (éviter Amazon Locker)
                r'Livré à[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-ZaZ\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Consegnato a[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-ZaZ\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Ship to[:\s]+(?!.*(?:Amazon|Locker))([A-Z][A-ZaZ\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})'
            ]
            # Note: 'total' pattern supprimé car géré par l'analyse spatiale
        }
        
        # === APPLICATION DES PATTERNS REGEX (CHAMPS NON-MONTANTS) ===
        for field, patterns in regex_patterns.items():
            current_value = invoice_data[field]
            if debug_mode:
                logger.info(f"   [REGEX] Traitement champ '{field}', valeur actuelle: '{current_value}'")
            
            # PRIORITÉ ABSOLUE DU NOM DE FICHIER pour pays, facture_amazon et date_facture
            if field in ['pays', 'facture_amazon', 'date_facture'] and filename_data.get(field):
                if debug_mode:
                    logger.info(f"   [REGEX] Champ '{field}' ignoré car extrait du nom de fichier avec priorité")
                continue
            
            if not current_value:  # Seulement si pas déjà rempli par l'analyse spatiale
                # LOGIQUE SPÉCIALE POUR facture_amazon EN CAS DE REMBOURSEMENT
                if field == 'facture_amazon' and invoice_data['total'] < 0:
                    # Pour les remboursements (montant négatif), chercher UNIQUEMENT les numéros d'avoir/notes de crédit
                    credit_note_patterns = [
                        r'Numéro de l\'avoir[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        r'Nummer creditnota[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        r'Numero della nota di credito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        r'Número de la nota de crédito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        r'Credit note number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        r'Gutschrift Nummer[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                        # Patterns génériques pour numéros d'avoir
                        r'(?:avoir|credit|credito)[:\s#]*([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                    ]
                    
                    if debug_mode:
                        logger.info(f"   [REMBOURSEMENT] Montant négatif détecté ({invoice_data['total']}), recherche de numéro d'avoir uniquement")
                    
                    for pattern in credit_note_patterns:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            value = match.group(1) if match.groups() else match.group(0)
                            invoice_data[field] = value
                            if debug_mode:
                                logger.info(f"   [REMBOURSEMENT] Numéro d'avoir trouvé: {value}")
                            break
                    
                    # Si aucun numéro d'avoir trouvé avec les patterns spécialisés, 
                    # continuer avec les patterns normaux mais privilégier les premiers
                    if not invoice_data[field]:
                        if debug_mode:
                            logger.info(f"   [REMBOURSEMENT] Aucun numéro d'avoir spécialisé trouvé, recherche avec patterns généraux")
                        for pattern in patterns:
                            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                            if match:
                                value = match.group(1) if match.groups() else match.group(0)
                                invoice_data[field] = value
                                if debug_mode:
                                    logger.info(f"   [REMBOURSEMENT] {field}: {value} (pattern général)")
                                break
                
                else:
                    # Logique normale pour les autres champs ou factures normales
                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            if debug_mode:
                                logger.info(f"   [REGEX] Match trouvé pour '{field}' avec pattern: {pattern}")
                            
                            if field == 'date_facture':
                                # Traitement UNIFORME de toutes les dates via parse_date_string
                                if len(match.groups()) >= 3:
                                    # Dates avec mois en texte (jour, mois, année)
                                    day = match.group(1)
                                    month_text = match.group(2)
                                    year = match.group(3)
                                    date_tuple = (day, month_text, year)
                                    parsed_date = parse_date_string(date_tuple)
                                else:
                                    # Dates numériques (DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY)
                                    date_string = match.group(1) if match.groups() else match.group(0)
                                    parsed_date = parse_date_string(date_string)
                                
                                if parsed_date:
                                    value = parsed_date
                                else:
                                    value = match.group(0)  # Fallback
                            else:
                                value = match.group(1) if match.groups() else match.group(0)
                            
                            # Mise à jour des données
                            invoice_data[field] = value
                            if debug_mode:
                                logger.info(f"   [REGEX] {field}: {value}")
                            break
        
        # Calcul automatique du taux de TVA si manquant
        if not invoice_data['taux_tva'] and invoice_data['ht'] > 0 and invoice_data['tva'] > 0:
            taux = (invoice_data['tva'] / invoice_data['ht']) * 100
            invoice_data['taux_tva'] = f"{taux:.0f}%"
            if debug_mode:
                logger.info(f"   [CALCUL] Taux TVA calculé: {invoice_data['taux_tva']}")
        
        # === CORRECTION POST-EXTRACTION POUR REMBOURSEMENTS ===
        # Si le montant est négatif, chercher obligatoirement un numéro d'avoir dans le PDF
        # même si un numéro de facture a été extrait du nom de fichier
        if invoice_data['total'] < 0:
            if debug_mode:
                logger.info(f"   [CORRECTION_REMBOURSEMENT] Montant négatif détecté ({invoice_data['total']}), recherche forcée de numéro d'avoir")
            
            # Patterns spécialisés pour numéros d'avoir/notes de crédit
            credit_note_patterns = [
                r'Numéro de l\'avoir[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Nummer creditnota[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',  
                r'Numero della nota di credito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Número de la nota de crédito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Credit note number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'Gutschrift Nummer[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                # Patterns génériques plus larges
                r'(?:avoir|credit|credito|nota)[:\s#]*([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
                r'\b([A-Z]{2}5000[A-Z0-9]{2,8})\b',  # Pattern FR5000... typique des avoirs Amazon
            ]
            
            credit_note_found = None
            for pattern in credit_note_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    credit_note_found = match.group(1) if match.groups() else match.group(0)
                    if debug_mode:
                        logger.info(f"   [CORRECTION_REMBOURSEMENT] Numéro d'avoir trouvé avec pattern '{pattern}': {credit_note_found}")
                    break
            
            # Si un numéro d'avoir a été trouvé, remplacer le numéro de facture
            if credit_note_found:
                old_facture = invoice_data['facture_amazon']
                invoice_data['facture_amazon'] = credit_note_found
                if debug_mode:
                    logger.info(f"   [CORRECTION_REMBOURSEMENT] Remplacement: '{old_facture}' → '{credit_note_found}'")
            elif debug_mode:
                logger.info(f"   [CORRECTION_REMBOURSEMENT] Aucun numéro d'avoir trouvé, conservation du numéro actuel: '{invoice_data['facture_amazon']}'")
        
        # Vérification des données minimales
        has_minimum_data = any([
            invoice_data['id_amazon'],
            invoice_data['facture_amazon'],
            invoice_data['total'] > 0
        ])
        
        if debug_mode:
            completeness = sum(1 for v in invoice_data.values() if v)
            logger.info(f"   [STATS] Complétude: {completeness}/8 champs remplis")
        
        # Nettoyage final : retirer les marqueurs SKIP pour les factures BE non-UOSS
        if invoice_data['facture_amazon'] == 'SKIP_BE_NON_UOSS':
            invoice_data['facture_amazon'] = ''
            if debug_mode:
                logger.info(f"   [CLEANUP] Marqueur SKIP supprimé pour facture BE non-UOSS")
        
        return invoice_data if has_minimum_data else None
        
    except Exception as e:
        logger.error(f"Erreur lors du parsing de {filename}: {str(e)}")
        return None


def _extract_with_spatial_analysis(pdf_path, debug_mode=False):
    """
    Extraction spatiale avancée avec pdfplumber - UNIQUEMENT POUR LES MONTANTS
    Se concentre exclusivement sur HT, TVA, TOTAL et taux de TVA
    """
    import pdfplumber
    result = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                if debug_mode:
                    logger.info(f"   [SPATIAL PAGE] {page_num + 1}")
                
                # === EXTRACTION DES TABLEAUX (MONTANTS UNIQUEMENT) ===
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables):
                        if not table:
                            continue
                        
                        # Analyse du tableau de TVA (formats variés)
                        for row in table:
                            if len(row) >= 3 and any('€' in str(cell) for cell in row):
                                # Recherche d'une ligne avec pourcentage et montants
                                percent_cell = None
                                ht_cell = None
                                tva_cell = None
                                
                                # Pattern spécial pour ['', '0%', '€ 93,52', '€ 0,00'] (TVA à 0%)
                                if len(row) == 4 and '%' in str(row[1]) and '€' in str(row[2]) and '€' in str(row[3]):
                                    try:
                                        percent_cell = float(str(row[1]).replace('%', '').replace(',', '.').strip())
                                        # Gestion des montants négatifs : -€, - €, € XXX-
                                        ht_str = str(row[2]).replace('€', '').replace(',', '.').replace('-€', '-').replace('- €', '-').replace('- ', '-').strip()
                                        tva_str = str(row[3]).replace('€', '').replace(',', '.').replace('-€', '-').replace('- €', '-').replace('- ', '-').strip()
                                        
                                        # Support du format € XXX,XX- (- à la fin)
                                        if ht_str.endswith('-'):
                                            ht_str = '-' + ht_str[:-1]
                                        if tva_str.endswith('-'):
                                            tva_str = '-' + tva_str[:-1]
                                            
                                        ht_cell = float(ht_str)
                                        tva_cell = float(tva_str)
                                    except:
                                        pass
                                
                                # Pattern classique pour ['', '20 %', '191,38 €', '38,28 €']
                                if percent_cell is None:
                                    for cell in row:
                                        cell_str = str(cell).strip()
                                        if '%' in cell_str:
                                            try:
                                                percent_cell = float(cell_str.replace('%', '').replace(',', '.').strip())
                                            except:
                                                pass
                                        elif '€' in cell_str:
                                            try:
                                                # Gestion des montants négatifs : -€, - €, € XXX-
                                                amount_str = cell_str.replace('€', '').replace(',', '.').replace('-€', '-').replace('- €', '-').replace('- ', '-').strip()
                                                
                                                # Support du format € XXX,XX- (- à la fin)
                                                if amount_str.endswith('-'):
                                                    amount_str = '-' + amount_str[:-1]
                                                
                                                amount = float(amount_str)
                                                if ht_cell is None:
                                                    ht_cell = amount
                                                elif tva_cell is None:
                                                    tva_cell = amount
                                            except:
                                                pass
                                
                                # Vérifier que les valeurs sont définies (accepter 0 pour TVA)
                                if percent_cell is not None and ht_cell is not None and tva_cell is not None:
                                    result['taux_tva'] = f"{percent_cell:.0f}%"
                                    result['ht'] = ht_cell
                                    result['tva'] = tva_cell
                                    if debug_mode:
                                        logger.info(f"      [SPATIAL-TABLE] TVA: {percent_cell}% | HT: {ht_cell}€ | TVA: {tva_cell}€")
                                    break
                
                # === EXTRACTION DU TOTAL (ANALYSE SPATIALE) ===
                if not result.get('total'):
                    text = page.extract_text() or ""
                    
                    # Recherche du total avec différents patterns (AVEC SUPPORT DES MONTANTS NÉGATIFS)
                    total_patterns = [
                        # Patterns italiens avec montants négatifs
                        r'Totale da pagare\s*-€\s*(\d+[,.]?\d{0,2})',  # -€ 115,25
                        r'Totale da pagare\s+(-\d+[,.]?\d{0,2})\s*€',  # -115,25 €
                        r'Totale nota di credito\s*-€\s*(\d+[,.]?\d{0,2})',  # Note de crédit
                        r'Totale da pagare\s*€\s*(-\d+[,.]?\d{0,2})',  # € -115,25
                        # Patterns italiens classiques
                        r'Totale da pagare\s*€\s*(\d+[,.]?\d{0,2})',
                        r'Totale da pagare\s+(\d+[,.]?\d{0,2})\s*€',
                        r'Totale fattura\s+(\d+[,.]?\d{0,2})\s*€',
                        # Patterns français avec montants négatifs
                        r'Total à payer\s*-€\s*(\d+[,.]?\d{0,2})',
                        r'Total à payer\s*€\s*(-\d+[,.]?\d{0,2})',
                        r'Avoir total\s+(-\d+[,.]?\d{0,2})\s*€',
                        # Patterns français classiques
                        r'Total à payer\s*€\s*(\d+[,.]?\d{0,2})',
                        r'Total à payer\s+(\d+[,.]?\d{0,2})\s*€',
                        r'Montant dû\s+(\d+[,.]?\d{0,2})\s*€',
                        # Patterns espagnols avec montants négatifs
                        r'Total pendiente\s*-€\s*(\d+[,.]?\d{0,2})',
                        r'Total pendiente\s*(-\d+[,.]?\d{0,2})\s*€',
                        r'Total pendiente\s*€\s*(-\d+[,.]?\d{0,2})',
                        # Patterns espagnols classiques
                        r'Total\s*(-?\d+[,.]?\d{0,2})\s*€',
                        # Patterns néerlandais avec montants négatifs (FORMAT € XXX,XX-)
                        r'Totaal te betalen\s*€\s*(\d+[,.]?\d{0,2})\s*-',  # € 115,78-
                        r'Totaal te betalen\s*-€\s*(\d+[,.]?\d{0,2})',  # -€ 115,78
                        r'Totaal te betalen\s*€\s*(-\d+[,.]?\d{0,2})',  # € -115,78
                        r'Totaal factuur\s*€\s*(\d+[,.]?\d{0,2})\s*-',  # € 115,78-
                        # Patterns néerlandais classiques
                        r'Totaal te betalen\s*€\s*(\d+[,.]?\d{0,2})',
                        r'Totaal te betalen\s+(\d+[,.]?\d{0,2})\s*€',
                        r'Totaal factuur\s*€\s*(\d+[,.]?\d{0,2})',
                        # Patterns génériques
                        r'Total[:\s]+(-?\d+[,.]?\d{0,2})\s*€'
                    ]
                    
                    for pattern in total_patterns:
                        total_match = re.search(pattern, text, re.IGNORECASE)
                        if total_match:
                            try:
                                amount_str = total_match.group(1).replace(',', '.')
                                
                                # Traitement spécial pour les patterns avec montants négatifs
                                if '-€' in pattern and not amount_str.startswith('-'):
                                    # Si le pattern contient -€ mais le montant capturé n'a pas de signe,
                                    # alors c'est un montant négatif
                                    result['total'] = -float(amount_str)
                                elif r'\s*-' in pattern and not amount_str.startswith('-'):
                                    # Si le pattern contient "€ XXX,XX-" (avec - à la fin)
                                    # alors c'est un montant négatif
                                    result['total'] = -float(amount_str)
                                else:
                                    # Montant normal (peut déjà être négatif avec le signe -)
                                    result['total'] = float(amount_str)
                                
                                if debug_mode:
                                    logger.info(f"      [SPATIAL-TOTAL] {result['total']}€")
                                break
                            except:
                                continue
                
                # Si on a trouvé des montants principaux, on peut arrêter
                if result.get('ht') is not None and result.get('tva') is not None and result.get('total') is not None:
                    break
    
    except Exception as e:
        if debug_mode:
            logger.warning(f"   Erreur analyse spatiale (montants): {e}")
    
    return result


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
                logger.error(f"Erreur lors du chargement du fichier existant: {str(e)}")          # Ajouter les nouvelles données de factures (sans numéro)
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
        
        # TRI PAR DATE CROISSANTE
        def parse_date_for_sorting(date_str):
            """Parse une date DD/MM/YYYY pour le tri"""
            if not date_str or date_str == '':
                return datetime.min  # Les dates vides en premier
            try:
                # Format attendu: DD/MM/YYYY
                return datetime.strptime(str(date_str), '%d/%m/%Y')
            except ValueError:
                try:
                    # Essayer d'autres formats au cas où
                    return datetime.strptime(str(date_str), '%Y-%m-%d')
                except ValueError:
                    return datetime.min  # Si parsing échoue, mettre en premier
        
        # Trier les données par date croissante
        rows_data.sort(key=lambda x: parse_date_for_sorting(x['date_facture']))
        logger.info(f"Données triées par date croissante: {len(rows_data)} factures")
        
        # Calculer les totaux
        total_ht = sum([row['ht'] for row in rows_data])
        total_tva = sum([row['tva'] for row in rows_data])
        total_ttc = sum([row['total'] for row in rows_data])
        
        logger.info(f"Totaux calculés - HT: {total_ht:.2f}, TVA: {total_tva:.2f}, TTC: {total_ttc:.2f}")        # Créer le DataFrame avec la structure attendue (sans colonne N°)
        df_data = []
        
        # Première ligne avec les totaux DYNAMIQUES (formules Excel)
        # Structure: 5 colonnes vides + HT + TVA + colonne vide + TOTAL = 9 colonnes
        # Les formules calculeront automatiquement la somme de toutes les lignes de données
        total_rows = len(rows_data) + 3  # +3 car ligne totaux (1) + ligne titres (2) + première ligne données (3)
        df_data.append(['', '', '', '', '', f"=SUM(F3:F{total_rows})", f"=SUM(G3:G{total_rows})", '', f"=SUM(I3:I{total_rows})"])
        
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
                float(row['ht']),  # Conserver comme nombre pour les formules Excel
                float(row['tva']),  # Conserver comme nombre pour les formules Excel
                row['taux_tva'],
                float(row['total'])  # Conserver comme nombre pour les formules Excel
            ])
        
        # Créer le DataFrame
        df = pd.DataFrame(df_data)
        
        # Sauvegarder en Excel avec formatage avancé
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, header=False, sheet_name='Factures Amazon')
            
            # Accéder à la feuille pour le formatage
            worksheet = writer.sheets['Factures Amazon']
            
            # Formatage de la ligne de titre (ligne 2, index 1)
            from openpyxl.styles import Font, PatternFill, Border, Side
            
            # Couleur verte #92d050 et gras pour les titres
            green_fill = PatternFill(start_color='92D050', end_color='92D050', fill_type='solid')
            bold_font = Font(bold=True)
            
            # Formatage spécial pour la ligne des totaux (ligne 1)
            # Couleur de fond légèrement différente et gras pour les totaux
            total_fill = PatternFill(start_color='E6F3FF', end_color='E6F3FF', fill_type='solid')  # Bleu clair
            total_font = Font(bold=True, color='000080')  # Bleu foncé et gras
            
            # Appliquer le formatage à la ligne des totaux (ligne 1)
            for col in [6, 7, 9]:  # Colonnes F(HT), G(TVA), I(TOTAL)
                cell = worksheet.cell(row=1, column=col)
                cell.fill = total_fill
                cell.font = total_font
            
            # Appliquer le formatage à la ligne de titre (ligne 2)
            for col in range(1, 10):  # Colonnes A à I (9 colonnes)
                cell = worksheet.cell(row=2, column=col)
                cell.fill = green_fill
                cell.font = bold_font
            
            # Figer la ligne de titre pour le scroll
            worksheet.freeze_panes = 'A3'  # Figer les 2 premières lignes (totaux + titres)
            
            # Formatage numérique pour les colonnes de montants (2 décimales)
            from openpyxl.styles import NamedStyle
            currency_style = NamedStyle(name="currency_style", number_format='0.00')
            
            # Appliquer le formatage numérique aux colonnes de montants (F, G, I)
            montant_columns = [6, 7, 9]  # F(HT), G(TVA), I(TOTAL)
            for row_idx in range(1, len(df_data) + 1):  # Toutes les lignes (totaux + données)
                for col_idx in montant_columns:
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    if cell.value is not None and not isinstance(cell.value, str):  # Ne pas formater les formules
                        cell.number_format = '0.00'
            
            # Formatage des montants négatifs en rouge
            red_font = Font(color='FF0000')  # Rouge #ff0000
            
            # Parcourir toutes les lignes de données (à partir de la ligne 3)
            for row_idx in range(3, len(df_data) + 1):
                # Colonnes des montants : F(HT), G(TVA), I(TOTAL) - colonnes 6, 7, 9
                montant_columns = [6, 7, 9]  # F, G, I
                has_negative = False
                
                # Vérifier s'il y a des montants négatifs dans cette ligne
                for col_idx in montant_columns:
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    try:
                        # Maintenant que les valeurs sont des nombres, c'est plus simple
                        if cell.value is not None and isinstance(cell.value, (int, float)) and cell.value < 0:
                            has_negative = True
                            break
                    except (ValueError, TypeError):
                        pass
                
                # Si on a trouvé un montant négatif, colorer tous les montants de cette ligne en rouge
                if has_negative:
                    for col_idx in montant_columns:
                        cell = worksheet.cell(row=row_idx, column=col_idx)
                        cell.font = red_font
            
            # Ajuster automatiquement la largeur des colonnes selon le contenu
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                # Ajuster la largeur avec une marge de sécurité
                adjusted_width = min(max_length + 2, 50)  # Maximum 50 caractères
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Fichier Excel créé avec succès: {output_path}")
        logger.info(f"Formatage appliqué: titres verts, gras, ligne fixe, colonnes auto-ajustées, montants négatifs en rouge")
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
                            invoice_data = parse_amazon_invoice_data(text_to_parse, debug_mode=True, filename=filename, pdf_path=pdf_path)
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
                    parsing_result = parse_amazon_invoice_data(text_to_parse, debug_mode=True, filename=filename, pdf_path=pdf_path)
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
