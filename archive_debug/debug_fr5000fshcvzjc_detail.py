#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdfplumber
import re
from datetime import datetime

def parse_date_string(date_str):
    """Parse a date string and return DD/MM/YYYY format"""
    if not date_str:
        return None
    
    # Clean the string
    date_str = date_str.strip()
    
    # Month names in different languages
    month_names = {
        # French
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06',
        'juillet': '07', 'août': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12',
        # English  
        'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06',
        'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12',
        # Italian
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04', 'maggio': '05', 'giugno': '06',
        'luglio': '07', 'agosto': '08', 'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
        # Dutch
        'januari': '01', 'februari': '02', 'maart': '03', 'april': '04', 'mei': '05', 'juni': '06',
        'juli': '07', 'augustus': '08', 'september': '09', 'oktober': '10', 'november': '11', 'december': '12',
        # Spanish
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
        'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    
    # Try DD month YYYY format first (e.g., "5 mai 2025")
    for month_name, month_num in month_names.items():
        pattern = rf'(\d{{1,2}})\s+{re.escape(month_name)}\s+(\d{{4}})'
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            year = match.group(2)
            return f"{day}/{month_num}/{year}"
    
    # Try various numeric formats
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',      # DD.MM.YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            if len(match.group(1)) == 4:  # YYYY format first
                year, month, day = match.groups()
            else:  # DD format first
                day, month, year = match.groups()
            
            day = day.zfill(2)
            month = month.zfill(2)
            return f"{day}/{month}/{year}"
    
    return None

def extract_date_from_paid_box(text):
    """Extract date from paid/refund box and invoice date sections"""
    if not text:
        return None
    
    print("=== ANALYSE EXTRACTION DATE ===")
    
    # Patterns for invoice date sections (PRIORITY)
    invoice_date_patterns = [
        # Credit note patterns (HIGHEST PRIORITY)
        r"Date d'émission de l'avoir\s*:?\s*([^\n\r]+)",
        r"Creditnotadatum\s*:?\s*([^\n\r]+)",
        r"Credit note date\s*:?\s*([^\n\r]+)", 
        r"Data della nota di credito\s*:?\s*([^\n\r]+)",
        
        # Regular invoice date patterns
        r"Data di fatturazione\s*:?\s*([^\n\r]+)",
        r"Date de (?:la )?facture\s*:?\s*([^\n\r]+)",
        r"Invoice date\s*:?\s*([^\n\r]+)",
        r"Factuurdatum\s*:?\s*([^\n\r]+)",
        r"Fecha de factura\s*:?\s*([^\n\r]+)",
        r"Rechnungsdatum\s*:?\s*([^\n\r]+)",
    ]
    
    # First try to find invoice date
    for pattern in invoice_date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            date_text = match.group(1).strip()
            print(f"Found invoice date pattern '{pattern}': '{date_text}'")
            
            parsed_date = parse_date_string(date_text)
            if parsed_date:
                print(f"Successfully parsed invoice date: {parsed_date}")
                return parsed_date
            else:
                print(f"Failed to parse date: '{date_text}'")
    
    # Fallback: paid/refund box patterns
    paid_patterns = [
        r"Payé le\s*:?\s*([^\n\r]+)",
        r"Paid on\s*:?\s*([^\n\r]+)",
        r"Pagato il\s*:?\s*([^\n\r]+)",
        r"Betaald op\s*:?\s*([^\n\r]+)",
        r"Remboursé le\s*:?\s*([^\n\r]+)",
        r"Refunded on\s*:?\s*([^\n\r]+)",
        r"Rimborsato il\s*:?\s*([^\n\r]+)",
        r"Terugbetaald op\s*:?\s*([^\n\r]+)",
    ]
    
    for pattern in paid_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            date_text = match.group(1).strip()
            print(f"Found paid/refund pattern '{pattern}': '{date_text}'")
            
            parsed_date = parse_date_string(date_text)
            if parsed_date:
                print(f"Successfully parsed paid/refund date: {parsed_date}")
                return parsed_date
            else:
                print(f"Failed to parse date: '{date_text}'")
    
    print("No date found in paid box or invoice date sections")
    return None

def debug_invoice_fr5000fshcvzjc():
    """Debug l'extraction de date pour la facture FR5000FSHCVZJC"""
    
    # Chercher le fichier
    import os
    uploads_dir = "uploads"
    pdf_file = None
    
    for filename in os.listdir(uploads_dir):
        if "FR5000FSHCVZJC" in filename.upper():
            pdf_file = os.path.join(uploads_dir, filename)
            break
    
    if not pdf_file:
        print("Fichier FR5000FSHCVZJC non trouvé dans uploads/")
        return
    
    print(f"Analyse du fichier: {pdf_file}")
    print("=" * 50)
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    print("TEXTE COMPLET DU PDF:")
    print("=" * 30)
    print(full_text)
    print("=" * 30)
    
    # Test de l'extraction de date
    extracted_date = extract_date_from_paid_box(full_text)
    print(f"\nDATE EXTRAITE: {extracted_date}")
    
    # Chercher manuellement toutes les dates dans le texte
    print("\n=== RECHERCHE MANUELLE DE TOUTES LES DATES ===")
    
    # Patterns de dates numériques
    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
        r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',
    ]
    
    # Patterns de dates textuelles
    month_names = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                   'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
                   'january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    
    for month in month_names:
        pattern = rf'\b(\d{{1,2}})\s+{re.escape(month)}\s+(\d{{4}})\b'
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            print(f"Date textuelle trouvée: {match.group(0)} à position {match.start()}-{match.end()}")
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, full_text)
        for match in matches:
            print(f"Date numérique trouvée: {match.group(0)} à position {match.start()}-{match.end()}")
    
    # Chercher spécifiquement les sections importantes
    print("\n=== RECHERCHE DANS SECTIONS SPÉCIFIQUES ===")
    
    sections_to_check = [
        "Date d'émission de l'avoir",
        "Creditnotadatum", 
        "Data della nota di credito",
        "Credit note date",
        "Date de facture",
        "Invoice date",
        "Data di fatturazione",
        "Factuurdatum"
    ]
    
    for section in sections_to_check:
        if section.lower() in full_text.lower():
            print(f"Section '{section}' trouvée dans le texte")
            # Extraire le contexte autour
            idx = full_text.lower().find(section.lower())
            context_start = max(0, idx - 50)
            context_end = min(len(full_text), idx + len(section) + 100)
            context = full_text[context_start:context_end]
            print(f"Contexte: ...{context}...")
        else:
            print(f"Section '{section}' NON trouvée")

if __name__ == "__main__":
    debug_invoice_fr5000fshcvzjc()
