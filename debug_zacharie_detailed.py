#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version de debug de parse_amazon_invoice_data pour diagnostiquer le problème Zacharie
"""

import re
import os
from datetime import datetime

def parse_date_string_debug(date_str):
    """Version debug de parse_date_string"""
    if not date_str:
        return ''
    
    try:
        # Dictionnaire des mois français
        french_months = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        # Traitement des dates avec mois en texte (format "DD mois YYYY")
        text_date_pattern = r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
        
        date_input = str(date_str).strip()
        match = re.search(text_date_pattern, date_input, re.IGNORECASE)
        if match:
            day, month_text, year = match.groups()
            month_text = month_text.lower()
            month_num = french_months.get(month_text)
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
        
        return ''
        
    except Exception as e:
        print(f"Erreur parsing date '{date_str}': {e}")
        return ''

def debug_zacharie_parsing(text):
    """Version debug pour comprendre le problème de parsing de Zacharie"""
    
    print("=== DEBUG PARSING ZACHARIE ===")
    print(f"Longueur du texte: {len(text)}")
    print(f"Début du texte: {text[:200]}")
    
    # Patterns order_id
    order_patterns = [
        r'Contratto\s+(\d{3}-\d{7}-\d{7})',
        r'Order\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
        r'Commande\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
        r'Ordine\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
        r'Bestellung\s*[#:]?\s*(\d{3}-\d{7}-\d{7})',
        r'\b(\d{3}-\d{7}-\d{7})\b'
    ]
    
    print("\n1. Test des patterns ORDER_ID:")
    id_amazon = ''
    for i, pattern in enumerate(order_patterns):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            id_amazon = match.group(1)
            print(f"   ✅ Pattern {i}: '{pattern}' -> {id_amazon}")
            break
        else:
            print(f"   ❌ Pattern {i}: '{pattern}' -> pas de match")
    
    # Patterns invoice_number
    invoice_patterns = [
        r'Numero fattura\s+([A-Z]{2}\d{4,8}[A-Z]{2,8})',
        r'\b(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)\b',
        r'\b([A-Z]{2}\d{4,8}[A-Z]{2,8}[A-Z0-9]*)\b',
        r'Payé.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Paid.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Pagato.*?(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Numéro\s*de\s*la\s*facture[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Invoice\s*Number[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Numero\s*della\s*fattura[:\s]*(FR\d{4,8}[A-Z]{2,8}[A-Z0-9]*)',
        r'Invoice\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
        r'Facture\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
        r'Fattura\s*[#:]?\s*(INV-[A-Z]{2}-[A-Z0-9-]+)',
        r'\b(INV-[A-Z]{2}-[A-Z0-9-]+)\b'
    ]
    
    print("\n2. Test des patterns INVOICE_NUMBER:")
    facture_amazon = ''
    for i, pattern in enumerate(invoice_patterns):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            facture_amazon = match.group(1)
            print(f"   ✅ Pattern {i}: '{pattern}' -> {facture_amazon}")
            break
        else:
            print(f"   ❌ Pattern {i}: '{pattern}' -> pas de match")
    
    # Patterns date
    date_patterns = [
        r'Data\s*di\s*fatturazione[^0-9]*(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
        r'Date\s*de\s*facturation.*?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
        r'Date\s*de\s*commande.*?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
        r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
        r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
        r'Data\s*di\s*fatturazione[:\s/]*(\d{1,2}/\d{1,2}/\d{4})',
        r'Invoice\s*Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
        r'Date\s*de\s*facturation[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(\d{1,2}\.\d{1,2}\.\d{4})'
    ]
    
    print("\n3. Test des patterns DATE:")
    date_facture = ''
    for i, pattern in enumerate(date_patterns):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            if len(match.groups()) > 1:
                parsed_date = parse_date_string_debug(match.groups())
            else:
                parsed_date = parse_date_string_debug(match.group(1))
            if parsed_date:
                date_facture = parsed_date
                print(f"   ✅ Pattern {i}: '{pattern}' -> {match.groups()} -> {date_facture}")
                break
            else:
                print(f"   ⚠️ Pattern {i}: '{pattern}' -> {match.groups()} -> parsing échoué")
        else:
            print(f"   ❌ Pattern {i}: '{pattern}' -> pas de match")
    
    # Patterns subtotal (HT)
    subtotal_patterns = [
        r'Total\s+(\d+,\d{2})\s*€\s+(\d+,\d{2})\s*€',
        r'(\d+)\s*%\s+(\d+,\d{2})\s*€\s+(\d+,\d{2})\s*€',
        r'0%\s*€\s+(\d+,\d{2})\s*€\s+0,00',
        r'Subtotale[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'Subtotal[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'Sous-total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'Sub-total[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'Net\s*Amount[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'Montant\s*HT[:\s]+[€$]?(\d+[,.]?\d{0,2})',
        r'(\d+[,.]?\d{2})\s*[€]?\s*(?=.*?(?:TVA|VAT|IVA))'
    ]
    
    print("\n4. Test des patterns SUBTOTAL (HT):")
    ht = 0.0
    subtotal_matches = []
    for i, pattern in enumerate(subtotal_patterns):
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            subtotal_matches.append((i, pattern, match))
            print(f"   ✅ Pattern {i}: '{pattern}' -> {match.groups()}")
    
    if subtotal_matches:
        # Prendre le dernier match comme dans le code original
        last_match = subtotal_matches[-1][2]
        print(f"   → DERNIER match sélectionné: {last_match.groups()}")
        try:
            if len(last_match.groups()) == 3:
                if last_match.pattern.startswith(r'Total\s+'):
                    clean_value = last_match.groups()[0].replace(',', '.')
                else:
                    clean_value = last_match.groups()[1].replace(',', '.')
                ht = float(clean_value)
            elif len(last_match.groups()) == 2:
                clean_value = last_match.groups()[0].replace(',', '.')
                ht = float(clean_value)
            else:
                clean_value = last_match.group(1).replace(',', '.')
                ht = float(clean_value)
            print(f"   → HT extrait: {ht}")
        except Exception as e:
            print(f"   → Erreur extraction HT: {e}")
    
    # Test validation finale
    print("\n5. VALIDATION FINALE:")
    print(f"   ID Amazon: '{id_amazon}'")
    print(f"   Facture Amazon: '{facture_amazon}'")
    print(f"   Date facture: '{date_facture}'") 
    print(f"   HT: {ht}")
    
    has_minimum_data = (
        bool(id_amazon) or 
        bool(facture_amazon) or 
        ht > 0
    )
    
    print(f"   Données minimales présentes: {has_minimum_data}")
    print(f"   - ID Amazon présent: {bool(id_amazon)}")
    print(f"   - Facture Amazon présente: {bool(facture_amazon)}")
    print(f"   - HT > 0: {ht > 0}")
    
    return has_minimum_data

if __name__ == "__main__":
    # Test avec le fichier Zacharie
    import sys
    sys.path.append('.')
    from app import extract_pdf_text
    
    pdf_path = "1709 TVA 20,00% FR 2025-05-03 FR5003OZHCVZJI 231,98€.pdf"
    
    if os.path.exists(pdf_path):
        text = extract_pdf_text(pdf_path)
        debug_zacharie_parsing(text)
    else:
        print(f"Fichier non trouvé: {pdf_path}")
