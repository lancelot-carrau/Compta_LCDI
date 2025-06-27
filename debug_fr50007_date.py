#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour analyser l'extraction de date de la facture FR50007IHCVZJU
Vérifier si la date de facturation est correctement extraite vs la date de commande
"""

import os
import sys
import pdfplumber
import PyPDF2
import re
from datetime import datetime

# Importer la fonction depuis app.py
sys.path.append('.')
from app import extract_date_from_paid_box, parse_date_string

def extract_pdf_text(pdf_path):
    """Extrait le texte d'un fichier PDF"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Erreur lors de l'extraction de texte: {e}")
    return text.strip()

def parse_date_string(date_str):
    """Convertir différents formats de date vers DD/MM/YYYY"""
    
    if not date_str:
        return None
    
    print(f"   [DATE_PARSE] Format reçu: {date_str}")
    
    # Dictionnaire des mois français
    french_months = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
    }
    
    # Vérifier si c'est un tuple (jour, mois_texte, année) depuis les patterns regex
    if isinstance(date_str, tuple) and len(date_str) == 3:
        day, month_text, year = date_str
        month_text = month_text.lower()
        
        # Chercher le mois dans le dictionnaire français
        month_num = french_months.get(month_text)
        if month_num:
            return f"{day.zfill(2)}/{month_num}/{year}"
    
    date_input = str(date_str).strip()
    
    # Traitement des dates avec mois en texte français
    text_date_pattern = r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
    
    match = re.search(text_date_pattern, date_input, re.IGNORECASE)
    if match:
        day, month_text, year = match.groups()
        month_text = month_text.lower()
        
        month_num = french_months.get(month_text)
        if month_num:
            return f"{day.zfill(2)}/{month_num}/{year}"
    
    # Essayer les formats numériques classiques
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_input, fmt)
            return parsed_date.strftime('%d/%m/%Y')
        except ValueError:
            continue
    
    print(f"   [DATE_PARSE] Échec parsing: {date_str}")
    return None

def analyze_all_dates_in_text(text):
    """Analyser toutes les dates trouvées dans le texte pour diagnostic"""
    print("\n=== ANALYSE DE TOUTES LES DATES DANS LE TEXTE ===")
    
    # Pattern pour capturer toutes les dates avec mois en français
    all_dates_pattern = r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
    
    all_matches = list(re.finditer(all_dates_pattern, text, re.IGNORECASE))
    
    print(f"Total de dates trouvées: {len(all_matches)}")
    
    for i, match in enumerate(all_matches):
        day, month, year = match.groups()
        
        # Obtenir le contexte autour de la date (100 caractères avant et après)
        start_ctx = max(0, match.start() - 100)
        end_ctx = min(len(text), match.end() + 100)
        context = text[start_ctx:end_ctx]
        
        # Formater la date
        formatted = parse_date_string((day, month, year))
        
        print(f"\nDate #{i+1}: {day} {month} {year} -> {formatted}")
        print(f"Position: {match.start()}-{match.end()}")
        print(f"Contexte: '...{context.replace(chr(10), ' ').replace(chr(13), ' ')}...'")
        
        # Vérifier si c'est dans un contexte de facturation
        context_lower = context.lower()
        
        is_invoice_context = any(keyword in context_lower for keyword in [
            'date de la facture', 'date facture', 'data di fatturazione', 
            'invoice date', 'fecha de la factura', 'factuurdatum'
        ])
        
        is_order_context = any(keyword in context_lower for keyword in [
            'date de la commande', 'date commande', 'order date', 
            'commandé le', 'ordered on', 'data dell\'ordine'
        ])
        
        is_payment_context = any(keyword in context_lower for keyword in [
            'payé', 'paid', 'remboursé', 'refunded'
        ])
        
        print(f"Contexte FACTURATION: {is_invoice_context}")
        print(f"Contexte COMMANDE: {is_order_context}")
        print(f"Contexte PAIEMENT: {is_payment_context}")

def main():
    # Chemin vers la facture FR50007IHCVZJU
    pdf_files = []
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            if "FR50007IHCVZJU" in filename and filename.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(uploads_dir, filename))
    
    if not pdf_files:
        print("❌ Facture FR50007IHCVZJU non trouvée dans le dossier uploads/")
        return
    
    pdf_path = pdf_files[0]
    print(f"📄 Analyse de la facture: {pdf_path}")
    
    # Extraire le texte
    text = extract_pdf_text(pdf_path)
    if not text:
        print("❌ Impossible d'extraire le texte du PDF")
        return
    
    print(f"✅ Texte extrait: {len(text)} caractères")
    
    # Analyser toutes les dates présentes
    analyze_all_dates_in_text(text)
    
    # Tester la fonction d'extraction de date
    print("\n" + "="*70)
    print("TEST DE LA FONCTION extract_date_from_paid_box()")
    print("="*70)
    
    extracted_date = extract_date_from_paid_box(text)
    
    print(f"\n🎯 RÉSULTAT FINAL:")
    print(f"Date extraite: {extracted_date}")
    
    if extracted_date:
        print(f"✅ Date extraite avec succès: {extracted_date}")
    else:
        print("❌ Aucune date extraite")

if __name__ == "__main__":
    main()
