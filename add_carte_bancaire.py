#!/usr/bin/env python3
"""
Script pour ajouter la colonne 'Carte bancaire' après 'Virement bancaire'
"""

import re

def add_carte_bancaire_column():
    """Ajoute la colonne Carte bancaire dans toutes les occurrences"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les sections de paiement à modifier
    old_pattern = r"df_final\['Virement bancaire'\] = \[pm\['Virement bancaire'\] for pm in payment_categorization\]\s*df_final\['ALMA'\] = \[pm\['ALMA'\] for pm in payment_categorization\]"
    
    new_replacement = """df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['Carte bancaire'] = [pm['Carte bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]"""
    
    # Remplacer toutes les occurrences
    content_fixed = re.sub(old_pattern, new_replacement, content, flags=re.MULTILINE)
    
    # Vérifier combien de remplacements ont été faits
    original_count = len(re.findall(old_pattern, content, flags=re.MULTILINE))
    new_count = len(re.findall(r"df_final\['Carte bancaire'\]", content_fixed))
    
    # Écrire le fichier corrigé
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content_fixed)
    
    print(f"Corrections appliquées: {original_count} occurrences trouvées")
    print(f"Colonne 'Carte bancaire' ajoutée: {new_count} fois")

if __name__ == "__main__":
    add_carte_bancaire_column()
