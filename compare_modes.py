#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparaison debug vs non-debug avec le même texte
"""

import sys
import os

# Importer les fonctions de app.py
sys.path.append('.')
from app import extract_pdf_text, extract_pdf_tables_pdfplumber, parse_amazon_invoice_data

def compare_debug_modes():
    """Comparer les résultats debug vs non-debug avec le même contenu"""
    
    pdf_file = "1710 TVA 22,00% IT 2025-05-04 FR5003PAHCVZJI 93,52€.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Fichier PDF non trouvé: {pdf_file}")
        return
    
    print(f"🔍 COMPARAISON DEBUG vs NON-DEBUG")
    print(f"📁 Fichier: {pdf_file}")
    print("=" * 80)
    
    # Extraire le contenu une seule fois
    pdf_text = extract_pdf_text(pdf_file)
    pdf_tables = extract_pdf_tables_pdfplumber(pdf_file)
    
    # Fusionner le contenu
    pdf_content = pdf_text
    if pdf_tables:
        for table in pdf_tables:
            if table:
                pdf_content += "\n" + str(table)
    
    print(f"📝 Contenu extrait ({len(pdf_content)} caractères)")
    print(f"Premier extrait: {pdf_content[:200]}...")
    print()
    
    # Test en mode DEBUG
    print("🔍 TEST MODE DEBUG:")
    result_debug = parse_amazon_invoice_data(pdf_content, debug_mode=True, filename=pdf_file)
    if result_debug:
        print(f"   HT: {result_debug.get('ht', 0):.2f}€")
        print(f"   TVA: {result_debug.get('tva', 0):.2f}€")
        print(f"   Total: {result_debug.get('total', 0):.2f}€")
        print(f"   Taux: {result_debug.get('taux_tva', 'N/A')}")
    else:
        print("   ❌ Échec")
    
    print()
    
    # Test en mode NON-DEBUG
    print("🔍 TEST MODE NON-DEBUG:")
    result_no_debug = parse_amazon_invoice_data(pdf_content, debug_mode=False, filename=pdf_file)
    if result_no_debug:
        print(f"   HT: {result_no_debug.get('ht', 0):.2f}€")
        print(f"   TVA: {result_no_debug.get('tva', 0):.2f}€")
        print(f"   Total: {result_no_debug.get('total', 0):.2f}€")
        print(f"   Taux: {result_no_debug.get('taux_tva', 'N/A')}")
    else:
        print("   ❌ Échec")
    
    print()
    
    # Comparaison
    if result_debug and result_no_debug:
        print("🔍 COMPARAISON:")
        
        ht_match = abs(result_debug.get('ht', 0) - result_no_debug.get('ht', 0)) < 0.01
        tva_match = abs(result_debug.get('tva', 0) - result_no_debug.get('tva', 0)) < 0.01
        total_match = abs(result_debug.get('total', 0) - result_no_debug.get('total', 0)) < 0.01
        taux_match = result_debug.get('taux_tva') == result_no_debug.get('taux_tva')
        
        print(f"   HT: {'✅' if ht_match else '❌'} {result_debug.get('ht', 0):.2f} vs {result_no_debug.get('ht', 0):.2f}")
        print(f"   TVA: {'✅' if tva_match else '❌'} {result_debug.get('tva', 0):.2f} vs {result_no_debug.get('tva', 0):.2f}")
        print(f"   Total: {'✅' if total_match else '❌'} {result_debug.get('total', 0):.2f} vs {result_no_debug.get('total', 0):.2f}")
        print(f"   Taux: {'✅' if taux_match else '❌'} {result_debug.get('taux_tva')} vs {result_no_debug.get('taux_tva')}")
        
        if ht_match and tva_match and total_match and taux_match:
            print("\n✅ LES DEUX MODES DONNENT LES MÊMES RÉSULTATS")
            print("Le problème ne vient PAS de la différence debug/non-debug")
        else:
            print("\n❌ LES MODES DONNENT DES RÉSULTATS DIFFÉRENTS")
            print("C'est ça le problème !")
    else:
        print("❌ Impossible de comparer (un des tests a échoué)")

if __name__ == "__main__":
    compare_debug_modes()
