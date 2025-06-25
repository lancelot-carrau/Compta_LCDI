#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse approfondie du PDF pour comprendre la structure des noms
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_text
import re

def analyze_pdf_structure():
    """Analyse la structure du PDF problématique"""
    
    pdf_path = 'uploads/batch_5_1714_TVA_2200_IT_2025-02-04_FR50006WHCVZJU_11525.pdf'
    if not os.path.exists(pdf_path):
        print("PDF non trouvé")
        return
    
    text = extract_pdf_text(pdf_path)
    
    print("=== ANALYSE STRUCTURE PDF ===")
    print(f"Fichier: {pdf_path}")
    print(f"Longueur texte: {len(text)} caractères")
    print()
    
    # Afficher le texte par sections
    lines = text.split('\n')
    print("=== LIGNES DU PDF ===")
    for i, line in enumerate(lines[:50]):  # 50 premières lignes
        if line.strip():
            print(f"{i+1:2}: {repr(line.strip())}")
    
    print()
    print("=== RECHERCHE DE NOMS POTENTIELS ===")
    
    # Patterns pour chercher différents types d'infos
    search_patterns = {
        'Commandé par': r'(?:Commandé par|Ordinato da|Ordered by)[:\s]*([^\n]+)',
        'Livré à': r'(?:Livré à|Consegnato a|Ship to)[:\s]*([^\n]+)',
        'Adresse': r'(?:Adresse|Indirizzo|Address)[:\s]*([^\n]+)',
        'Noms en majuscules': r'\b([A-Z]{2,}\s+[A-Z]{2,}(?:\s+[A-Z]{2,})?)\b',
        'Amazon Locker': r'(Amazon Locker[^\n]*)',
        'Lignes avec noms': r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$'
    }
    
    for pattern_name, pattern in search_patterns.items():
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            print(f"\n{pattern_name}:")
            for match in matches[:5]:  # Limiter à 5 résultats
                print(f"  -> {repr(match)}")

if __name__ == "__main__":
    analyze_pdf_structure()
