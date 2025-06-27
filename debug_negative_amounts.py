#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from app import parse_amazon_invoice_data, process_pdf_extraction

def debug_specific_invoice(pdf_path, invoice_name):
    """Debug spécifique d'une facture problématique"""
    print(f"\n{'='*60}")
    print(f"ANALYSE DÉTAILLÉE DE: {invoice_name}")
    print(f"Fichier: {pdf_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    # Extraction du texte brut
    extraction_result = process_pdf_extraction(pdf_path)
    if not extraction_result['success']:
        print(f"❌ Échec de l'extraction PDF: {extraction_result['errors']}")
        return
    
    text = extraction_result['text']
    print(f"✅ Texte extrait: {len(text)} caractères")
    
    # Recherche des patterns de montants négatifs
    print(f"\n🔍 RECHERCHE DES MONTANTS NÉGATIFS:")
    
    # Patterns pour montants négatifs (y compris format -€)
    negative_patterns = [
        r'Totale da pagare\s*-€\s*(\d+[,.]?\d{0,2})',  # -€ 115,25
        r'Totale\s+-€\s*(\d+[,.]?\d{0,2})\s+-€\s*(\d+[,.]?\d{0,2})',  # Totale -€ 94,47 -€ 20,78
        r'Total\s+(?:pendiente|à payer|te betalen|da pagare)\s+(-\d+[,.]?\d{0,2})\s*€',
        r'Total\s+(?:pendiente|à payer|te betalen|da pagare)\s*€\s*(-\d+[,.]?\d{0,2})',
        r'Totale da pagare\s*€\s*(-\d+[,.]?\d{0,2})',
        r'Totale da pagare\s+(-\d+[,.]?\d{0,2})\s*€',
        r'Total à payer\s*€\s*(-\d+[,.]?\d{0,2})',
        r'Total à payer\s+(-\d+[,.]?\d{0,2})\s*€',
        r'Avoir total\s+(-\d+[,.]?\d{0,2})\s*€',
        r'Total pendiente\s*(-\d+[,.]?\d{0,2})\s*€',
        r'Total pendiente\s*€\s*(-\d+[,.]?\d{0,2})',
        r'Totaal te betalen\s*€\s*(-\d+[,.]?\d{0,2})',
        r'Totaal te betalen\s+(-\d+[,.]?\d{0,2})\s*€',
        r'(-\d+[,.]?\d{0,2})\s*€',  # Pattern général pour montant négatif
        r'€\s*(-\d+[,.]?\d{0,2})',   # Pattern général pour montant négatif après €
        r'-€\s*(\d+[,.]?\d{0,2})'   # Pattern spécifique pour -€ XXXX
    ]
    
    for i, pattern in enumerate(negative_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  Pattern {i+1}: {pattern}")
            print(f"  ✅ Trouvé: {matches}")
        else:
            print(f"  Pattern {i+1}: ❌ Aucun match")
    
    # Recherche de tous les montants avec €
    print(f"\n💰 TOUS LES MONTANTS AVEC € :")
    all_amounts = re.findall(r'(-?\d+[,.]?\d{0,2})\s*€|€\s*(-?\d+[,.]?\d{0,2})', text)
    for amount in all_amounts:
        # amount est un tuple, prendre la valeur non-vide
        value = amount[0] if amount[0] else amount[1]
        print(f"  💶 {value}€")
    
    # Recherche spécifique du texte autour de "Total"
    print(f"\n🎯 CONTEXTE AUTOUR DE 'TOTAL':")
    total_contexts = re.findall(r'.{0,50}[Tt]otal.{0,50}', text, re.IGNORECASE)
    for i, context in enumerate(total_contexts):
        print(f"  Context {i+1}: {context.strip()}")
    
    # Test de l'extraction avec notre fonction
    print(f"\n🧪 TEST D'EXTRACTION AVEC parse_amazon_invoice_data:")
    invoice_data = parse_amazon_invoice_data(text, debug_mode=True, filename=invoice_name, pdf_path=pdf_path)
    
    if invoice_data:
        print(f"✅ Données extraites:")
        for key, value in invoice_data.items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ Aucune donnée extraite")

if __name__ == "__main__":
    # Analyser les factures potentiellement problématiques
    factures_to_check = [
        ("1765 - FR5000J6HCVZJU", "1765 TVA 22,00% IT 2025-05-07 FR5000J6HCVZJU 115,25€.pdf"),
        ("1766 - FR500023HCVZJQ", "1766 TVA 22,00% IT 2025-05-07 FR500023HCVZJQ -115,25€.pdf")
    ]
    
    uploads_dir = "uploads"
    
    for name, filename in factures_to_check:
        pdf_path = os.path.join(uploads_dir, filename)
        debug_specific_invoice(pdf_path, name)
        print(f"\n{'='*80}\n")
