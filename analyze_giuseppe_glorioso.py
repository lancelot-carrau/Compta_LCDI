#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyser la facture GIUSEPPE GLORIOSO (TVA 0%) pour comprendre le problème d'extraction
"""

import sys
import os
import re

# Importer les fonctions de app.py
sys.path.append('.')
from app import extract_pdf_text, extract_pdf_tables_pdfplumber, parse_amazon_invoice_data

def analyze_giuseppe_glorioso():
    """Analyser la facture GIUSEPPE GLORIOSO (TVA 0%)"""
    
    pdf_file = "1710 TVA 22,00% IT 2025-05-04 FR5003PAHCVZJI 93,52€.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Fichier PDF non trouvé: {pdf_file}")
        return
    
    print(f"🔍 ANALYSE DE LA FACTURE GIUSEPPE GLORIOSO (TVA 0%)")
    print(f"📁 Fichier: {pdf_file}")
    print("=" * 80)
    
    # D'après le nom du fichier, on s'attend à une TVA de 22% mais le contenu devrait montrer TVA 0%
    expected_ht = 93.52  # Montant du fichier, probablement le total
    expected_tva = 0.0   # TVA à 0%
    expected_total = 93.52
    expected_taux = "0%"
    
    print(f"💰 MONTANTS ATTENDUS (d'après l'analyse précédente):")
    print(f"   HT: {expected_ht:.2f}€")
    print(f"   TVA: {expected_tva:.2f}€")
    print(f"   TOTAL: {expected_total:.2f}€")
    print(f"   Taux TVA: {expected_taux}")
    print()
    
    # Extraire le contenu
    pdf_text = extract_pdf_text(pdf_file)
    pdf_tables = extract_pdf_tables_pdfplumber(pdf_file)
    
    # Fusionner le contenu
    pdf_content = pdf_text
    if pdf_tables:
        for table in pdf_tables:
            if table:
                pdf_content += "\n" + str(table)
    
    print(f"📝 CONTENU EXTRAIT ({len(pdf_content)} caractères):")
    print(pdf_content[:800] + "...")
    print()
    
    # Rechercher des indices de TVA à 0%
    print(f"🔍 RECHERCHE DE MOTS-CLÉS TVA:")
    tva_keywords = ['TVA', 'IVA', 'VAT', '0%', '22%', '0,00', '22,00']
    for keyword in tva_keywords:
        lines_with_keyword = []
        for i, line in enumerate(pdf_content.split('\n')):
            if keyword in line:
                lines_with_keyword.append((i, line))
        
        if lines_with_keyword:
            print(f"   🔍 '{keyword}' trouvé dans {len(lines_with_keyword)} lignes:")
            for i, line in lines_with_keyword[:5]:  # Limiter à 5 lignes
                print(f"      Ligne {i}: {line.strip()}")
        else:
            print(f"   ❌ '{keyword}' non trouvé")
    
    print()
    
    # Rechercher tous les montants
    print(f"🔍 TOUS LES MONTANTS TROUVÉS:")
    amounts = re.findall(r'(\d+[,.]?\d{0,2})\s*€', pdf_content)
    amounts_unique = list(set(amounts))
    amounts_unique.sort(key=lambda x: float(x.replace(',', '.')))
    print(f"   Montants uniques: {amounts_unique}")
    
    # Rechercher le contexte de 93.52 ou 93,52
    print(f"\n🔍 CONTEXTE DU MONTANT 93.52/93,52:")
    for i, line in enumerate(pdf_content.split('\n')):
        if '93.52' in line or '93,52' in line:
            print(f"   Ligne {i}: {line.strip()}")
            # Afficher aussi les lignes avant/après
            lines = pdf_content.split('\n')
            for j in range(max(0, i-2), min(len(lines), i+3)):
                if j != i:
                    print(f"   Contexte {j}: {lines[j].strip()}")
            break
    
    # Test du parsing
    print(f"\n🧪 TEST DU PARSING:")
    parsed_data = parse_amazon_invoice_data(pdf_content, debug_mode=True, filename=pdf_file)
    
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
        
        # Vérifier les erreurs
        extracted_tva = parsed_data.get('tva', 0)
        if extracted_tva > 0:
            print(f"\n❌ PROBLÈME DÉTECTÉ: TVA extraite = {extracted_tva:.2f}€ (attendu: 0€)")
        else:
            print(f"\n✅ TVA correcte: {extracted_tva:.2f}€")
            
        # Afficher les infos debug importantes
        if 'debug_info' in parsed_data:
            print(f"\n🔍 INFOS DEBUG (TVA):")
            for line in parsed_data['debug_info']:
                if 'tva' in line.lower() or 'iva' in line.lower() or 'vat' in line.lower():
                    print(f"   {line}")
    else:
        print(f"   ❌ Aucune donnée parsée!")

if __name__ == "__main__":
    analyze_giuseppe_glorioso()
