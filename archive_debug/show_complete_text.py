#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.getcwd())

from app import extract_pdf_text

def show_complete_text():
    """Afficher le texte complet de la facture FR5000FSHCVZJC"""
    
    pdf_path = os.path.join(os.getcwd(), 'uploads', '1756 TVA 20,00% FR 2025-05-05 FR5000FSHCVZJC -2,33€.pdf')
    
    print(f"📂 Chemin: {pdf_path}")
    print(f"📂 Existe: {os.path.exists(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        return
    
    text = extract_pdf_text(pdf_path)
    
    print("=" * 80)
    print("TEXTE COMPLET DE LA FACTURE:")
    print("=" * 80)
    print(text)
    print("=" * 80)
    
    # Recherche spécifique des patterns d'émission
    print("\n🔍 RECHERCHE PATTERNS ÉMISSION:")
    print("-" * 50)
    
    # Pattern plus large pour émission
    emission_patterns = [
        r'émission.*?(\d{1,2})\s+(mai|avril|juin|juillet|août|septembre|octobre|novembre|décembre|janvier|février|mars)\s+(\d{4})',
        r'Date.*?émission.*?(\d{1,2})\s+(mai|avril|juin|juillet|août|septembre|octobre|novembre|décembre|janvier|février|mars)\s+(\d{4})',
        r'(\d{1,2})\s+(mai|avril|juin|juillet|août|septembre|octobre|novembre|décembre|janvier|février|mars)\s+(\d{4})'
    ]
    
    for i, pattern in enumerate(emission_patterns):
        print(f"\nPattern {i+1}: {pattern}")
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"   → Trouvé: {match}")
    
    # Recherche de tous les contextes contenant "émission"
    print("\n🔍 CONTEXTES CONTENANT 'ÉMISSION':")
    print("-" * 50)
    
    for match in re.finditer(r'émission', text, re.IGNORECASE):
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        context = text[start:end]
        print(f"Position {match.start()}: {repr(context)}")

if __name__ == "__main__":
    show_complete_text()
