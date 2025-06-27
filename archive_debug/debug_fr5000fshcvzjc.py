#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from datetime import datetime

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.getcwd())

from app import extract_pdf_text, extract_date_from_paid_box, parse_amazon_invoice_data, parse_date_string

def debug_fr5000fshcvzjc_date():
    """Debug spécifique pour FR5000FSHCVZJC - analyser la priorité des dates"""
    
    # Trouver le fichier FR5000FSHCVZJC
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    target_file = None
    
    for filename in os.listdir(uploads_dir):
        if 'FR5000FSHCVZJC' in filename and filename.endswith('.pdf'):
            target_file = filename
            break
    
    if not target_file:
        print("❌ Fichier FR5000FSHCVZJC non trouvé")
        print("📂 Fichiers disponibles:")
        for f in os.listdir(uploads_dir):
            if f.endswith('.pdf'):
                print(f"   - {f}")
        return
    
    pdf_path = os.path.join(uploads_dir, target_file)
    
    print(f"🔍 ANALYSE DÉTAILLÉE DE {target_file}")
    print(f"📂 Chemin: {pdf_path}")
    print("=" * 80)
    
    # Extraire le texte complet
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("❌ Impossible d'extraire le texte du PDF")
        return
    
    print(f"📄 Texte extrait: {len(text)} caractères")
    print(f"📄 Extrait du texte (premiers 300 chars):")
    print(text[:300])
    print("\n" + "=" * 80)
    
    # Rechercher TOUTES les dates dans le texte
    print("🔍 RECHERCHE DE TOUTES LES DATES DANS LE TEXTE:")
    print("-" * 50)
    
    # Pattern pour dates numériques
    numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
    numeric_matches = re.findall(numeric_date_pattern, text)
    
    print(f"Dates numériques trouvées: {len(numeric_matches)}")
    for i, (d1, d2, year) in enumerate(numeric_matches):
        print(f"  {i+1}. {d1}-{d2}-{year}")
        formatted = parse_date_string(f"{d1}-{d2}-{year}")
        print(f"     → Formaté: {formatted}")
    
    # Pattern pour dates avec mois en texte français
    french_date_pattern = r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
    french_matches = re.findall(french_date_pattern, text, re.IGNORECASE)
    
    print(f"\nDates françaises trouvées: {len(french_matches)}")
    for i, (day, month, year) in enumerate(french_matches):
        print(f"  {i+1}. {day} {month} {year}")
        formatted = parse_date_string((day, month, year))
        print(f"     → Formaté: {formatted}")
    
    print("\n" + "=" * 80)
    
    # Analyser les contextes de date de note de crédit
    print("🔍 ANALYSE DES CONTEXTES DE DATE DE NOTE DE CRÉDIT:")
    print("-" * 50)
    
    credit_note_date_keywords = [
        'Date d\'émission de l\'avoir', 'Creditnotadatum', 'Data emissione nota di credito',
        'Fecha de emisión de la nota de crédito', 'Credit note date', 'Gutschrift Datum',
        'Datum van de creditnota', 'Date de la note de crédit', 'Data nota di credito'
    ]
    
    found_credit_dates = []
    
    for keyword in credit_note_date_keywords:
        keyword_pattern = re.escape(keyword)
        for keyword_match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            # Récupérer 200 caractères après le mot-clé
            start = keyword_match.end()
            end = min(len(text), start + 200)
            context = text[start:end]
            
            print(f"\n📍 Contexte trouvé pour '{keyword}':")
            print(f"   Position: {keyword_match.start()}-{keyword_match.end()}")
            print(f"   Contexte (200 chars): {repr(context[:100])}...")
            
            # Recherche de dates dans ce contexte
            date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            date_matches = re.findall(date_pattern, context, re.IGNORECASE)
            
            for day, month_name, year in date_matches:
                found_credit_dates.append((keyword, day, month_name, year, keyword_match.start()))
                print(f"   ✅ Date trouvée: {day} {month_name} {year}")
                formatted = parse_date_string((day, month_name, year))
                print(f"      → Formaté: {formatted}")
            
            # Recherche de dates numériques
            numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
            numeric_matches = re.findall(numeric_date_pattern, context)
            
            for day, month, year in numeric_matches:
                found_credit_dates.append((keyword, day, month, year, keyword_match.start()))
                print(f"   ✅ Date numérique trouvée: {day}-{month}-{year}")
                formatted = parse_date_string(f"{day}-{month}-{year}")
                print(f"      → Formaté: {formatted}")
    
    if not found_credit_dates:
        print("   ❌ Aucune date de note de crédit trouvée")
    
    print("\n" + "=" * 80)
    
    # Analyser les contextes de date de facturation
    print("🔍 ANALYSE DES CONTEXTES DE DATE DE FACTURATION:")
    print("-" * 50)
    
    invoice_date_keywords = [
        'Data di fatturazione', 'Date de la facture', 'Invoice date', 'Fecha de la factura',
        'Factuurdatum', 'Rechnungsdatum', 'Data fattura', 'Date facture'
    ]
    
    found_invoice_dates = []
    
    for keyword in invoice_date_keywords:
        keyword_pattern = re.escape(keyword)
        for keyword_match in re.finditer(keyword_pattern, text, re.IGNORECASE):
            # Récupérer 200 caractères après le mot-clé
            start = keyword_match.end()
            end = min(len(text), start + 200)
            context = text[start:end]
            
            print(f"\n📍 Contexte trouvé pour '{keyword}':")
            print(f"   Position: {keyword_match.start()}-{keyword_match.end()}")
            print(f"   Contexte (200 chars): {repr(context[:100])}...")
            
            # Recherche de dates dans ce contexte
            date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            date_matches = re.findall(date_pattern, context, re.IGNORECASE)
            
            for day, month_name, year in date_matches:
                found_invoice_dates.append((keyword, day, month_name, year, keyword_match.start()))
                print(f"   ✅ Date trouvée: {day} {month_name} {year}")
                formatted = parse_date_string((day, month_name, year))
                print(f"      → Formaté: {formatted}")
            
            # Recherche de dates numériques
            numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
            numeric_matches = re.findall(numeric_date_pattern, context)
            
            for day, month, year in numeric_matches:
                found_invoice_dates.append((keyword, day, month, year, keyword_match.start()))
                print(f"   ✅ Date numérique trouvée: {day}-{month}-{year}")
                formatted = parse_date_string(f"{day}-{month}-{year}")
                print(f"      → Formaté: {formatted}")
    
    if not found_invoice_dates:
        print("   ❌ Aucune date de facturation trouvée")
    
    print("\n" + "=" * 80)
    
    # Analyser les contextes "Payé"/"Remboursé"
    print("🔍 ANALYSE DES CONTEXTES 'PAYÉ'/'REMBOURSÉ':")
    print("-" * 50)
    
    paid_keywords = [
        'payé', 'paid', 'betaald', 'pagato', 'pagado', 'bezahlt',
        'remboursé', 'refunded', 'terugbetaald', 'rimborsato', 'reembolsado', 'erstattet'
    ]
    
    found_paid_dates = []
    keywords_pattern = '|'.join(paid_keywords)
    
    for keyword_match in re.finditer(f'({keywords_pattern})', text, re.IGNORECASE):
        # Récupérer 200 caractères autour du mot-clé
        start = max(0, keyword_match.start() - 100)
        end = min(len(text), keyword_match.end() + 100)
        context = text[start:end]
        
        print(f"\n📍 Contexte trouvé pour '{keyword_match.group()}':")
        print(f"   Position: {keyword_match.start()}-{keyword_match.end()}")
        print(f"   Contexte (200 chars): {repr(context[:100])}...")
        
        # Recherche de dates dans ce contexte
        date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
        date_matches = re.findall(date_pattern, context, re.IGNORECASE)
        
        for day, month_name, year in date_matches:
            found_paid_dates.append((keyword_match.group(), day, month_name, year, keyword_match.start()))
            print(f"   ✅ Date trouvée: {day} {month_name} {year}")
            formatted = parse_date_string((day, month_name, year))
            print(f"      → Formaté: {formatted}")
        
        # Recherche de dates numériques
        numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
        numeric_matches = re.findall(numeric_date_pattern, context)
        
        for day, month, year in numeric_matches:
            found_paid_dates.append((keyword_match.group(), day, month, year, keyword_match.start()))
            print(f"   ✅ Date numérique trouvée: {day}-{month}-{year}")
            formatted = parse_date_string(f"{day}-{month}-{year}")
            print(f"      → Formaté: {formatted}")
    
    if not found_paid_dates:
        print("   ❌ Aucune date 'Payé' trouvée")
    
    print("\n" + "=" * 80)
    
    # Test de la fonction extract_date_from_paid_box
    print("🧪 TEST DE LA FONCTION extract_date_from_paid_box:")
    print("-" * 50)
    
    extracted_date = extract_date_from_paid_box(text)
    print(f"Date extraite par la fonction: {extracted_date}")
    
    print("\n" + "=" * 80)
    
    # Test de l'extraction complète
    print("🧪 TEST DE L'EXTRACTION COMPLÈTE:")
    print("-" * 50)
    
    result = parse_amazon_invoice_data(
        text=text, 
        debug_mode=True, 
        filename=target_file, 
        pdf_path=pdf_path
    )
    
    if result:
        print("✅ Extraction réussie:")
        for key, value in result.items():
            print(f"   {key}: {value}")
        
        print(f"\n📅 DATE EXTRAITE: {result.get('date_facture', 'AUCUNE')}")
        
        # Extraire la date du nom de fichier pour comparaison
        filename_date = target_file.split(' ')[4]  # Format: YYYY-MM-DD
        filename_date_formatted = filename_date.replace('-', '/')  # Format: YYYY/MM/DD
        # Inverser pour avoir DD/MM/YYYY
        date_parts = filename_date.split('-')
        if len(date_parts) == 3:
            filename_date_dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
        else:
            filename_date_dd_mm_yyyy = filename_date_formatted
        
        print(f"📅 DATE DU NOM DE FICHIER: {filename_date_dd_mm_yyyy}")
        
        if result.get('date_facture') == filename_date_dd_mm_yyyy:
            print("✅ SUCCÈS: Les dates correspondent")
        else:
            print("❌ DIVERGENCE: Les dates ne correspondent pas")
            print(f"   → PDF: {result.get('date_facture')}")
            print(f"   → Fichier: {filename_date_dd_mm_yyyy}")
    else:
        print("❌ Échec de l'extraction")
    
    print("\n" + "=" * 80)
    
    # Analyse de la priorité
    print("📊 ANALYSE DE PRIORITÉ:")
    print("-" * 50)
    
    print("0. Dates trouvées dans les contextes de 'Date d'émission de note de crédit':")
    if found_credit_dates:
        found_credit_dates.sort(key=lambda x: x[4])  # Trier par position
        for keyword, day, month, year, pos in found_credit_dates:
            print(f"   Position {pos}: {day} {month} {year} (contexte: {keyword})")
        print(f"   → PRIORITÉ ABSOLUE: {found_credit_dates[0][1]} {found_credit_dates[0][2]} {found_credit_dates[0][3]}")
    else:
        print("   ❌ Aucune date de note de crédit trouvée")
    
    print("\n1. Dates trouvées dans les contextes de 'Date de facturation':")
    if found_invoice_dates:
        found_invoice_dates.sort(key=lambda x: x[4])  # Trier par position
        for keyword, day, month, year, pos in found_invoice_dates:
            print(f"   Position {pos}: {day} {month} {year} (contexte: {keyword})")
        print(f"   → PRIORITÉ 1: {found_invoice_dates[0][1]} {found_invoice_dates[0][2]} {found_invoice_dates[0][3]}")
    else:
        print("   ❌ Aucune date de facturation trouvée")
    
    print("\n2. Dates trouvées dans les contextes 'Payé':")
    if found_paid_dates:
        found_paid_dates.sort(key=lambda x: x[4])  # Trier par position
        for keyword, day, month, year, pos in found_paid_dates:
            print(f"   Position {pos}: {day} {month} {year} (contexte: {keyword})")
        print(f"   → Fallback: {found_paid_dates[0][1]} {found_paid_dates[0][2]} {found_paid_dates[0][3]}")
    else:
        print("   ❌ Aucune date 'Payé' trouvée")

if __name__ == "__main__":
    debug_fr5000fshcvzjc_date()
