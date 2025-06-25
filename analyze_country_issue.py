#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple pour analyser les patterns de pays et identifier pourquoi "DE" est extrait au lieu de "FR"
"""

import re

def analyze_country_patterns():
    """Analyser les patterns de pays sur un texte français"""
    
    # Texte simulé d'une facture française Amazon
    text_fr = """
Amazon EU Sarl
5 Rue Plaetis
L-2338 Luxembourg

Ship to:
Jean Dupont
123 Rue de la Paix
75001 Paris
FR

Order #: 171-2345678-9012345
Invoice Number: FR12345678AB
Date de facturation: 15 juin 2024
Total de la facture: 29,99 €
TVA: 4,99 €
Sous-total: 25,00 €
Taux TVA: 20%
"""

    print("=" * 50)
    print("ANALYSE DES PATTERNS DE PAYS")
    print("=" * 50)
    print(f"Texte analysé:\n{text_fr}")
    print("-" * 50)
    
    # Patterns de pays dans l'ordre actuel
    country_patterns = [
        # Patterns pour adresses complètes
        r'(?:Ship\s*to|Livraison|Spedire\s*a|Address|Indirizzo|Facturation|Bill\s*to)[\s\S]*?(\d{5})\s*\n?\s*(FR)\b',
        r'(?:Ship\s*to|Livraison|Spedire\s*a|Address|Indirizzo|Facturation|Bill\s*to)[\s\S]*?(\d{5})\s+(FR)\b',
        # Patterns pour codes postaux + pays
        r'(\d{5})\s*\n\s*(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH)\b',
        r'(\d{5})\s+(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH)\b',
        # Patterns spécifiques pays européens en contexte d'adresse
        r'(?:Ship\s*to|Livraison|Spedire\s*a|Address|Indirizzo|Facturation|Bill\s*to)[\s\S]*?\b(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b',
        # Patterns pour codes pays en fin de ligne d'adresse
        r'\n\s*(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\s*$',
        r'\b(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\s*$',
        # Fallback patterns génériques
        r'\b(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b'
    ]
    
    print("RÉSULTATS DES PATTERNS:")
    print("-" * 50)
    
    for i, pattern in enumerate(country_patterns):
        matches = list(re.finditer(pattern, text_fr, re.IGNORECASE | re.MULTILINE))
        print(f"Pattern {i+1}: {pattern}")
        if matches:
            for match in matches:
                if len(match.groups()) == 2:
                    print(f"  -> Match avec 2 groupes: {match.groups()}, pays: {match.groups()[1]}")
                else:
                    print(f"  -> Match simple: {match.group(1)}")
            print()
        else:
            print("  -> Aucun match")
            print()
    
    print("=" * 50)
    print("RECHERCHE MANUELLE DES OCCURRENCES")
    print("=" * 50)
    
    # Rechercher toutes les occurrences de codes pays dans le texte
    all_countries = re.findall(r'\b(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b', text_fr, re.IGNORECASE)
    print(f"Tous les codes pays trouvés: {all_countries}")
    
    # Rechercher spécifiquement "DE" pour voir d'où il vient
    de_matches = list(re.finditer(r'\bDE\b', text_fr, re.IGNORECASE))
    print(f"Occurrences de 'DE': {len(de_matches)}")
    for match in de_matches:
        start, end = match.span()
        context = text_fr[max(0, start-20):end+20]
        print(f"  Position {start}-{end}: ...{context}...")
    
    # Rechercher spécifiquement "FR"
    fr_matches = list(re.finditer(r'\bFR\b', text_fr, re.IGNORECASE))
    print(f"Occurrences de 'FR': {len(fr_matches)}")
    for match in fr_matches:
        start, end = match.span()
        context = text_fr[max(0, start-20):end+20]
        print(f"  Position {start}-{end}: ...{context}...")
    
    print("\n" + "=" * 50)
    print("RECOMMANDATIONS")
    print("=" * 50)
    
    # Recommandations pour améliorer l'extraction
    print("1. Le pattern générique r'\\b(FR|IT|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\\b' capture TOUS les codes pays")
    print("2. Il faut utiliser un système de priorité pour privilégier les codes pays dans les adresses")
    print("3. Les patterns avec contexte d'adresse doivent être prioritaires")
    print("4. Les patterns génériques doivent être en dernier recours")

if __name__ == "__main__":
    analyze_country_patterns()
