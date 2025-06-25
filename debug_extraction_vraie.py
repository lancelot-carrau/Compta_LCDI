#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de l'extraction réelle en utilisant les fonctions de app.py
"""

import os
import sys

# Ajouter le répertoire courant au path pour importer app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import process_pdf_extraction, parse_amazon_invoice_data, extract_pdf_text

def debug_extraction_complete(pdf_path):
    """Debug complet de l'extraction d'un PDF"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG EXTRACTION COMPLÈTE: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # 1. Extraction du texte brut
        print(f"📄 1. EXTRACTION DU TEXTE BRUT")
        text = extract_pdf_text(pdf_path)
        print(f"   Texte extrait: {len(text)} caractères")
        print(f"   Aperçu: {text[:300]}...")
        
        # 2. Utiliser process_pdf_extraction
        print(f"\n📊 2. EXTRACTION COMPLÈTE (process_pdf_extraction)")
        result = process_pdf_extraction(pdf_path, extraction_method='auto')
        print(f"   Type de résultat: {type(result)}")
        print(f"   Résultat: {result}")
        
        # 3. Utiliser parse_amazon_invoice_data directement
        print(f"\n💰 3. ANALYSE AMAZON (parse_amazon_invoice_data)")
        invoice_data = parse_amazon_invoice_data(text, debug_mode=True, filename=os.path.basename(pdf_path))
        
        print(f"   Type de données: {type(invoice_data)}")
        if isinstance(invoice_data, dict):
            print(f"   📋 DONNÉES FACTURE:")
            for key, value in invoice_data.items():
                print(f"     {key}: {value}")
        elif isinstance(invoice_data, list):
            print(f"   📋 LISTE DE FACTURES ({len(invoice_data)} éléments):")
            for i, item in enumerate(invoice_data):
                print(f"     Facture {i+1}: {item}")
        else:
            print(f"   Données: {invoice_data}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ Erreur lors du debug: {e}")
        import traceback
        traceback.print_exc()

def debug_patterns_extraction(pdf_path):
    """Debug spécifique des patterns d'extraction des montants"""
    print(f"\n{'='*80}")
    print(f"🎯 DEBUG PATTERNS MONTANTS: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Extraire le texte
        text = extract_pdf_text(pdf_path)
        
        # Nettoyer le texte
        import re
        text_clean = re.sub(r'\s+', ' ', text.strip())
        
        print(f"📄 Texte nettoyé ({len(text_clean)} caractères)")
        
        # Simuler l'extraction des montants avec les patterns de app.py
        print(f"\n💰 SIMULATION EXTRACTION MONTANTS:")
        
        # Patterns HT (copiés de app.py)
        ht_patterns = [
            r'Subtotal\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Sous-total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Total\s*HT\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Prezzo\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Netto\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'([0-9,]+\.?[0-9]*)\s*€\s*([0-9,]+\.?[0-9]*)\s*€\s*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        ht_value = None
        print(f"🔍 Recherche HT:")
        for i, pattern in enumerate(ht_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern {i+1} match: {pattern}")
                print(f"     Résultats: {matches}")
                if not ht_value:
                    if isinstance(matches[0], tuple):
                        ht_value = matches[0][0] if matches[0][0] else matches[0][-1]
                    else:
                        ht_value = matches[0]
                    print(f"     🎯 HT retenu: {ht_value}")
                    break
        
        # Patterns TVA
        tva_patterns = [
            r'TVA\s*\(([0-9,]+\.?[0-9]*)\s*%\)\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'IVA\s*\(([0-9,]+\.?[0-9]*)\s*%\)\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'VAT\s*\(([0-9,]+\.?[0-9]*)\s*%\)\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'TVA\s*([0-9,]+\.?[0-9]*)\s*%\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Imposta\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Tax\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        tva_value = None
        tva_rate = None
        print(f"\n🔍 Recherche TVA:")
        for i, pattern in enumerate(tva_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern {i+1} match: {pattern}")
                print(f"     Résultats: {matches}")
                if not tva_value:
                    match = matches[0]
                    if isinstance(match, tuple) and len(match) >= 2:
                        tva_rate = match[0]
                        tva_value = match[1]
                    else:
                        tva_value = match if not isinstance(match, tuple) else match[0]
                    print(f"     🎯 TVA retenu: {tva_value}, Taux: {tva_rate}")
                    break
        
        # Patterns TOTAL
        total_patterns = [
            r'Total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Totale\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Gesamtbetrag\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Grand\s*Total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        total_value = None
        print(f"\n🔍 Recherche TOTAL:")
        for i, pattern in enumerate(total_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern {i+1} match: {pattern}")
                print(f"     Résultats: {matches}")
                if not total_value:
                    total_value = matches[0] if not isinstance(matches[0], tuple) else matches[0][0]
                    print(f"     🎯 TOTAL retenu: {total_value}")
                    break
        
        # Résumé
        print(f"\n📊 RÉSUMÉ EXTRACTION:")
        print(f"  HT: {ht_value}")
        print(f"  TVA: {tva_value} (Taux: {tva_rate})")
        print(f"  TOTAL: {total_value}")
        
        # Vérification cohérence
        if ht_value and tva_value and total_value:
            try:
                ht_num = float(ht_value.replace(',', '.'))
                tva_num = float(tva_value.replace(',', '.'))
                total_num = float(total_value.replace(',', '.'))
                
                calculated_total = ht_num + tva_num
                print(f"\n🧮 VÉRIFICATION:")
                print(f"  HT + TVA = {ht_num} + {tva_num} = {calculated_total}")
                print(f"  TOTAL extrait = {total_num}")
                print(f"  Cohérent: {'✅' if abs(calculated_total - total_num) < 0.01 else '❌'}")
                
                if tva_rate:
                    expected_tva = ht_num * float(tva_rate.replace(',', '.')) / 100
                    print(f"  TVA attendue ({tva_rate}%): {expected_tva:.2f}")
                    print(f"  TVA extraite: {tva_num}")
                    print(f"  Taux cohérent: {'✅' if abs(expected_tva - tva_num) < 0.01 else '❌'}")
                
            except ValueError as e:
                print(f"  ❌ Erreur de conversion: {e}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ Erreur lors du debug patterns: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Tester les 3 PDF problématiques"""
      # Chemins des PDF disponibles
    pdf_files = [
        "uploads/batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf",  # GIUSEPPE GLORIOSO
        "uploads/batch_5_1714_TVA_2200_IT_2025-02-04_FR50006WHCVZJU_11525.pdf",  # PDF Italien 2
        "uploads/batch_6_1715_TVA_2200_IT_2025-02-01_FR50006FHCVZJU_11525.pdf",  # PDF Italien 3
        "uploads/batch_7_1716_TVA_2000_FR_2025-04-28_FR5003KOHCVZJI_22966.pdf",  # PDF Français
    ]
    
    print("🔍 DEBUG EXTRACTION RÉELLE AVEC VRAIES FONCTIONS")
    print("=" * 80)
    
    for pdf_file in pdf_files:
        debug_extraction_complete(pdf_file)
        debug_patterns_extraction(pdf_file)

if __name__ == "__main__":
    main()
