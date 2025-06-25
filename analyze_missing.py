#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from app import parse_amazon_invoice_data

def analyze_missing_data():
    """Analyser les données manquantes dans l'extraction"""
    
    # Tester plusieurs factures avec des données manquantes
    test_files = [
        "uploads/1762 TVA 21,00% ES 2025-05-06 FR500025HCVZJQ -117,49€.pdf",  # Date manquante
        "uploads/1763 TVA 21,00% ES 2025-05-08 FR5000JGHCVZJU 117,49€.pdf",   # Date manquante  
        "uploads/1769 TVA 21,00% NL 2025-05-06 FR5000J5HCVZJU 115,78€.pdf",   # Date manquante
        "uploads/1756 TVA 20,00% FR 2025-05-05 FR5000FSHCVZJC -2,33€.pdf"     # Contact manquant
    ]
    
    for pdf_file in test_files:
        if not os.path.exists(pdf_file):
            print(f"❌ Fichier non trouvé: {pdf_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"ANALYSE: {os.path.basename(pdf_file)}")
        print(f"{'='*60}")
        
        try:
            # Extraire le texte
            with pdfplumber.open(pdf_file) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() + '\n'
            
            print(f"📄 TEXTE EXTRAIT (premiers 1500 chars):")
            print("-" * 50)
            print(text[:1500])
            print("..." if len(text) > 1500 else "")
            
            # Tester l'extraction
            print(f"\n🔍 RÉSULTAT D'EXTRACTION:")
            print("-" * 50)
            result = parse_amazon_invoice_data(text, debug_mode=False, filename=os.path.basename(pdf_file), pdf_path=pdf_file)
            
            if result:
                for key, value in result.items():
                    status = "✅" if value and str(value).strip() != "" and str(value) != "0.0" else "❌"
                    print(f"  {status} {key}: '{value}'")
            else:
                print("  ❌ Aucune donnée extraite")
            
            # Analyser spécifiquement les patterns de date
            print(f"\n📅 ANALYSE DES DATES:")
            print("-" * 50)
            import re
            
            # Patterns de date italiens
            italian_dates = re.findall(r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})', text, re.IGNORECASE)
            if italian_dates:
                print(f"  Dates italiennes trouvées: {italian_dates}")
            
            # Patterns de date espagnols
            spanish_dates = re.findall(r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{4})', text, re.IGNORECASE)
            if spanish_dates:
                print(f"  Dates espagnoles trouvées: {spanish_dates}")
            
            # Patterns génériques
            generic_dates = re.findall(r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text)
            if generic_dates:
                print(f"  Dates numériques trouvées: {generic_dates}")
            
            # Analyser les contacts
            print(f"\n👤 ANALYSE DES CONTACTS:")
            print("-" * 50)
            contact_patterns = [
                r'Ordinato da[:\s]+([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Commandé par[:\s]+([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'Ordered by[:\s]+([A-Z][A-Za-z\s\-\'\.]{2,60}?)(?=\s*\n|\s*$|\s{3,})',
                r'([A-Z]+\s+[A-Z]+(?:\s+[A-Z]+)?)\s*\n\s*(?:VIA|RUE|STREET|STRADA)'
            ]
            
            for pattern in contact_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    print(f"  Pattern '{pattern[:30]}...': {matches}")
                    
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyze_missing_data()
