#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour analyser le contenu exact du PDF
"""

import pdfplumber
import os

def analyze_pdf_structure(pdf_path):
    """Analyse la structure détaillée du PDF"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    print(f"🔍 ANALYSE DÉTAILLÉE DU PDF: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📖 Nombre de pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n📄 PAGE {page_num + 1}")
                print("-" * 50)
                
                # Texte brut
                text = page.extract_text()
                if text:
                    print(f"✅ Texte extrait: {len(text)} caractères")
                    print("📝 CONTENU (premiers 1000 caractères):")
                    print("-" * 30)
                    print(text[:1000])
                    print("-" * 30)
                    
                    # Recherche de patterns critiques
                    print("\n🔍 PATTERNS TROUVÉS:")
                    
                    import re
                    
                    # ID Amazon
                    id_matches = re.findall(r'\d{3}-\d{7}-\d{7}', text)
                    if id_matches:
                        print(f"   📋 ID Amazon: {id_matches}")
                    
                    # Numéro de facture
                    facture_matches = re.findall(r'[A-Z]{2}\d{4,}[A-Z0-9]+', text)
                    if facture_matches:
                        print(f"   📄 Factures: {facture_matches}")
                    
                    # Montants en euros
                    montant_matches = re.findall(r'\d+[,.]?\d{0,2}\s*€', text)
                    if montant_matches:
                        print(f"   💰 Montants: {montant_matches[:10]}...")  # Premiers 10
                    
                    # Pourcentages
                    percent_matches = re.findall(r'\d+[,.]?\d*\s*%', text)
                    if percent_matches:
                        print(f"   📊 Pourcentages: {percent_matches}")
                    
                    # Dates
                    date_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text)
                    if date_matches:
                        print(f"   📅 Dates: {date_matches}")
                    
                    # Mots-clés Amazon
                    amazon_keywords = ['amazon', 'Amazon', 'AMAZON', 'fattura', 'invoice', 'facture', 'Totale', 'IVA', 'TVA']
                    found_keywords = [kw for kw in amazon_keywords if kw in text]
                    if found_keywords:
                        print(f"   🏷️  Mots-clés Amazon: {found_keywords}")
                    
                else:
                    print("❌ Aucun texte extrait")
                    
                # Analyse des objets de la page
                chars = page.chars
                words = page.extract_words()
                
                print(f"\n📊 ÉLÉMENTS DE LA PAGE:")
                print(f"   Caractères: {len(chars) if chars else 0}")
                print(f"   Mots:       {len(words) if words else 0}")
                
                if words:
                    print(f"   📍 Position des premiers mots:")
                    for i, word in enumerate(words[:10]):
                        print(f"      {i+1:2d}. '{word['text'][:20]}' @ ({word['x0']:.1f}, {word['top']:.1f})")
                
                # Recherche de tableaux
                tables = page.extract_tables()
                if tables:
                    print(f"\n📋 TABLEAUX DÉTECTÉS: {len(tables)}")
                    for i, table in enumerate(tables):
                        print(f"   Tableau {i+1}: {len(table)} lignes × {len(table[0]) if table else 0} colonnes")
                        if table:
                            print(f"      Première ligne: {table[0]}")
                            if len(table) > 1:
                                print(f"      Deuxième ligne: {table[1]}")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = 'uploads/batch_7_1716_TVA_2000_FR_2025-04-28_FR5003KOHCVZJI_22966.pdf'
    analyze_pdf_structure(pdf_path)
