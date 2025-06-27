#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse du contenu PDF de la facture 1710
"""

import pdfplumber
import re

def analyze_1710():
    """Analyser le contenu de la facture 1710"""
    pdf_path = "uploads/1710 TVA 22,00% IT 2025-05-04 FR5003PAHCVZJI 93,52€.pdf"
    
    print("🔍 Analyse de la facture 1710...")
    print("-" * 60)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"\n📄 PAGE {page_num + 1}")
                print("-" * 30)
                
                # Extraire le texte brut
                text = page.extract_text() or ""
                print("📝 TEXTE BRUT:")
                print(text[:1000] + "..." if len(text) > 1000 else text)
                
                # Extraire les tableaux
                tables = page.extract_tables()
                if tables:
                    print(f"\n📊 TABLEAUX TROUVÉS: {len(tables)}")
                    for t_num, table in enumerate(tables):
                        print(f"\n🔢 Tableau {t_num + 1}:")
                        for row_num, row in enumerate(table):
                            if row_num < 10:  # Limiter l'affichage
                                print(f"   Ligne {row_num}: {row}")
                
                # Recherche de patterns spécifiques
                print(f"\n🔍 RECHERCHE DE PATTERNS:")
                
                # TVA et montants
                tva_patterns = [
                    r'(\d+[,.]?\d*)\s*%',
                    r'(\d+[,.]?\d*)\s*€',
                    r'Total.*?(\d+[,.]?\d*)\s*€',
                    r'Totale.*?(\d+[,.]?\d*)\s*€'
                ]
                
                for pattern in tva_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"   {pattern}: {matches}")
                        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    analyze_1710()
