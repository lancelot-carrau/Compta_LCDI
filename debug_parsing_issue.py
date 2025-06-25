#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer les fonctions de app.py
from app import extract_pdf_text, process_pdf_extraction

def test_single_pdf(pdf_path):
    """Test l'extraction d'un seul PDF pour diagnostiquer les problèmes"""
    print(f"=== TEST PDF: {pdf_path} ===")
      if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Test de l'extraction complète
        print("📄 Traitement du PDF...")
        result = process_pdf_extraction(pdf_path, 'auto')
        
        if not result:
            print("❌ Aucun résultat de l'extraction")
            return
        
        print("✅ Extraction réussie!")
        print(f"📝 Résultat:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        # Vérification des champs requis
        required_fields = ['company_name', 'invoice_date', 'total_amount', 'ht_amount', 'vat_amount', 'vat_rate']
        missing_fields = []
        
        for field in required_fields:
            if not result.get(field) or result.get(field) in ['N/A', '', None]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️  Champs manquants: {missing_fields}")
        else:
            print("✅ Tous les champs requis sont présents")
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Test des fichiers problématiques
    uploads_dir = r"c:\Code\Apps\Compta LCDI Rollback\uploads"
    
    test_files = [
        "batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf",
        "batch_5_1714_TVA_2200_IT_2025-02-04_FR50006WHCVZJU_11525.pdf",
        "batch_6_1715_TVA_2200_IT_2025-02-01_FR50006FHCVZJU_11525.pdf",
        "batch_7_1716_TVA_2000_FR_2025-04-28_FR5003KOHCVZJI_22966.pdf"
    ]
    
    for filename in test_files:
        pdf_path = os.path.join(uploads_dir, filename)
        test_single_pdf(pdf_path)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
