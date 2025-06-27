#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import pdfplumber

def analyze_table_structure(pdf_path):
    """Analyser la structure des tableaux dans la facture problématique"""
    print(f"\n{'='*60}")
    print(f"ANALYSE DES TABLEAUX DANS: {pdf_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"\n📄 PAGE {page_num + 1}:")
                
                # Extraire les tableaux
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables):
                        print(f"\n🔍 TABLEAU {table_num + 1}:")
                        print(f"   Nombre de lignes: {len(table) if table else 0}")
                        
                        if table:
                            for row_num, row in enumerate(table):
                                print(f"   Ligne {row_num + 1}: {row}")
                                
                                # Analyser chaque cellule pour les montants
                                for cell_num, cell in enumerate(row):
                                    if cell and '€' in str(cell):
                                        print(f"      Cellule {cell_num + 1} (€): '{cell}' -> Type: {type(cell)}")
                                        
                                        # Tester le nettoyage
                                        cell_str = str(cell).strip()
                                        print(f"         Brut: '{cell_str}'")
                                        
                                        # Test des remplacements
                                        test1 = cell_str.replace('€', '').replace(',', '.')
                                        print(f"         Après €→'' et ,→.: '{test1}'")
                                        
                                        test2 = test1.replace('-€', '-')
                                        print(f"         Après -€→-: '{test2}'")
                                        
                                        test3 = test2.replace('- €', '-')
                                        print(f"         Après - €→-: '{test3}'")
                                        
                                        test4 = test3.strip()
                                        print(f"         Final après strip(): '{test4}'")
                                        
                                        try:
                                            value = float(test4)
                                            print(f"         ✅ Conversion réussie: {value}")
                                        except Exception as e:
                                            print(f"         ❌ Erreur conversion: {e}")
                else:
                    print(f"   Aucun tableau trouvé sur cette page")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    # Analyser la facture problématique
    pdf_path = os.path.join("uploads", "1766 TVA 22,00% IT 2025-05-07 FR500023HCVZJQ -115,25€.pdf")
    analyze_table_structure(pdf_path)
