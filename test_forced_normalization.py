#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test avec normalisation forcée des références LMB
"""

import pandas as pd
from app import normalize_reference_format, improve_journal_matching

def test_forced_normalization():
    """Test avec normalisation forcée"""
    
    print("=== TEST AVEC NORMALISATION FORCÉE ===")
    
    # Données de test avec formats de références différents
    orders_data = {
        'Name': ['#1001', '#1002', 'ORDER-1003', '1004', '#1005'],
        'Fulfilled at': ['2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25', '2024-01-30'],
        'Billing name': ['Client A', 'Client B', 'Client C', 'Client D', 'Client A'],
        'Financial Status': ['paid', 'paid', 'paid', 'paid', 'paid'],
        'Tax 1 Value': [10.0, 20.0, 15.0, 12.0, 8.0],
        'Outstanding Balance': [0.0, 0.0, 0.0, 0.0, 0.0],
        'Payment Method': ['PayPal', 'Virement', 'Carte', 'PayPal', 'Virement'],
        'Total': [110.0, 220.0, 165.0, 132.0, 88.0],
        'Email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'a@test.com'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C', 'Produit D', 'Produit E'],
        'Lineitem price': [100.0, 200.0, 150.0, 120.0, 80.0]
    }
    
    transactions_data = {
        'Order': ['#1001', '#1002', 'ORDER-1003', '1004', '#1005'],
        'Presentment Amount': [110.0, 220.0, 165.0, 132.0, 88.0],
        'Fee': [3.30, 6.60, 4.95, 3.96, 2.64],
        'Net': [106.70, 213.40, 160.05, 128.04, 85.36]
    }
    
    journal_data = {
        'Piece': ['#1001', '#1002', '#1003', 'ORDER-1004', '#1005'],
        'Référence LMB': ['LMB001', 'LMB002', 'LMB003', 'LMB004', 'LMB005']
    }
    
    df_orders = pd.DataFrame(orders_data)
    df_transactions = pd.DataFrame(transactions_data)
    df_journal = pd.DataFrame(journal_data)
    
    # Simuler les étapes avant fusion
    df_merged_step1 = pd.merge(df_orders, df_transactions, 
                              left_on='Name', right_on='Order', how='left')
    
    print("AVANT NORMALISATION:")
    correspondances_avant = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
    print(f"  Correspondances: {correspondances_avant}/{len(df_merged_step1)}")
    
    # Appliquer la normalisation
    print("\nAPPLICATION DE LA NORMALISATION:")
    df_result = improve_journal_matching(df_merged_step1, df_journal)
    
    # Vérifier les résultats
    print("\nRÉSULTAT:")
    if 'Référence LMB' in df_result.columns:
        ref_lmb_non_nulles = df_result['Référence LMB'].notna().sum()
        print(f"  Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_result)} ({ref_lmb_non_nulles/len(df_result)*100:.1f}%)")
        
        print("\nDÉTAIL DES RÉFÉRENCES:")
        for i, row in df_result.iterrows():
            ref_web = row['Name']
            ref_lmb = row.get('Référence LMB', 'VIDE')
            status = "✅" if pd.notna(ref_lmb) and ref_lmb != '' else "❌"
            print(f"    {status} {ref_web} -> {ref_lmb}")
    else:
        print("  ❌ Colonne 'Référence LMB' non trouvée!")
        print(f"  Colonnes disponibles: {list(df_result.columns)}")

if __name__ == "__main__":
    test_forced_normalization()
