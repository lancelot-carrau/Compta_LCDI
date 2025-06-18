#!/usr/bin/env python3
"""
Script pour corriger les appels de categorize_payment_method dans app.py
Ce script corrige les 3 occurrences pour passer les deux paramètres de méthodes de paiement
"""

import re

def fix_payment_method_calls():
    """Corrige les appels de categorize_payment_method dans app.py"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les appels à corriger
    old_pattern = r"lambda row: categorize_payment_method\(\s*row\['Payment Method'\],\s*"
    new_replacement = """lambda row: categorize_payment_method(
                row.get('Payment Method'),  # Méthode de paiement des commandes
                row.get('Payment Method Name'),  # Méthode de paiement des transactions (plus précise pour PayPal),
                """
    
    # Remplacer toutes les occurrences
    content_fixed = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE)
    
    # Écrire le fichier corrigé
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content_fixed)
    
    print("Corrections appliquées avec succès!")

if __name__ == "__main__":
    fix_payment_method_calls()
