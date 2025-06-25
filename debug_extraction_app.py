#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug de l'extraction réelle en utilisant les fonctions de app.py
"""

import os
import sys

# Ajouter le répertoire courant au path pour importer app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_data, extract_amounts_from_text

def debug_extraction_avec_app(pdf_path):
    """Debug de l'extraction d'un PDF en utilisant les vraies fonctions de app.py"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG EXTRACTION AVEC APP.PY: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Utiliser la vraie fonction d'extraction de app.py
        result = extract_pdf_data(pdf_path)
        
        print(f"📄 Résultat d'extraction:")
        print(f"  Type: {type(result)}")
        print(f"  Contenu: {result}")
        
        if isinstance(result, dict):
            print(f"\n📊 DONNÉES EXTRAITES:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        
        # Si c'est une liste, afficher chaque élément
        elif isinstance(result, list):
            print(f"\n📊 LISTE DES FACTURES EXTRAITES ({len(result)} factures):")
            for i, invoice in enumerate(result):
                print(f"\n  📋 Facture {i+1}:")
                if isinstance(invoice, dict):
                    for key, value in invoice.items():
                        print(f"    {key}: {value}")
                else:
                    print(f"    Données: {invoice}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        import traceback
        traceback.print_exc()

def debug_extraction_texte(pdf_path):
    """Debug de l'extraction du texte brut"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG TEXTE BRUT: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Importer la fonction d'extraction de texte
        import fitz
        
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
        
        # Tester extract_amounts_from_text
        amounts = extract_amounts_from_text(all_text)
        
        print(f"\n💰 MONTANTS EXTRAITS PAR extract_amounts_from_text:")
        if isinstance(amounts, dict):
            for key, value in amounts.items():
                print(f"  {key}: {value}")
        else:
            print(f"  Résultat: {amounts}")
        
        # Afficher un extrait du texte
        print(f"\n📝 EXTRAIT DU TEXTE (premiers 1000 caractères):")
        print(all_text[:1000])
        print("...")
        
        print(f"\n{'='*80}")
        
    except ImportError:
        print(f"❌ Module fitz non disponible, utilisation de l'extraction complète seulement")
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction du texte: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Tester les 3 PDF problématiques"""
    
    # Chemins des PDF problématiques
    pdf_files = [
        "uploads/batch_1_1709_TVA_2000_FR_2025-01-27_FR50006WA8BC8T_85001.pdf",  # ADF INFORMATIQUE
        "uploads/batch_4_1711_TVA_2200_IT_2025-01-27_FR50006WA8BC8T_85003.pdf",  # Zacharie Carpentier
        "uploads/batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf",  # GIUSEPPE GLORIOSO
    ]
    
    print("🔍 DEBUG EXTRACTION RÉELLE AVEC APP.PY")
    print("=" * 80)
    
    for pdf_file in pdf_files:
        debug_extraction_avec_app(pdf_file)
        debug_extraction_texte(pdf_file)

if __name__ == "__main__":
    main()
