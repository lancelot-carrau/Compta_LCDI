#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdfplumber
import os

def analyze_apostrophes():
    """Analyser les caractères d'apostrophe dans le PDF"""
    
    # Chercher le fichier
    uploads_dir = "uploads"
    pdf_file = None
    
    for filename in os.listdir(uploads_dir):
        if "FR5000FSHCVZJC" in filename.upper():
            pdf_file = os.path.join(uploads_dir, filename)
            break
    
    if not pdf_file:
        print("Fichier FR5000FSHCVZJC non trouvé dans uploads/")
        return
    
    print(f"Analyse des apostrophes dans: {pdf_file}")
    print("=" * 50)
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    
    # Chercher la section spécifique
    target = "Date d"
    idx = full_text.find(target)
    if idx >= 0:
        # Extraire 50 caractères autour
        start = max(0, idx - 10)
        end = min(len(full_text), idx + 50)
        context = full_text[start:end]
        print(f"Contexte trouvé: '{context}'")
        
        # Analyser chaque caractère
        for i, char in enumerate(context):
            print(f"Position {i}: '{char}' (ord: {ord(char)})")
    else:
        print("'Date d' non trouvé dans le texte")
    
    # Chercher tous les caractères apostrophe-like
    apostrophe_chars = []
    for i, char in enumerate(full_text):
        if char in ["'", "'", "'", "`", "´"]:
            apostrophe_chars.append((i, char, ord(char)))
    
    print(f"\nTous les caractères apostrophe trouvés ({len(apostrophe_chars)}):")
    for pos, char, code in apostrophe_chars[:10]:  # Premiers 10
        context_start = max(0, pos - 15)
        context_end = min(len(full_text), pos + 15)
        context = full_text[context_start:context_end]
        print(f"Position {pos}: '{char}' (ord: {code}) dans: '{context}'")

if __name__ == "__main__":
    analyze_apostrophes()
