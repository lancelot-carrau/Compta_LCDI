#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer les fonctions de app.py
from app import extract_pdf_text, process_pdf_extraction, parse_amazon_invoice_data

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
        
        if not result or not result.get('success'):
            print("❌ Échec de l'extraction du PDF")
            if result and result.get('errors'):
                print(f"Erreurs: {result['errors']}")
            return
        
        print("✅ Extraction brute réussie!")
        text = result.get('text', '')
        
        if not text:
            print("❌ Aucun texte extrait")
            return
        
        print(f"📝 Texte extrait: {len(text)} caractères")
        print(f"Premiers 200 caractères: {text[:200]}")
        
        # Parse des données de facture
        print("\n🔍 Parsing des données de facture...")
        invoice_data = parse_amazon_invoice_data(text, debug_mode=True, filename=os.path.basename(pdf_path))
        
        if not invoice_data:
            print("❌ Aucune donnée de facture extraite")
            return
        
        print("✅ Données de facture extraites!")
        for key, value in invoice_data.items():
            print(f"  {key}: {value}")
        
        # Vérification des champs requis
        required_fields = ['company_name', 'invoice_date', 'total_amount', 'ht_amount', 'vat_amount', 'vat_rate']
        missing_fields = []
        
        for field in required_fields:
            if not invoice_data.get(field) or invoice_data.get(field) in ['N/A', '', None]:
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
    # Test d'un seul fichier problématique
    uploads_dir = r"c:\Code\Apps\Compta LCDI Rollback\uploads"
    
    test_file = "batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf"
    pdf_path = os.path.join(uploads_dir, test_file)
    test_single_pdf(pdf_path)

if __name__ == "__main__":
    main()
