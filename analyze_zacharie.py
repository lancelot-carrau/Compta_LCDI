#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse du PDF de Zacharie Carpentier pour diagnostiquer le problème d'extraction
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_text, extract_pdf_tables_pdfplumber

def analyze_zacharie_pdf():
    """Analyser le PDF de Zacharie Carpentier"""
    pdf_file = "uploads/batch_7_1716_TVA_2000_FR_2025-04-28_FR5003KOHCVZJI_22966.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Fichier PDF non trouvé: {pdf_file}")
        return
    
    print(f"📄 Analyse du PDF: {os.path.basename(pdf_file)}")
    print("=" * 80)
    
    try:
        # Extraire le texte et les tableaux
        text = extract_pdf_text(pdf_file)
        tables = extract_pdf_tables_pdfplumber(pdf_file)
        
        print("📝 TEXTE EXTRAIT:")
        print("-" * 50)
        print(text)
        print()
        
        print("📊 TABLEAUX EXTRAITS:")
        print("-" * 50)
        for i, table in enumerate(tables):
            print(f"Tableau {i+1}:")
            for j, row in enumerate(table):
                print(f"  Ligne {j+1}: {row}")
            print()
        
        # Chercher les montants dans le texte
        print("🔍 RECHERCHE DES MONTANTS:")
        print("-" * 50)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if any(keyword in line_clean.lower() for keyword in ['total', 'ht', 'tva', '€', 'eur']):
                if any(char.isdigit() for char in line_clean):
                    print(f"Ligne {i+1}: {line_clean}")
        
        # Chercher spécifiquement les montants finaux
        print("\n💰 RECHERCHE DES TOTAUX FINAUX:")
        print("-" * 50)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if ('193' in line_clean and '32' in line_clean) or \
               ('38' in line_clean and '66' in line_clean) or \
               ('231' in line_clean and '98' in line_clean):
                print(f"Ligne {i+1}: {line_clean}")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_zacharie_pdf()
