#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from app import parse_amazon_invoice_data

def debug_invoice_deep():
    """Déboguer l'extraction en profondeur"""
    
    pdf_file = "uploads/1710 TVA 22,00% IT 2025-05-04 FR5003PAHCVZJI 93,52€.pdf"
    
    print(f"=== DÉBOGAGE PROFOND ===")
    print(f"Fichier: {pdf_file}")
    
    # D'abord extraire le texte brut avec pdfplumber
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() + '\n'
        
        print(f"\n=== TEXTE BRUT EXTRAIT ===")
        print(text[:2000])  # Premiers 2000 caractères
        print("..." if len(text) > 2000 else "")
        
        # Maintenant tester l'extraction avec le texte ET le chemin du PDF
        print(f"\n=== TEST D'EXTRACTION ===")
        result = parse_amazon_invoice_data(text, debug_mode=True, filename=os.path.basename(pdf_file), pdf_path=pdf_file)
        print(f"Résultat:")
        if result:
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("  Aucune donnée extraite")
            
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_invoice_deep()
