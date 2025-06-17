#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def verify_lcdi_1020_status():
    """Vérifier le statut de LCDI-1020 dans le fichier généré"""
    
    print("=== VÉRIFICATION DU STATUT LCDI-1020 ===")
    
    # Lire le fichier généré le plus récent
    file_path = "output/tableau_references_multiples_20250617_154659.xlsx"
    
    try:
        df = pd.read_excel(file_path)
        print(f"Fichier chargé: {len(df)} lignes")
        
        # Trouver LCDI-1020
        lcdi_1020 = df[df['Réf.WEB'] == '#LCDI-1020']
        
        if len(lcdi_1020) > 0:
            row = lcdi_1020.iloc[0]
            print(f"\n--- LCDI-1020 ---")
            print(f"Réf. LMB: {row['Réf. LMB']}")
            print(f"Date Facture: {row['Date Facture']}")
            print(f"HT: {row['HT']}")
            print(f"TVA: {row['TVA']}")
            print(f"TTC: {row['TTC']}")
            print(f"ALMA: {row['ALMA']}")
            print(f"Statut: {row['Statut']}")
            
            if row['Statut'] == 'COMPLET':
                print("✅ SUCCÈS: LCDI-1020 est maintenant COMPLET dans le fichier Excel!")
            else:
                print("❌ PROBLÈME: LCDI-1020 est toujours INCOMPLET dans le fichier Excel")
                
            # Vérifier aussi LCDI-1021 pour comparaison
            lcdi_1021 = df[df['Réf.WEB'] == '#LCDI-1021']
            if len(lcdi_1021) > 0:
                row_1021 = lcdi_1021.iloc[0]
                print(f"\n--- LCDI-1021 (pour comparaison) ---")
                print(f"Statut: {row_1021['Statut']}")
                print(f"PayPal: {row_1021['PayPal']}")
                print(f"Shopify: {row_1021['Shopify']}")
        else:
            print("❌ LCDI-1020 non trouvé dans le fichier")
            
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    verify_lcdi_1020_status()
