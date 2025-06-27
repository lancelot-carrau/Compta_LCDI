#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from datetime import datetime

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.getcwd())

from app import extract_pdf_text, extract_date_from_paid_box, parse_date_string

def debug_fr50007_date_extraction():
    """Debug spécifique pour FR50007IHCVZJU - analyser la priorité des dates"""
    
    pdf_path = os.path.join(os.getcwd(), 'uploads', '1782 TVA 21,00% BE 2025-02-17 FR50007IHCVZJU 902,94€.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    print(f"🔍 ANALYSE DÉTAILLÉE DE FR50007IHCVZJU")
    print(f"📂 Chemin: {pdf_path}")
    print("=" * 80)
    
    # Extraire le texte complet
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("❌ Impossible d'extraire le texte du PDF")
        return
    
    print(f"📄 Texte extrait: {len(text)} caractères")
    print("\n" + "=" * 80)
    
    # Rechercher TOUS les patterns de date dans le texte
    print("🔍 RECHERCHE DE TOUTES LES DATES DANS LE TEXTE:")
    print("-" * 50)
    
    # Pattern pour dates italiennes
    italian_date_pattern = r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})'
    italian_matches = re.findall(italian_date_pattern, text, re.IGNORECASE)
    
    print(f"Dates italiennes trouvées: {len(italian_matches)}")
    for i, (day, month, year) in enumerate(italian_matches):
        print(f"  {i+1}. {day} {month} {year}")
        formatted = parse_date_string((day, month, year))
        print(f"     → Formaté: {formatted}")
    
    # Pattern pour dates numériques
    numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
    numeric_matches = re.findall(numeric_date_pattern, text)
    
    print(f"\nDates numériques trouvées: {len(numeric_matches)}")
    for i, (d1, d2, year) in enumerate(numeric_matches):
        print(f"  {i+1}. {d1}-{d2}-{year}")
        formatted = parse_date_string(f"{d1}-{d2}-{year}")
        print(f"     → Formaté: {formatted}")
    
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
            
            # Recherche du pattern DD Month YYYY dans ce contexte
            date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
            date_matches = re.findall(date_pattern, context, re.IGNORECASE)
            
            for day, month_name, year in date_matches:
                found_invoice_dates.append((keyword, day, month_name, year, keyword_match.start()))
                print(f"   ✅ Date trouvée: {day} {month_name} {year}")
                formatted = parse_date_string((day, month_name, year))
                print(f"      → Formaté: {formatted}")
            
            # Recherche de dates numériques DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
            numeric_date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})'
            numeric_matches = re.findall(numeric_date_pattern, context)
            
            for day, month, year in numeric_matches:
                found_invoice_dates.append((keyword, day, month, year, keyword_match.start()))
                print(f"   ✅ Date numérique trouvée: {day}-{month}-{year}")
                formatted = parse_date_string(f"{day}-{month}-{year}")
                print(f"      → Formaté: {formatted}")
    
    print("\n" + "=" * 80)
    
    # Analyser les contextes de "Payé" / "Remboursé"
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
        
        # Recherche du pattern DD Month YYYY dans ce contexte
        date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
        date_matches = re.findall(date_pattern, context, re.IGNORECASE)
        
        for day, month_name, year in date_matches:
            found_paid_dates.append((keyword_match.group(), day, month_name, year, keyword_match.start()))
            print(f"   ✅ Date trouvée: {day} {month_name} {year}")
            formatted = parse_date_string((day, month_name, year))
            print(f"      → Formaté: {formatted}")
    
    print("\n" + "=" * 80)
    
    # Test de la fonction extract_date_from_paid_box
    print("🧪 TEST DE LA FONCTION extract_date_from_paid_box:")
    print("-" * 50)
    
    extracted_date = extract_date_from_paid_box(text)
    print(f"Date extraite par la fonction: {extracted_date}")
    
    print("\n" + "=" * 80)
    
    # Analyse de la priorité
    print("📊 ANALYSE DE PRIORITÉ:")
    print("-" * 50)
    
    print("1. Dates trouvées dans les contextes de 'Date de facturation':")
    if found_invoice_dates:
        # Trier par position dans le texte (plus haut = priorité plus haute)
        found_invoice_dates.sort(key=lambda x: x[4])  # Trier par position
        for keyword, day, month, year, pos in found_invoice_dates:
            print(f"   Position {pos}: {day} {month} {year} (contexte: {keyword})")
        print(f"   → PRIORITÉ ABSOLUE: {found_invoice_dates[0][1]} {found_invoice_dates[0][2]} {found_invoice_dates[0][3]}")
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
    
    print("\n🎯 RÉSULTAT FINAL:")
    final_date = extracted_date
    print(f"Date extraite: {final_date}")
    
    if final_date:
        print("✅ Date extraite avec succès")
    else:
        print("❌ Échec de l'extraction de date")

if __name__ == "__main__":
    debug_fr50007_date_extraction()
