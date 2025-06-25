#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyser quel pattern capture 115.99€ dans la facture Zacharie
"""

import sys
import os
import re

# Importer les fonctions de app.py
sys.path.append('.')
from app import extract_pdf_text, extract_pdf_tables_pdfplumber

def analyze_pattern_115_99():
    """Analyser pourquoi 115.99€ est capturé au lieu de 193.32€"""
    
    pdf_file = "1709 TVA 20,00% FR 2025-05-03 FR5003OZHCVZJI 231,98€.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Fichier PDF non trouvé: {pdf_file}")
        return
    
    print(f"🔍 ANALYSE DU PATTERN QUI CAPTURE 115.99€")
    print(f"📁 Fichier: {pdf_file}")
    print("=" * 70)
    
    # Extraire le contenu
    pdf_text = extract_pdf_text(pdf_file)
    pdf_tables = extract_pdf_tables_pdfplumber(pdf_file)
    
    # Fusionner le contenu
    pdf_content = pdf_text
    if pdf_tables:
        for table in pdf_tables:
            if table:
                pdf_content += "\n" + str(table)
    
    print(f"📝 CONTENU EXTRAIT ({len(pdf_content)} caractères):")
    print(pdf_content[:500] + "...")
    print()
    
    print(f"🔍 RECHERCHE DE 115.99 DANS LE TEXTE:")
    lines_with_115_99 = []
    for i, line in enumerate(pdf_content.split('\n')):
        if '115.99' in line or '115,99' in line:
            lines_with_115_99.append((i, line))
            print(f"   Ligne {i}: {line.strip()}")
    
    print()
    print(f"🔍 RECHERCHE DE 193.32 DANS LE TEXTE:")
    lines_with_193_32 = []
    for i, line in enumerate(pdf_content.split('\n')):
        if '193.32' in line or '193,32' in line:
            lines_with_193_32.append((i, line))
            print(f"   Ligne {i}: {line.strip()}")
    
    print()
    print(f"🔍 RECHERCHE DE 38.66 DANS LE TEXTE:")
    lines_with_38_66 = []
    for i, line in enumerate(pdf_content.split('\n')):
        if '38.66' in line or '38,66' in line:
            lines_with_38_66.append((i, line))
            print(f"   Ligne {i}: {line.strip()}")
    
    # Test des patterns HT existants dans app.py
    print()
    print(f"🧪 TEST DES PATTERNS HT:")
    
    # Pattern ultra-prioritaire pour format "Total 193,32 € 38,66 €"
    pattern1 = r'Total\s+([\d,]+,\d{2})\s*€\s+([\d,]+,\d{2})\s*€'
    matches1 = re.findall(pattern1, pdf_content, re.IGNORECASE)
    if matches1:
        print(f"   ✅ Pattern ultra-prioritaire 1: {matches1}")
        print(f"      HT: {matches1[0][0]}, TVA: {matches1[0][1]}")
    else:
        print(f"   ❌ Pattern ultra-prioritaire 1: Aucun match")
    
    # Pattern ultra-prioritaire pour format "20 % 193,32 € 38,66 €"
    pattern2 = r'20\s*%\s+([\d,]+,\d{2})\s*€\s+([\d,]+,\d{2})\s*€'
    matches2 = re.findall(pattern2, pdf_content, re.IGNORECASE)
    if matches2:
        print(f"   ✅ Pattern ultra-prioritaire 2: {matches2}")
        print(f"      HT: {matches2[0][0]}, TVA: {matches2[0][1]}")
    else:
        print(f"   ❌ Pattern ultra-prioritaire 2: Aucun match")
    
    # Pattern qui pourrait capturer 115.99
    pattern3 = r'(\d+,\d{2})\s*€'
    matches3 = re.findall(pattern3, pdf_content)
    print(f"   🔍 Tous les montants trouvés: {matches3}")
    
    # Chercher spécifiquement le contexte de 115.99
    print()
    print(f"🔍 CONTEXTE DE 115.99:")
    for i, line in enumerate(pdf_content.split('\n')):
        if '115.99' in line or '115,99' in line:
            print(f"   Ligne {i}: {line.strip()}")
            # Afficher aussi les lignes avant/après
            lines = pdf_content.split('\n')
            for j in range(max(0, i-2), min(len(lines), i+3)):
                if j != i:
                    print(f"   Ligne {j}: {lines[j].strip()}")
            break

if __name__ == "__main__":
    analyze_pattern_115_99()
