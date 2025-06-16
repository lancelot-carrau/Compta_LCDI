#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la fonction de normalisation des références
"""

from app import normalize_reference_format

def test_normalize_function():
    """Test de la fonction normalize_reference_format"""
    
    print("=== TEST DE LA FONCTION DE NORMALISATION ===")
    
    test_cases = [
        ('#1001', '#1001'),
        ('ORDER-1003', '#1003'),
        ('1004', '#1004'),
        ('#1005', '#1005'),
        ('CMD-2024-0567', '#2024'),
        ('REF_890', '#890'),
        ('SHOPIFY-123', '#123'),
        ('', ''),
        (None, None),
        ('ABC-XYZ', 'ABC-XYZ')  # Pas de chiffres
    ]
    
    for input_ref, expected in test_cases:
        result = normalize_reference_format(input_ref)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_ref}' -> '{result}' (attendu: '{expected}')")
    
    print("\n=== TEST AVEC DONNÉES RÉELLES ===")
    
    # Test avec les données de notre diagnostic
    commandes = ['#1001', '#1002', 'ORDER-1003', '1004', '#1005']
    journal = ['#1001', '#1002', '#1003', 'ORDER-1004', '#1005']
    
    print("Références commandes normalisées:")
    for ref in commandes:
        normalized = normalize_reference_format(ref)
        print(f"  {ref} -> {normalized}")
    
    print("\nRéférences journal normalisées:")
    for ref in journal:
        normalized = normalize_reference_format(ref)
        print(f"  {ref} -> {normalized}")
    
    # Vérifier les correspondances après normalisation
    commandes_norm = [normalize_reference_format(ref) for ref in commandes]
    journal_norm = [normalize_reference_format(ref) for ref in journal]
    
    print(f"\nCorrespondances avant normalisation: {len(set(commandes) & set(journal))}/5")
    print(f"Correspondances après normalisation: {len(set(commandes_norm) & set(journal_norm))}/5")
    
    print("\nCorrespondances détaillées après normalisation:")
    for i, cmd_norm in enumerate(commandes_norm):
        if cmd_norm in journal_norm:
            j_idx = journal_norm.index(cmd_norm)
            print(f"  ✅ {commandes[i]} ({cmd_norm}) = {journal[j_idx]} ({journal_norm[j_idx]})")
        else:
            print(f"  ❌ {commandes[i]} ({cmd_norm}) - pas de correspondance")

if __name__ == "__main__":
    test_normalize_function()
