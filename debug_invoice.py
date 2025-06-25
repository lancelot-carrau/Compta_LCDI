#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import parse_amazon_invoice_data
import traceback

def debug_single_invoice():
    """Déboguer l'extraction sur une seule facture"""
    
    pdf_file = "uploads/1710 TVA 22,00% IT 2025-05-04 FR5003PAHCVZJI 93,52€.pdf"
    
    print(f"=== DÉBOGAGE DE LA FACTURE ===")
    print(f"Fichier: {pdf_file}")
    print(f"Fichier existe: {os.path.exists(pdf_file)}")
    
    try:
        result = parse_amazon_invoice_data(pdf_file)
        print(f"\nRésultat de l'extraction:")
        if result:
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("  Aucune donnée extraite (None ou dict vide)")
    except Exception as e:
        print(f"Erreur: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_single_invoice()
