#!/usr/bin/env python3
"""Test de la normalisation des références"""

import re
import pandas as pd

def normalize_reference_format(ref):
    """
    Normalise le format des références pour améliorer les correspondances
    Gère les formats LCDI-XXXX, #LCDI-XXXX, #lcdi-xxxx, etc.
    """
    if pd.isna(ref) or ref == '':
        return ref
    
    ref_str = str(ref).strip().upper()
    
    # Pattern pour capturer LCDI-XXXX avec ou sans #
    lcdi_pattern = r'#?LCDI[-_]?(\d+)'
    matches = re.findall(lcdi_pattern, ref_str)
    
    if matches:
        # Retourner au format standard #LCDI-XXXX
        return f"#LCDI-{matches[0]}"
    
    # Si pas de pattern LCDI, essayer de capturer juste les chiffres
    numbers = re.findall(r'\d+', ref_str)
    if numbers:
        return f"#{numbers[0]}"
    
    return ref

print("=== TEST DE NORMALISATION DES RÉFÉRENCES ===")

# Test avec les références problématiques
test_refs = [
    "#LCDI-1006",
    "#LCDI-1008", 
    "LCDI-1006",
    "LCDI-1008",
    "#lcdi-1006",
    "#lcdi-1008"
]

for ref in test_refs:
    normalized = normalize_reference_format(ref)
    print(f"{ref:12} -> {normalized}")

print("\n⚠️ Recherche de problèmes potentiels:")
print("Si deux références différentes donnent la même forme normalisée,")
print("cela peut causer des mélanges dans la fusion !")

# Vérifier s'il y a des doublons
normalized_refs = [normalize_reference_format(ref) for ref in test_refs]
unique_normalized = set(normalized_refs)

if len(normalized_refs) != len(unique_normalized):
    print("❌ PROBLÈME DÉTECTÉ: Plusieurs références donnent la même forme normalisée!")
    from collections import Counter
    counts = Counter(normalized_refs)
    for norm_ref, count in counts.items():
        if count > 1:
            print(f"   '{norm_ref}' correspond à {count} références différentes")
else:
    print("✅ Pas de collision dans la normalisation des références")
