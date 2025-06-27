#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse spécifique de la facture NL avec montant négatif format "€ 115,78-"
"""

import sys
import os
sys.path.append('.')

from app import process_pdf_extraction, parse_amazon_invoice_data
import re

def extract_date_from_paid_box(text):
    """Extraire la date depuis l'encadré Payé/Remboursé au format DD Month YYYY"""
    
    # Dictionnaire des mois en différentes langues
    months_dict = {
        # Français
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12',
        
        # Anglais
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        
        # Allemand
        'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
        'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12',
        
        # Italien
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
        
        # Espagnol
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        
        # Néerlandais
        'januari': '01', 'februari': '02', 'maart': '03', 'april': '04',
        'mei': '05', 'juni': '06', 'juli': '07', 'augustus': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'december': '12',
        
        # Versions courtes communes
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Recherche des termes "Payé" ou "Remboursé" en différentes langues
    paid_keywords = [
        'payé', 'paid', 'betaald', 'pagato', 'pagado', 'bezahlt',
        'remboursé', 'refunded', 'terugbetaald', 'rimborsato', 'reembolsado', 'erstattet'
    ]
    
    # Construire le pattern pour les mots-clés
    keywords_pattern = '|'.join(paid_keywords)
    
    # Recherche du contexte autour des mots-clés avec date
    for keyword_match in re.finditer(f'({keywords_pattern})', text, re.IGNORECASE):
        # Récupérer 200 caractères autour du mot-clé
        start = max(0, keyword_match.start() - 100)
        end = min(len(text), keyword_match.end() + 100)
        context = text[start:end]
        
        # Recherche du pattern DD Month YYYY dans ce contexte
        date_pattern = r'(\d{1,2})\s+([a-zA-ZÀ-ÿ]+)\s+(\d{4})'
        date_matches = re.findall(date_pattern, context, re.IGNORECASE)
        
        for day, month_name, year in date_matches:
            month_lower = month_name.lower().strip()
            
            # Vérifier si le mois est dans notre dictionnaire
            if month_lower in months_dict:
                day_formatted = day.zfill(2)
                month_formatted = months_dict[month_lower]
                formatted_date = f"{day_formatted}/{month_formatted}/{year}"
                
                print(f"  🔍 Trouvé dans contexte '{keyword_match.group()}': {day} {month_name} {year}")
                print(f"  📅 Formaté: {formatted_date}")
                
                return formatted_date
    
    print(f"  ❌ Aucune date trouvée dans les encadrés Payé/Remboursé")
    return None

def analyze_nl_negative():
    """Analyser la facture NL avec montant négatif manqué"""
    
    print("=== ANALYSE FACTURE NL NÉGATIVE ===\n")
    
    # Facture NL négative spécifique
    filename = "1770 TVA 21,00% NL 2025-05-06 FR500026HCVZJQ -115,78€.pdf"
    pdf_path = f"uploads/{filename}"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    print(f"📁 Analyse de: {filename}")
    
    # Extraction du PDF
    pdf_results = process_pdf_extraction(pdf_path, 'auto')
    if not pdf_results['success']:
        print(f"❌ Échec extraction PDF: {pdf_results['errors']}")
        return
    
    text = pdf_results['text']
    print(f"✅ Texte extrait: {len(text)} caractères")
    
    # Recherche du format "€ 115,78-"
    print(f"\n🔍 RECHERCHE DU FORMAT '€ XXX,XX-':")
    
    patterns = [
        r'€\s*(\d+[,.]?\d{0,2})-',  # € 115,78-
        r'€\s*(\d+[,.]?\d{0,2})\s*-',  # € 115,78 -
        r'(\d+[,.]?\d{0,2})\s*€\s*-',  # 115,78 € -
        r'(\d+[,.]?\d{0,2})\s*€-',     # 115,78€-
        r'-\s*€\s*(\d+[,.]?\d{0,2})',  # - € 115,78
        r'-€\s*(\d+[,.]?\d{0,2})',     # -€ 115,78
    ]
    
    for i, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"  Pattern {i}: {pattern}")
        if matches:
            print(f"  ✅ Trouvé: {matches}")
        else:
            print(f"  ❌ Aucun match")
    
    # Affichage du texte brut pour comprendre le format
    print(f"\n💰 RECHERCHE DE TOUS LES MONTANTS AVEC €:")
    euro_matches = re.findall(r'€[^a-zA-Z]*?\d+[,.]?\d{0,2}[^a-zA-Z]*?', text, re.IGNORECASE)
    for match in euro_matches:
        print(f"  💶 {match.strip()}")
    
    # Contexte autour de "Total"
    print(f"\n🎯 CONTEXTE AUTOUR DE 'TOTAL':")
    total_contexts = []
    for match in re.finditer(r'.{0,50}[Tt]otal.{0,50}', text, re.IGNORECASE):
        context = match.group().replace('\n', ' ').strip()
        total_contexts.append(context)
    
    for i, context in enumerate(total_contexts, 1):
        print(f"  Context {i}: {context}")
    
    # Test avec l'extraction normale
    print(f"\n🧪 TEST D'EXTRACTION AVEC parse_amazon_invoice_data:")
    
    # Nouvelle extraction de date depuis l'encadré Payé/Remboursé
    print(f"\n📅 EXTRACTION DATE DEPUIS ENCADRÉ PAYÉ/REMBOURSÉ:")
    paid_date = extract_date_from_paid_box(text)
    if paid_date:
        print(f"✅ Date trouvée dans encadré: {paid_date}")
    else:
        print(f"❌ Date non trouvée dans encadré Payé/Remboursé")
    
    invoice_data = parse_amazon_invoice_data(
        text, 
        debug_mode=True, 
        filename=filename, 
        pdf_path=pdf_path
    )
    
    if invoice_data:
        print(f"✅ Données extraites:")
        for key, value in invoice_data.items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ Échec de l'extraction")

if __name__ == "__main__":
    analyze_nl_negative()
