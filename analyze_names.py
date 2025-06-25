#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from app import parse_amazon_invoice_data

def analyze_missing_names():
    """Analyser pourquoi certains noms ne sont pas extraits"""
    
    # Factures avec des noms manquants selon le test précédent
    problematic_files = [
        'uploads/1766 TVA 22,00% IT 2025-05-07 FR500023HCVZJQ -115,25€.pdf',  # 4/9 champs
        'uploads/1770 TVA 21,00% NL 2025-05-06 FR500026HCVZJQ -115,78€.pdf',  # 5/9 champs
        'uploads/1760 TVA 20,00% FR 2025-05-04 FR5003PCHCVZJI 115,99€.pdf'    # 8/9 champs (nom manquant)
    ]
    
    for pdf_file in problematic_files:
        if not os.path.exists(pdf_file):
            continue
            
        print(f'\n{"="*60}')
        print(f'ANALYSE: {os.path.basename(pdf_file)}')
        print(f'{"="*60}')
        
        try:
            # Extraire le texte
            with pdfplumber.open(pdf_file) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() + '\n'
            
            # Tester l'extraction
            result = parse_amazon_invoice_data(text, debug_mode=False, filename=os.path.basename(pdf_file), pdf_path=pdf_file)
            
            print(f'🔍 RÉSULTAT ACTUEL:')
            for key, value in result.items():
                status = "✅" if value and str(value).strip() != "" and str(value) != "0.0" else "❌"
                print(f'  {status} {key}: "{value}"')
            
            # Analyser spécifiquement les noms potentiels
            print(f'\n🔎 RECHERCHE DE NOMS DANS LE TEXTE:')
            import re
            
            # Patterns pour trouver des noms potentiels
            name_patterns = [
                (r'Numero della fattura [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)', "Italien - après numéro facture"),
                (r'Factuurnummer [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)', "Néerlandais - après numéro facture"),
                (r'Numéro de la facture [A-Z0-9]+\s*\n\s*([A-Z][A-Za-z\s]+)(?=\s*\n|\s*$)', "Français - après numéro facture"),
                (r'([A-Z]+\s+[A-Z]+(?:\s+[A-Z]+)?)\s*\n\s*(?:VIA|RUE|STREET|STRADA)', "Avant adresse"),
                (r'Adresse de facturation\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n', "Adresse facturation FR"),
                (r'Factuuradres\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n', "Adresse facturation NL"),
                (r'Indirizzo di fatturazione\s*\n\s*([A-Z][A-Za-z\s]+)\s*\n', "Adresse facturation IT"),
                (r'([A-Z]{3,}(?:\s+[A-Z]{3,})*)\s*\n', "Noms en majuscules isolés")
            ]
            
            found_names = []
            for pattern, description in name_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    found_names.extend([(match, description) for match in matches])
                    print(f'  ✅ {description}: {matches}')
                    
            if not found_names:
                print(f'  ❌ Aucun nom trouvé avec les patterns')
                
            # Afficher les 1000 premiers caractères pour analyse manuelle
            print(f'\n📄 EXTRAIT DU TEXTE (1000 premiers caractères):')
            print('-' * 50)
            print(f'{text[:1000]}...')
                
        except Exception as e:
            print(f'❌ Erreur: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyze_missing_names()
