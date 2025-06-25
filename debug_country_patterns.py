#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour débugger spécifiquement les patterns country et total
"""

import re

# Texte du premier PDF
text1 = """VIA CIVITA CASTELLANA 24, SECONDO PIANO
CASTEL SANT'ELIA, VITERBO, 01030
IT
Per domande relative al tuo ordine, ti preghiamo di visitare il sito www.amazon.it/contact-us
Indirizzo di fatturazione
Cristina Moraru
Via Civita Castellana 24, Secondo piano
Castel Sant'Elia, Viterbo, 01030
IT"""

# Texte du deuxième PDF
text2 = """10 SHALOM, FLT 2,, ROMEO ROMANO STR,
ST' VENERA, MALTA, SVR1191
MT
Per domande relative al tuo ordine, ti preghiamo di visitare il sito www.amazon.it/contact-us
Indirizzo di fatturazione
Grixti Charles
10 Shalom, Flt 2,, Romeo Romano Str,
St' Venera, Malta, SVR1191
MT"""

def debug_patterns():
    """Debug les patterns country et total"""
    
    texts = [text1, text2]
    
    for i, text in enumerate(texts, 1):
        print(f"\n{'='*60}")
        print(f"DEBUG TEXTE {i}")
        print('='*60)
        print(f"Texte:\n{text}")
        print("-"*40)
        
        # Test patterns country
        print("PATTERNS COUNTRY:")
        country_patterns = [
            r'(\d{5})\s*\n([A-Z]{2})(?:\s|$)',
            r'(\d{5})\s*([A-Z]{2})(?:\s|$)',
            r'\n([A-Z]{2})\s*$',
            r'\b([A-Z]{2})\s*$',
            r'\b(IT|FR|DE|ES|MT|NL|BE|AT|PT|CH|UK|GB)\b',
        ]
        
        for j, pattern in enumerate(country_patterns, 1):
            matches = re.findall(pattern, text, re.MULTILINE)
            print(f"  {j}. Pattern '{pattern}' -> {matches}")
        
        # Test avec recherche
        for j, pattern in enumerate(country_patterns, 1):
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                print(f"  {j}. MATCH '{pattern}' -> groups: {match.groups()}, value: '{match.group(1) if len(match.groups()) >= 1 else 'N/A'}'")

if __name__ == "__main__":
    debug_patterns()
