#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de la facture FR50006WHCVZJU pour comprendre d'où vient la date incorrecte
"""

import sys
import os
sys.path.append('.')

from app import process_pdf_extraction, parse_amazon_invoice_data, extract_date_from_paid_box
import re

def debug_facture_fr50006():
    """Débugger la facture FR50006WHCVZJU qui a une date incorrecte"""
    
    print("=== DEBUG FACTURE FR50006WHCVZJU ===\n")
    
    # Chercher le fichier PDF
    pdf_files = []
    for file in os.listdir("uploads"):
        if "FR50006WHCVZJU" in file and file.endswith('.pdf'):
            pdf_files.append(file)
    
    if not pdf_files:
        print("❌ Fichier FR50006WHCVZJU non trouvé dans uploads/")
        return
    
    filename = pdf_files[0]
    pdf_path = f"uploads/{filename}"
    
    print(f"📁 Analyse de: {filename}")
    
    # Extraction du PDF
    pdf_results = process_pdf_extraction(pdf_path, 'auto')
    if not pdf_results['success']:
        print(f"❌ Échec extraction PDF: {pdf_results['errors']}")
        return
    
    text = pdf_results['text']
    print(f"✅ Texte extrait: {len(text)} caractères")
    
    # Affichage du texte complet pour comprendre
    print(f"\n📄 TEXTE COMPLET DE LA FACTURE:")
    print("=" * 80)
    print(text)
    print("=" * 80)
    
    # Recherche spécifique de toutes les dates dans le texte
    print(f"\n📅 RECHERCHE DE TOUTES LES DATES:")
    
    # Pattern pour dates avec mois italien
    italian_dates = re.findall(r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})', text, re.IGNORECASE)
    print(f"📅 Dates italiennes trouvées:")
    for i, (day, month, year) in enumerate(italian_dates, 1):
        print(f"  {i}: {day} {month} {year}")
    
    # Pattern pour dates françaises
    french_dates = re.findall(r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})', text, re.IGNORECASE)
    print(f"\n📅 Dates françaises trouvées:")
    for i, (day, month, year) in enumerate(french_dates, 1):
        print(f"  {i}: {day} {month} {year}")
    
    # Pattern pour dates numériques
    numeric_dates = re.findall(r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})', text)
    print(f"\n📅 Dates numériques trouvées:")
    for i, date in enumerate(numeric_dates, 1):
        print(f"  {i}: {date}")
    
    # Test de l'extraction depuis l'encadré "Payé"/"Remboursé"
    print(f"\n🔍 TEST EXTRACTION DEPUIS ENCADRÉ PAYÉ/REMBOURSÉ:")
    paid_date = extract_date_from_paid_box(text)
    if paid_date:
        print(f"✅ Date depuis encadré: {paid_date}")
    else:
        print(f"❌ Aucune date trouvée dans encadré Payé/Remboursé")
    
    # Recherche de contextes autour des mots-clés de date
    print(f"\n🎯 CONTEXTES AUTOUR DES MOTS-CLÉS DE DATE:")
    
    date_keywords = [
        'Data della fattura', 'Invoice date', 'Date de la facture', 'Fecha de la factura',
        'Factuurdatum', 'Data', 'Date', 'Fecha', 'Datum'
    ]
    
    for keyword in date_keywords:
        matches = list(re.finditer(keyword, text, re.IGNORECASE))
        for match in matches:
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace('\n', ' ')
            print(f"  🔍 '{keyword}': ...{context}...")
    
    # Test avec l'extraction complète
    print(f"\n🧪 TEST EXTRACTION COMPLÈTE:")
    invoice_data = parse_amazon_invoice_data(
        text, 
        debug_mode=True, 
        filename=filename, 
        pdf_path=pdf_path
    )
    
    if invoice_data:
        print(f"✅ Données extraites:")
        for key, value in invoice_data.items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ Échec de l'extraction")

if __name__ == "__main__":
    debug_facture_fr50006()
