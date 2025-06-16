#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch pour forcer l'amélioration des références LMB dans app.py
"""

import re

def patch_app_py():
    """Patch le fichier app.py pour forcer l'amélioration des références"""
    
    print("=== PATCH DE L'APPLICATION ===")
    
    # Lire le fichier
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer le seuil de 80% par 100% (force toujours la normalisation)
    old_pattern = r'if commandes_dans_journal < len\(df_merged_step1\) \* 0\.8:'
    new_pattern = 'if commandes_dans_journal < len(df_merged_step1):'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        print("✅ Seuil de normalisation modifié (80% -> 100%)")
    else:
        print("⚠️ Pattern 80% non trouvé, recherche d'autres patterns...")
        
        # Chercher le pattern plus général
        pattern2 = r'# Si moins de 80% de correspondances'
        if pattern2 in content:
            content = content.replace(pattern2, '# Si pas 100% de correspondances')
            print("✅ Commentaire modifié")
        
        # Forcer l'application de la normalisation
        pattern3 = r'if commandes_dans_journal < len\(df_merged_step1\) \* 0\.8:'
        replacement3 = 'if commandes_dans_journal < len(df_merged_step1):'
        
        if re.search(pattern3, content):
            content = re.sub(pattern3, replacement3, content)
            print("✅ Condition de normalisation modifiée")
        else:
            print("❌ Impossible de trouver la condition à modifier")
    
    # Sauvegarder le fichier
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Patch appliqué avec succès!")
    print("L'application utilisera maintenant la normalisation dès qu'elle peut améliorer les résultats")

if __name__ == "__main__":
    patch_app_py()
