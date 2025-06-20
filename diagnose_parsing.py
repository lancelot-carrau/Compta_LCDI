#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic du parsing pour identifier pourquoi parse_amazon_invoice_data retourne None
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import process_pdf_extraction, parse_amazon_invoice_data
import re

def diagnose_parsing():
    """Diagnostic complet du parsing"""
    
    test_files = [
        'uploads/batch_2_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf',
        'uploads/batch_3_1712_TVA_1800_MT_2025-01-29_FR500063HCVZJU_12672.pdf'
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ Fichier manquant: {file_path}")
            continue
            
        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC: {os.path.basename(file_path)}")
        print('='*80)
        
        # Extraction PDF
        pdf_results = process_pdf_extraction(file_path, extraction_method='auto')
        
        if not pdf_results['success']:
            print("❌ Échec extraction PDF")
            continue
            
        text = pdf_results['text']
        print(f"📄 Texte extrait ({len(text)} caractères):")
        print("-" * 50)
        print(text)
        print("-" * 50)
        
        # Tests de patterns individuels
        print(f"\n🔍 TESTS DE PATTERNS:")
        
        # 1. Pattern ID Amazon
        id_patterns = [
            r'(\d{3}-\d{7}-\d{7})',
            r'Order ID[:\s]*(\d{3}-\d{7}-\d{7})',
            r'Commande[:\s]*(\d{3}-\d{7}-\d{7})',
            r'Ordine[:\s]*(\d{3}-\d{7}-\d{7})',
            r'Bestellung[:\s]*(\d{3}-\d{7}-\d{7})'
        ]
        
        print("ID Amazon:")
        id_found = False
        for pattern in id_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern '{pattern}' -> {matches}")
                id_found = True
            else:
                print(f"  ❌ Pattern '{pattern}' -> Aucun match")
        
        if not id_found:
            print("  ⚠️  Recherche manuelle d'IDs dans le texte:")
            # Recherche plus générale
            general_id = re.findall(r'\d{3}-\d{7}-\d{7}', text)
            if general_id:
                print(f"     ID trouvés: {general_id}")
        
        # 2. Pattern Facture Amazon  
        print("\nFacture Amazon:")
        facture_patterns = [
            r'FR\d{11}[A-Z]{2,10}',
            r'IT\d{11}[A-Z]{2,10}',
            r'DE\d{11}[A-Z]{2,10}',
            r'MT\d{11}[A-Z]{2,10}',
            r'[A-Z]{2}\d{11}[A-Z]{2,10}'
        ]
        
        facture_found = False
        for pattern in facture_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"  ✅ Pattern '{pattern}' -> {matches}")
                facture_found = True
            else:
                print(f"  ❌ Pattern '{pattern}' -> Aucun match")
        
        # 3. Pattern Date
        print("\nDates:")
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        date_found = False
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"  ✅ Pattern '{pattern}' -> {matches}")
                date_found = True
            else:
                print(f"  ❌ Pattern '{pattern}' -> Aucun match")
        
        # 4. Pattern Pays
        print("\nPays:")
        country_patterns = [
            r'Via\s+[^,]+,\s*(\d{5})\s*([A-Z]{2})\b',
            r'Address[^,]+,\s*(\d{5})\s*([A-Z]{2})\b',
            r'Indirizzo[^,]+,\s*(\d{5})\s*([A-Z]{2})\b'
        ]
        
        country_found = False
        for pattern in country_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern '{pattern}' -> {matches}")
                country_found = True
            else:
                print(f"  ❌ Pattern '{pattern}' -> Aucun match")
        
        # 5. Pattern Montants
        print("\nMontants:")
        amount_patterns = [
            r'Total[:\s]*€\s*(\d+[.,]\d{2})',
            r'Totale[:\s]*€\s*(\d+[.,]\d{2})',
            r'Gesamt[:\s]*€\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*€'
        ]
        
        amount_found = False
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern '{pattern}' -> {matches}")
                amount_found = True
            else:
                print(f"  ❌ Pattern '{pattern}' -> Aucun match")
        
        # Test de la fonction parse_amazon_invoice_data
        print(f"\n🧪 TEST DE LA FONCTION parse_amazon_invoice_data:")
        result = parse_amazon_invoice_data(text, debug_mode=True)
        if result:
            print(f"✅ Résultat: {result}")
        else:
            print("❌ Résultat: None")
        
        print(f"\n" + "="*80)

if __name__ == "__main__":
    diagnose_parsing()
