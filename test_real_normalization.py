#!/usr/bin/env python3
"""
Test de la nouvelle normalisation avec les vrais formats de références
"""

import sys
import os
sys.path.append('.')
from app import normalize_reference_format, normalize_reference_with_multiples

def test_real_formats():
    """Test avec les vrais formats trouvés dans les fichiers"""
    
    print("=== TEST DE NORMALISATION AVEC VRAIS FORMATS ===\n")
    
    # Formats trouvés dans le journal
    journal_refs = [
        "LCDI-1038",
        "LCDI-1026", 
        "#LCDI-1016",
        "#lcdi-1018",
        "LCDI-1020 LCDI-1021",  # Références multiples
        "LCDI-1019",
        "#LCDI-1010"
    ]
    
    # Formats trouvés dans les commandes
    order_refs = [
        "#LCDI-1042",
        "#LCDI-1041", 
        "#LCDI-1038",
        "#LCDI-1037",
        "#LCDI-1036"
    ]
    
    print("1. NORMALISATION SIMPLE :")
    print("Journal :")
    for ref in journal_refs:
        normalized = normalize_reference_format(ref)
        print(f"  {ref:<20} -> {normalized}")
    
    print("\nCommandes :")
    for ref in order_refs:
        normalized = normalize_reference_format(ref)
        print(f"  {ref:<20} -> {normalized}")
    
    print("\n2. NORMALISATION AVEC RÉFÉRENCES MULTIPLES :")
    for ref in journal_refs:
        normalized = normalize_reference_with_multiples(ref)
        print(f"  {ref:<20} -> {normalized}")
    
    print("\n3. TEST DE CORRESPONDANCES :")
    # Simuler les correspondances possibles
    journal_normalized = []
    for ref in journal_refs:
        refs = normalize_reference_with_multiples(ref)
        journal_normalized.extend(refs)
    
    order_normalized = [normalize_reference_format(ref) for ref in order_refs]
    
    print(f"Journal normalisé ({len(journal_normalized)} refs) : {journal_normalized}")
    print(f"Commandes normalisées ({len(order_normalized)} refs) : {order_normalized}")
    
    # Compter les correspondances
    matches = []
    for order_ref in order_normalized:
        if order_ref in journal_normalized:
            matches.append(order_ref)
    
    print(f"Correspondances trouvées ({len(matches)}) : {matches}")
    print(f"Taux de correspondance : {len(matches)}/{len(order_normalized)} ({len(matches)/len(order_normalized)*100:.1f}%)")

if __name__ == "__main__":
    test_real_formats()
