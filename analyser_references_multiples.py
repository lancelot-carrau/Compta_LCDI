#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def analyser_references_multiples():
    """Analyser le problème des références multiples dans le journal"""
    
    print("=== ANALYSE DES RÉFÉRENCES MULTIPLES ===")
    
    journal_file = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    try:
        # Charger le journal avec le bon séparateur
        journal_df = pd.read_csv(journal_file, encoding='latin-1', sep=';', dtype=str)
        print(f"Journal chargé: {len(journal_df)} lignes, {len(journal_df.columns)} colonnes")
        
        # Rechercher les lignes avec LCDI-1020 et LCDI-1021
        print("\n=== RECHERCHE DES RÉFÉRENCES LCDI-1020 ET LCDI-1021 ===")
        
        # Afficher toutes les lignes qui contiennent ces références
        ref_matches = journal_df[
            journal_df['Référence externe'].str.contains('LCDI-1020|LCDI-1021', case=False, na=False)
        ]
        
        print(f"Trouvé {len(ref_matches)} lignes contenant LCDI-1020 ou LCDI-1021:")
        
        for idx, row in ref_matches.iterrows():
            print(f"\n--- Ligne {idx} ---")
            print(f"Référence LMB: {row['Référence LMB']}")
            print(f"Date: {row['Date du document']}")
            print(f"Montant TTC: {row['Montant du document TTC']}")
            print(f"Montant HT: {row['Montant du document HT']}")
            print(f"Référence externe: {row['Référence externe']}")
            print(f"Nom contact: {row['Nom contact']}")
            print("Tous les champs:")
            for col, val in row.items():
                print(f"  {col}: {val}")
        
        # Analyser le problème
        print("\n=== ANALYSE DU PROBLÈME ===")
        
        if len(ref_matches) > 0:
            for _, row in ref_matches.iterrows():
                ref_externe = row['Référence externe']
                montant_ttc = row['Montant du document TTC']
                montant_ht = row['Montant du document HT']
                
                print(f"\nLigne avec référence externe: '{ref_externe}'")
                print(f"Montant TTC: {montant_ttc}")
                print(f"Montant HT: {montant_ht}")
                
                # Cette ligne contient deux références, mais un seul montant
                # Comment doit-on répartir ?
                if 'LCDI-1020' in ref_externe and 'LCDI-1021' in ref_externe:
                    print("PROBLÈME IDENTIFIÉ:")
                    print("- Cette ligne contient les références de DEUX commandes")
                    print("- Mais elle n'a qu'UN SEUL montant TTC/HT")
                    print("- Comment répartir ? Options possibles:")
                    print("  1. Attribuer le montant total à la première commande")
                    print("  2. Attribuer le montant total à la commande principale")
                    print("  3. Répartir proportionnellement")
                    print("  4. Marquer comme non répartissable")
                    
                    # Convertir les montants pour analyse
                    try:
                        ttc_val = float(montant_ttc.replace(',', '.').replace(' ', ''))
                        ht_val = float(montant_ht.replace(',', '.').replace(' ', ''))
                        
                        print(f"\nMontants numériques:")
                        print(f"  TTC: {ttc_val}€")
                        print(f"  HT: {ht_val}€")
                        print(f"  TVA calculée: {ttc_val - ht_val:.2f}€")
                        
                        # Comparer avec les commandes
                        print(f"\nCommandes correspondantes:")
                        print(f"  LCDI-1020: Total 2067.90€, Taxes 344.65€")
                        print(f"  LCDI-1021: Total 15.90€, Taxes 2.65€")
                        print(f"  Total des deux: {2067.90 + 15.90}€")
                        
                        if abs(ttc_val - (2067.90 + 15.90)) < 1:
                            print("  => Le montant journal correspond à la SOMME des deux commandes")
                        elif abs(ttc_val - 2067.90) < 1:
                            print("  => Le montant journal correspond à LCDI-1020 uniquement")
                        elif abs(ttc_val - 15.90) < 1:
                            print("  => Le montant journal correspond à LCDI-1021 uniquement")
                        else:
                            print("  => Le montant journal ne correspond à aucune commande individuellement")
                            
                    except ValueError as e:
                        print(f"Erreur de conversion numérique: {e}")
        
        else:
            print("Aucune ligne trouvée - problème de matching")
        
        # Afficher quelques autres lignes pour contexte
        print(f"\n=== ÉCHANTILLON COMPLET DU JOURNAL ===")
        print("Toutes les lignes du journal:")
        for idx, row in journal_df.iterrows():
            print(f"{idx:2d}: {row['Référence LMB']} -> {row['Référence externe']} ({row['Montant du document TTC']})")
    
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyser_references_multiples()
