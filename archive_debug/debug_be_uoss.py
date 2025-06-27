#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug détaillé pour les factures BE UOSS
"""

import os
import pandas as pd
from app import parse_amazon_invoice_data, extract_pdf_tables_pdfplumber

def debug_be_uoss():
    """Debug détaillé d'une facture BE UOSS"""
    
    # Test sur toutes les factures BE UOSS
    be_uoss_files = [
        "1771 TVA 21,00% BE 2024-12-20 INV-FR-UOSS-996613615-2024-2087 58,72€.pdf",
        "1772 TVA 21,00% BE 2024-12-20 INV-FR-UOSS-996613615-2024-2088 57,72€.pdf",
        "1773 TVA 21,00% BE 2025-01-02 INV-FR-UOSS-996613615-2024-2137 1103,97€.pdf"
    ]
    
    for filename in be_uoss_files:
        filepath = os.path.join("uploads", filename)
        
        if not os.path.exists(filepath):
            print(f"❌ Fichier introuvable: {filename}")
            continue
        
        print(f"\n{'='*60}")
        print(f"FICHIER: {filename}")
        print(f"{'='*60}")
        
        try:
            # Extraire le texte du PDF
            tables = extract_pdf_tables_pdfplumber(filepath)
            
            text_parts = []
            if tables:
                for table in tables:
                    try:
                        if hasattr(table, 'values'):
                            text_parts.append(' '.join([str(cell) for row in table.values for cell in row if cell is not None and str(cell) != 'nan']))
                        elif isinstance(table, list):
                            text_parts.append(' '.join([str(cell) for row in table for cell in row if cell]))
                    except Exception as table_error:
                        continue
            
            text_to_parse = ' '.join(text_parts)
            
            if text_to_parse:
                print(f"✅ Texte extrait: {len(text_to_parse)} caractères")
                
                # Parser avec debug activé
                data = parse_amazon_invoice_data(text_to_parse, debug_mode=True, filename=filename, pdf_path=filepath)
                
                if data:
                    print(f"\n✅ DONNÉES EXTRAITES:")
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                    
                    # Vérifier les conditions de validation
                    has_minimum_data = any([
                        data['id_amazon'],
                        data['facture_amazon'],
                        data['total'] > 0
                    ])
                    
                    print(f"\n📊 VALIDATION:")
                    print(f"  id_amazon: '{data['id_amazon']}' -> {bool(data['id_amazon'])}")
                    print(f"  facture_amazon: '{data['facture_amazon']}' -> {bool(data['facture_amazon'])}")
                    print(f"  total > 0: {data['total']} -> {data['total'] > 0}")
                    print(f"  HAS_MINIMUM_DATA: {has_minimum_data}")
                    
                    if has_minimum_data:
                        print("  ✅ FACTURE VALIDE - SERA INCLUSE")
                    else:
                        print("  ❌ FACTURE INVALIDE - SERA REJETÉE")
                        
                else:
                    print(f"\n❌ AUCUNE DONNÉE EXTRAITE")
            else:
                print("❌ Aucun texte extrait du PDF")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_be_uoss()
