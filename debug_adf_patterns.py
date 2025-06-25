#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test spécifique pour déboguer les patterns HT sur ADF INFORMATIQUE
"""

import re

# Test de la ligne problématique d'ADF INFORMATIQUE
text_adf = """
Total à payer 229,66 €ADF INFORMATIQUE
20 % 191,38 € 38,28 €
Total 191,38 € 38,28 €
Veuillez vous référer à la première page pour les informations de paiementMontant dû 229,66 €
"""

# Patterns HT prioritaires que j'ai ajoutés
new_patterns = [
    (r'Total\s+(\d+[,.]?\d{0,2})\s*€\s+\d+[,.]?\d{0,2}\s*€', 'Pattern français Total HT TVA'),
    (r'Sous-total\s+(\d+[,.]?\d{0,2})\s*€\s+\d+[,.]?\d{0,2}\s*€', 'Pattern français Sous-total HT TVA'),
    (r'(\d+)%\s+([\d,]+)\s*€\s+[\d,]+\s*€', 'Pattern italien % HT TVA'),
]

# Patterns génériques existants qui posent problème
old_patterns = [
    (r'(?:Total|Totale\s*da\s*pagare|Amount\s*Due|Montant\s*dû)[^€]*€\s*(\d+[,.]?\d{0,2})', 'Total générique (problématique)'),
    (r'Total[:\s]+(\d+[,.]?\d{0,2})\s*€(?!\s*HT)', 'Total simple'),
]

print("🔍 DEBUG PATTERNS HT pour ADF INFORMATIQUE")
print("=" * 60)
print(f"Texte à analyser:\n{text_adf}")
print("\n" + "=" * 60)

print("\n✅ NOUVEAUX PATTERNS HT (prioritaires):")
for pattern, name in new_patterns:
    matches = re.findall(pattern, text_adf, re.IGNORECASE)
    if matches:
        for match in matches:
            if isinstance(match, tuple):
                # Pattern avec 2 groupes - choisir le bon
                if '%)' in pattern:
                    value = match[1]  # Italien: prendre HT (2ème groupe)
                    print(f"   ✅ {name}: Taux={match[0]}%, HT={value}€")
                else:
                    value = match[0]  # Français: prendre HT (1er groupe)
                    print(f"   ✅ {name}: HT={value}€")
            else:
                print(f"   ✅ {name}: {match}€")
    else:
        print(f"   ❌ {name}: pas de match")

print("\n⚠️ ANCIENS PATTERNS (conflictuels):")
for pattern, name in old_patterns:
    matches = re.findall(pattern, text_adf, re.IGNORECASE)
    if matches:
        for match in matches:
            print(f"   ⚠️  {name}: {match}€ (capte le TOTAL au lieu du HT!)")
    else:
        print(f"   ❌ {name}: pas de match")

print("\n🎯 ANALYSE:")
print("- Le bon HT devrait être: 191,38€ (de la ligne 'Total 191,38 € 38,28 €')")
print("- Le bon TOTAL devrait être: 229,66€ (de la ligne 'Total à payer 229,66 €')")
print("- La TVA est correcte: 38,28€")

# Test manuel du pattern exact
print("\n🔧 TEST MANUEL DU PATTERN:")
test_pattern = r'Total\s+(\d+[,.]?\d{0,2})\s*€\s+\d+[,.]?\d{0,2}\s*€'
matches = re.findall(test_pattern, text_adf, re.IGNORECASE)
print(f"Pattern: {test_pattern}")
print(f"Matches: {matches}")

if matches:
    ht_value = matches[0].replace(',', '.')
    print(f"✅ HT extrait: {ht_value}€")
else:
    print("❌ Aucun match - le pattern doit être ajusté")
