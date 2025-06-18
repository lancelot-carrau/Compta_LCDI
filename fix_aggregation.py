#!/usr/bin/env python3
"""
Script pour corriger l'agrégation des transactions et inclure Payment Method Name
"""

import re

def fix_transaction_aggregation():
    """Corrige l'agrégation des transactions pour inclure Payment Method Name"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les agrégations à corriger
    old_pattern = r"df_transactions_aggregated = df_transactions\.groupby\('Order'\)\.agg\(\{\s*'Presentment Amount': 'sum',\s*'Fee': 'sum',\s*'Net': 'sum'\s*\}\)\.reset_index\(\)"
    
    new_replacement = """df_transactions_aggregated = df_transactions.groupby('Order').agg({
            'Presentment Amount': 'sum',
            'Fee': 'sum',
            'Net': 'sum',
            'Payment Method Name': 'first'  # Garder la méthode de paiement
        }).reset_index()"""
    
    # Remplacer toutes les occurrences
    content_fixed = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Vérifier combien de remplacements ont été faits
    original_count = len(re.findall(old_pattern, content, flags=re.MULTILINE | re.DOTALL))
    new_count = len(re.findall(r"'Payment Method Name': 'first'", content_fixed))
    
    # Écrire le fichier corrigé
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content_fixed)
    
    print(f"Corrections appliquées: {original_count} occurrences trouvées")
    print(f"Payment Method Name ajouté: {new_count} fois")

if __name__ == "__main__":
    fix_transaction_aggregation()
