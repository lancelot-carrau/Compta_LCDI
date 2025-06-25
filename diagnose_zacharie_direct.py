#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic direct de l'extraction dans app.py pour la facture Zacharie
"""

import sys
import os
import re
from datetime import datetime

# Importer les fonctions de app.py
sys.path.append('.')
from app import extract_pdf_text, extract_pdf_tables_pdfplumber, parse_amazon_invoice_data

def diagnose_zacharie_extraction():
    """Diagnostiquer l'extraction directe de la facture Zacharie"""
    
    pdf_file = "1709 TVA 20,00% FR 2025-05-03 FR5003OZHCVZJI 231,98€.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Fichier PDF non trouvé: {pdf_file}")
        return
    
    print(f"📄 DIAGNOSTIC DE L'EXTRACTION DIRECTE")
    print(f"📁 Fichier: {pdf_file}")
    print("=" * 70)
      # Étape 1: Extraction du contenu PDF
    print("🔍 ÉTAPE 1: Extraction du contenu PDF...")
    try:
        # Extraire le texte
        pdf_text = extract_pdf_text(pdf_file)
        
        # Extraire les tableaux
        pdf_tables = extract_pdf_tables_pdfplumber(pdf_file)
        
        # Fusionner le contenu
        pdf_content = pdf_text
        if pdf_tables:
            for table in pdf_tables:
                if table:
                    pdf_content += "\n" + str(table)
        
        print(f"   ✅ Contenu total extrait: {len(pdf_content)} caractères")
        print(f"   📝 Début: {pdf_content[:200]}...")
        
        # Chercher les montants dans le texte brut
        if "193,32" in pdf_content and "38,66" in pdf_content and "231,98" in pdf_content:
            print("   ✅ Montants attendus trouvés dans le texte brut!")
        else:
            print("   ⚠️ Montants attendus non trouvés dans le texte brut")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'extraction: {e}")
        return
    
    # Étape 2: Parsing des données
    print("\n🔍 ÉTAPE 2: Parsing des données...")
    try:        # Créer un dictionnaire comme dans l'application
        pdf_info = {
            'filename': pdf_file,
            'content': pdf_content,
            'path': pdf_file
        }
        
        # Parser les données
        parsed_data = parse_amazon_invoice_data(pdf_content, debug_mode=True, filename=pdf_file)
        
        print(f"   📊 Données parsées: {type(parsed_data)}")
        
        if parsed_data:
            print(f"   📋 RÉSULTAT DU PARSING:")
            print(f"      Client: {parsed_data.get('nom_contact', 'NON TROUVÉ')}")
            print(f"      Date: {parsed_data.get('date_facture', 'NON TROUVÉE')}")
            print(f"      Numéro: {parsed_data.get('facture_amazon', 'NON TROUVÉ')}")
            print(f"      💰 HT: {parsed_data.get('ht', 0):.2f}€")
            print(f"      💰 TVA: {parsed_data.get('tva', 0):.2f}€")
            print(f"      💰 TOTAL: {parsed_data.get('total', 0):.2f}€")
            print(f"      📊 Taux TVA: {parsed_data.get('taux_tva', 'NON TROUVÉ')}")
            print(f"      🌍 Pays: {parsed_data.get('pays', 'NON TROUVÉ')}")
        else:
            print("   ❌ Aucune donnée parsée!")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_zacharie_extraction()
