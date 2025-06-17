#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification du fichier final généré après correction.
Vérifie spécifiquement les commandes LCDI-1020 et LCDI-1021.
"""

import pandas as pd
import os
from glob import glob

def verifier_fichier_final():
    """Vérifie le dernier fichier généré"""
    print("=== VÉRIFICATION DU FICHIER FINAL ===\n")
    
    # Trouver le dernier fichier généré
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("❌ Dossier output non trouvé!")
        return
    
    # Chercher les fichiers .xlsx les plus récents
    xlsx_files = glob(os.path.join(output_dir, "tableau_facturation_final_*.xlsx"))
    if not xlsx_files:
        print("❌ Aucun fichier Excel trouvé dans output/")
        return
    
    # Prendre le plus récent
    latest_file = max(xlsx_files, key=os.path.getctime)
    print(f"Fichier analysé: {latest_file}")
    
    # Lire le fichier
    try:
        df = pd.read_excel(latest_file)
        print(f"Nombre total de lignes: {len(df)}")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return
    
    # Rechercher les lignes LCDI-1020 et LCDI-1021
    print("\n=== RECHERCHE DES LIGNES 1020/1021 ===")
    
    mask_1020 = df['Réf.WEB'].str.contains('1020', na=False)
    mask_1021 = df['Réf.WEB'].str.contains('1021', na=False)
    
    lines_1020 = df[mask_1020]
    lines_1021 = df[mask_1021]
    
    print(f"Lignes LCDI-1020: {len(lines_1020)}")
    print(f"Lignes LCDI-1021: {len(lines_1021)}")
    
    if len(lines_1020) == 0 and len(lines_1021) == 0:
        print("❌ Aucune ligne 1020/1021 trouvée!")
        return
    
    # Analyser chaque ligne
    print("\n=== ANALYSE DÉTAILLÉE ===")
    
    for idx, row in lines_1020.iterrows():
        print(f"LCDI-1020 (ligne {idx+2}):")
        print(f"  - Réf. LMB: '{row['Réf. LMB']}'")
        print(f"  - TTC: {row['TTC']} €")
        print(f"  - HT: {row['HT']} €")
        print(f"  - TVA: {row['TVA']} €")
        print(f"  - Client: {row['Client']}")
        print()
    
    for idx, row in lines_1021.iterrows():
        print(f"LCDI-1021 (ligne {idx+2}):")
        print(f"  - Réf. LMB: '{row['Réf. LMB']}'")
        print(f"  - TTC: {row['TTC']} €")
        print(f"  - HT: {row['HT']} €")
        print(f"  - TVA: {row['TVA']} €")
        print(f"  - Client: {row['Client']}")
        print()
    
    # Vérifications
    print("=== VÉRIFICATIONS ===")
    
    all_lines = pd.concat([lines_1020, lines_1021])
    
    # Test 1: Présence des Réf. LMB
    ref_lmb_present = all_lines['Réf. LMB'].notna() & (all_lines['Réf. LMB'] != '')
    print(f"✓ Lignes avec Réf. LMB: {ref_lmb_present.sum()}/{len(all_lines)}")
    
    # Test 2: Montants corrects (vérification de la non-duplication)
    if len(all_lines) >= 2:
        ttc_values = all_lines['TTC'].tolist()
        print(f"✓ Montants TTC: {ttc_values}")
        
        # Les montants doivent être différents (pas de duplication)
        if len(set(ttc_values)) == len(ttc_values):
            print("✓ Pas de duplication des montants")
        else:
            print("❌ Duplication détectée!")
        
        # Vérifier les montants attendus approximatifs
        # (les montants exacts peuvent varier selon les données réelles)
        total_ttc = sum(ttc_values)
        print(f"✓ Somme TTC: {total_ttc} €")
    
    # Test 3: Réf. LMB identiques (si présentes)
    ref_lmb_unique = all_lines['Réf. LMB'].dropna().unique()
    if len(ref_lmb_unique) == 1:
        print(f"✓ Réf. LMB partagée: {ref_lmb_unique[0]}")
    elif len(ref_lmb_unique) > 1:
        print(f"❌ Réf. LMB différentes: {ref_lmb_unique}")
    else:
        print("⚠️ Aucune Réf. LMB trouvée")
    
    # Statistiques générales
    print("\n=== STATISTIQUES GÉNÉRALES ===")
    ref_lmb_total = df['Réf. LMB'].notna().sum()
    print(f"Réf. LMB remplies: {ref_lmb_total}/{len(df)} ({ref_lmb_total/len(df)*100:.1f}%)")
    
    total_ttc_global = df['TTC'].sum()
    print(f"Somme TTC totale: {total_ttc_global}€")

if __name__ == "__main__":
    verifier_fichier_final()
