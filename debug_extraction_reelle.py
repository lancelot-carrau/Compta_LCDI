#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de l'extraction réelle sur les PDF problématiques
"""

import fitz  # PyMuPDF
import re
import os
from decimal import Decimal

def debug_extraction_pdf(pdf_path):
    """Debug de l'extraction d'un PDF spécifique"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG EXTRACTION: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Ouvrir le PDF
        doc = fitz.open(pdf_path)
        all_text = ""
        
        # Extraire tout le texte
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            all_text += page_text
        
        doc.close()
        
        print(f"📄 Texte extrait ({len(all_text)} caractères)")
        
        # Nettoyer le texte
        text_clean = re.sub(r'\s+', ' ', all_text.strip())
        
        print(f"\n📝 TEXTE NETTOYÉ (premiers 500 caractères):")
        print(text_clean[:500])
        print("...")
        
        # Chercher des patterns de montants
        print(f"\n💰 RECHERCHE DE MONTANTS:")
        
        # Patterns pour HT
        ht_patterns = [
            r'Subtotal\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Sous-total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Total\s*HT\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Prezzo\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Netto\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'([0-9,]+\.?[0-9]*)\s*€\s*[0-9,]+\.?[0-9]*\s*€\s*[0-9,]+\.?[0-9]*\s*€',  # Premier montant dans une série
        ]
        
        print("\n🔍 Recherche HT:")
        for i, pattern in enumerate(ht_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern}")
                print(f"    ✅ Trouvé: {matches}")
                
        # Patterns pour TVA
        tva_patterns = [
            r'TVA\s*\(?([0-9,]+\.?[0-9]*)\s*%?\)?\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'IVA\s*\(?([0-9,]+\.?[0-9]*)\s*%?\)?\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'VAT\s*\(?([0-9,]+\.?[0-9]*)\s*%?\)?\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Imposta\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Tax\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        print("\n🔍 Recherche TVA:")
        for i, pattern in enumerate(tva_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern}")
                print(f"    ✅ Trouvé: {matches}")
        
        # Patterns pour TOTAL
        total_patterns = [
            r'Total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Totale\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Gesamtbetrag\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'Grand\s*Total\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        print("\n🔍 Recherche TOTAL:")
        for i, pattern in enumerate(total_patterns):
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern}")
                print(f"    ✅ Trouvé: {matches}")
        
        # Rechercher des lignes avec plusieurs montants
        print(f"\n💡 LIGNES AVEC PLUSIEURS MONTANTS:")
        lines = text_clean.split('\n' if '\n' in text_clean else '. ')
        for i, line in enumerate(lines):
            # Chercher les lignes avec au moins 2 montants en euros
            euro_matches = re.findall(r'([0-9,]+\.?[0-9]*)\s*€', line)
            if len(euro_matches) >= 2:
                print(f"  Ligne {i+1}: {line.strip()}")
                print(f"    Montants trouvés: {euro_matches}")
        
        # Patterns spécifiques pour les cas problématiques
        print(f"\n🎯 PATTERNS SPÉCIFIQUES:")
        
        # Pour ADF INFORMATIQUE (chercher structure avec taux)
        adf_patterns = [
            r'([0-9,]+\.?[0-9]*)\s*€.*?([0-9,]+\.?[0-9]*)\s*€.*?([0-9,]+\.?[0-9]*)\s*€.*?([0-9,]+\.?[0-9]*)\s*%',
            r'Total\s*([0-9,]+\.?[0-9]*)\s*€\s*([0-9,]+\.?[0-9]*)\s*€\s*([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        for pattern in adf_patterns:
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  ADF Pattern: {pattern}")
                print(f"    ✅ Trouvé: {matches}")
        
        # Pour Zacharie/Giuseppe (chercher structure italienne)
        it_patterns = [
            r'Prezzo\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€.*?IVA.*?([0-9,]+\.?[0-9]*)\s*€.*?Totale\s*[:\s]*([0-9,]+\.?[0-9]*)\s*€',
            r'([0-9,]+\.?[0-9]*)\s*€.*?Imposta.*?([0-9,]+\.?[0-9]*)\s*€.*?([0-9,]+\.?[0-9]*)\s*€',
        ]
        
        for pattern in it_patterns:
            matches = re.findall(pattern, text_clean, re.IGNORECASE)
            if matches:
                print(f"  IT Pattern: {pattern}")
                print(f"    ✅ Trouvé: {matches}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")

def main():
    """Tester les 3 PDF problématiques"""
    
    # Chemins des PDF problématiques
    pdf_files = [
        "uploads/batch_1_1709_TVA_2000_FR_2025-01-27_FR50006WA8BC8T_85001.pdf",  # ADF INFORMATIQUE
        "uploads/batch_4_1711_TVA_2200_IT_2025-01-27_FR50006WA8BC8T_85003.pdf",  # Zacharie Carpentier
        "uploads/batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf",  # GIUSEPPE GLORIOSO
    ]
    
    print("🔍 DEBUG EXTRACTION RÉELLE SUR PDF PROBLÉMATIQUES")
    print("=" * 80)
    
    for pdf_file in pdf_files:
        debug_extraction_pdf(pdf_file)

if __name__ == "__main__":
    main()
