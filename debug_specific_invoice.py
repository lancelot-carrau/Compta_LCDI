#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PyPDF2
import re
import os
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un PDF"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Erreur lors de l'extraction du PDF {pdf_path}: {e}")
    return text

def analyze_specific_invoice(pdf_path):
    """Analyse spécifique d'une facture problématique"""
    print(f"\n=== ANALYSE DE {os.path.basename(pdf_path)} ===")
    
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print("❌ Aucun texte extrait du PDF")
        return
    
    print(f"✅ Texte extrait ({len(text)} caractères)")
    print("\n--- CONTENU BRUT (premiers 2000 caractères) ---")
    print(text[:2000])
    print("\n--- FIN DU CONTENU BRUT ---")
    
    # Patterns actuels de l'application
    date_patterns = [
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})',
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})',
        r'(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})',
        r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
        r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
    ]
    
    amount_patterns = [
        r'(?:EUR|€)\s*([0-9]{2,}[,.]?\d{0,2})',
        r'([0-9]{2,}[,.]?\d{0,2})\s*(?:EUR|€)',
        r'(?:Total|Totale|TOTAL|HT|TTC|TVA|IVA)[\s:]*([0-9]{2,}[,.]?\d{0,2})',
        r'([0-9]{2,}[,.]?\d{0,2})(?=\s*(?:EUR|€|\n|$))'
    ]
    
    amazon_id_patterns = [
        r'([0-9]{3}-[0-9]{7}-[0-9]{7})',
        r'ID.*?([0-9]{3}-[0-9]{7}-[0-9]{7})',
        r'Amazon.*?([0-9]{3}-[0-9]{7}-[0-9]{7})'
    ]
    
    invoice_patterns = [
        r'(FR[0-9]{4}[A-Z0-9]{6,})',
        r'Facture.*?(FR[0-9]{4}[A-Z0-9]{6,})',
        r'Invoice.*?(FR[0-9]{4}[A-Z0-9]{6,})',
        r'N°.*?(FR[0-9]{4}[A-Z0-9]{6,})'
    ]
    
    print("\n--- RECHERCHE DES DATES ---")
    for i, pattern in enumerate(date_patterns, 1):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"Pattern {i}: {match.group()} à position {match.start()}-{match.end()}")
    
    print("\n--- RECHERCHE DES MONTANTS ---")
    for i, pattern in enumerate(amount_patterns, 1):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"Pattern {i}: {match.group()} à position {match.start()}-{match.end()}")
            if match.groups():
                print(f"  Groupe capturé: {match.group(1)}")
    
    print("\n--- RECHERCHE ID AMAZON ---")
    for i, pattern in enumerate(amazon_id_patterns, 1):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"Pattern {i}: {match.group()} à position {match.start()}-{match.end()}")
    
    print("\n--- RECHERCHE FACTURE ---")
    for i, pattern in enumerate(invoice_patterns, 1):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"Pattern {i}: {match.group()} à position {match.start()}-{match.end()}")
    
    # Recherche spécifique de mots-clés
    print("\n--- MOTS-CLÉS SPÉCIFIQUES ---")
    keywords = ['Date', 'Invoice', 'Facture', 'Total', 'EUR', '€', 'TVA', 'IVA', 'HT', 'TTC', 'Amazon']
    for keyword in keywords:
        matches = list(re.finditer(re.escape(keyword), text, re.IGNORECASE))
        if matches:
            print(f"{keyword}: {len(matches)} occurrences")
            for match in matches[:3]:  # Limite à 3 pour éviter le spam
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].replace('\n', ' ')
                print(f"  ...{context}...")

if __name__ == "__main__":
    # Analyse de la facture problématique
    problem_invoice = "uploads/batch_7_1710_TVA_2200_IT_2025-05-04_FR5003PAHCVZJI_9352.pdf"
    
    if os.path.exists(problem_invoice):
        analyze_specific_invoice(problem_invoice)
    else:
        print(f"❌ Fichier non trouvé: {problem_invoice}")
        
    # Analyse d'une facture qui fonctionne pour comparaison
    print("\n" + "="*80)
    working_invoice = "uploads/batch_6_1709_TVA_2000_FR_2025-05-03_FR5003OZHCVZJI_23198.pdf"
    
    if os.path.exists(working_invoice):
        analyze_specific_invoice(working_invoice)
    else:
        print(f"❌ Fichier non trouvé: {working_invoice}")
