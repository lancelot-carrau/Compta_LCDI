#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app import fill_missing_data_indicators

def test_statut_logic_corrected():
    """Test de la logique de statut corrigée pour LCDI-1020"""
    
    print("=== TEST DE LA LOGIQUE DE STATUT CORRIGÉE ===")
    
    # Créer un DataFrame de test avec les données de LCDI-1020
    test_data = {
        'Centre de profit': ['lcdi.fr', 'lcdi.fr'],
        'Réf.WEB': ['#LCDI-1020', '#LCDI-1021'],
        'Réf. LMB': ['FAC-L-04321', 'FAC-L-04321'],
        'Date Facture': ['30/05/2025', '30/05/2025'],
        'Etat': ['payée', 'payée'],
        'Client': ['Dylan Sersoub', 'Dylan Sersoub'],
        'HT': [1723.25, 13.25],
        'TVA': [344.65, 2.65],
        'TTC': [2067.9, 15.9],
        'reste': [0, 0],
        'Shopify': [0, 15.48],
        'Frais de commission': [0, 0.42],
        'Virement bancaire': [0, 0],
        'ALMA': [2067.9, 0],
        'Younited': [0, 0],
        'PayPal': [0, 15.9]
    }
    
    df_final = pd.DataFrame(test_data)
    
    # DataFrame merged simulé (pour la compatibilité avec la fonction)
    df_merged_final = pd.DataFrame({
        'Presentment Amount': [0, 15.9]  # LCDI-1020 n'a pas de Presentment Amount, LCDI-1021 en a
    })
    
    print("Données de test:")
    print(df_final.to_string())
    
    # Tester la logique de statut
    print("\n=== TEST DE LA LOGIQUE DE STATUT ===")
    
    # Appliquer la fonction
    df_result = fill_missing_data_indicators(df_final, df_merged_final)
    
    print("\nRésultats:")
    for idx, row in df_result.iterrows():
        print(f"\n--- {row['Réf.WEB']} ---")
        print(f"Réf. LMB: '{row['Réf. LMB']}'")
        print(f"Date Facture: '{row['Date Facture']}'")
        print(f"Paiements:")
        print(f"  - Shopify: {row['Shopify']}")
        print(f"  - ALMA: {row['ALMA']}")
        print(f"  - PayPal: {row['PayPal']}")
        print(f"STATUT: {row['Statut']}")
        
        if row['Réf.WEB'] == '#LCDI-1020' and row['Statut'] == 'COMPLET':
            print("✅ SUCCÈS: LCDI-1020 est maintenant COMPLET!")
        elif row['Réf.WEB'] == '#LCDI-1020' and row['Statut'] == 'INCOMPLET':
            print("❌ PROBLÈME: LCDI-1020 est toujours INCOMPLET")

if __name__ == "__main__":
    test_statut_logic_corrected()
