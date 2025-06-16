#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier qu'un même client peut avoir plusieurs commandes distinctes
Chaque commande doit apparaître sur une ligne séparée dans le tableau final
"""

import pandas as pd
from app import process_dataframes_directly
import os

def test_client_with_multiple_orders():
    """Test qu'un même client avec plusieurs commandes distinctes apparaît sur plusieurs lignes"""
    
    print("=== TEST: CLIENT AVEC PLUSIEURS COMMANDES DISTINCTES ===")
    
    # Créer des données de test avec le même client ayant 3 commandes différentes
    orders_data = {
        'Name': ['#1001', '#1002', '#1003'],  # 3 commandes distinctes
        'Fulfilled at': ['2024-01-10', '2024-01-15', '2024-01-20'],
        'Billing name': ['Dupont Jean', 'Dupont Jean', 'Dupont Jean'],  # Même client
        'Financial Status': ['paid', 'paid', 'paid'],
        'Tax 1 Value': [10.0, 20.0, 15.0],  # Montants différents
        'Outstanding Balance': [0.0, 0.0, 0.0],
        'Payment Method': ['PayPal', 'Virement', 'Carte'],  # Méthodes différentes
        'Total': [110.0, 220.0, 165.0],
        'Email': ['jean.dupont@email.com', 'jean.dupont@email.com', 'jean.dupont@email.com'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C'],
        'Lineitem price': [100.0, 200.0, 150.0]
    }
    
    transactions_data = {
        'Order': ['#1001', '#1002', '#1003'],
        'Presentment Amount': [110.0, 220.0, 165.0],
        'Fee': [3.30, 6.60, 4.95],
        'Net': [106.70, 213.40, 160.05]
    }
    
    journal_data = {
        'Piece': ['#1001', '#1002', '#1003'],
        'Référence LMB': ['LMB001', 'LMB002', 'LMB003']
    }
    
    # Créer les DataFrames
    df_orders = pd.DataFrame(orders_data)
    df_transactions = pd.DataFrame(transactions_data)
    df_journal = pd.DataFrame(journal_data)
    
    print("Données initiales:")
    print(f"- Commandes: {len(df_orders)} lignes")
    print(f"- Client unique: {df_orders['Billing name'].nunique()} ('{df_orders['Billing name'].iloc[0]}')")
    print(f"- Commandes distinctes: {df_orders['Name'].nunique()} ({list(df_orders['Name'])})")
      # Traiter les données
    result_df = process_dataframes_directly(df_orders, df_transactions, df_journal)
    
    print(f"\nRésultat final:")
    print(f"- Nombre de lignes dans le tableau final: {len(result_df)}")
    print(f"- Clients uniques: {result_df['Nom'].nunique()}")
    print(f"- Commandes dans le résultat: {list(result_df['Référence'])}")
    
    # Vérifications
    assert len(result_df) == 3, f"Attendu 3 lignes, obtenu {len(result_df)}"
    assert result_df['Nom'].nunique() == 1, f"Attendu 1 client unique, obtenu {result_df['Nom'].nunique()}"
    assert len(result_df['Référence'].unique()) == 3, f"Attendu 3 commandes distinctes, obtenu {len(result_df['Référence'].unique())}"
    
    # Vérifier que chaque commande est bien présente
    expected_orders = {'#1001', '#1002', '#1003'}
    actual_orders = set(result_df['Référence'])
    assert actual_orders == expected_orders, f"Commandes attendues {expected_orders}, obtenues {actual_orders}"
    
    # Vérifier que les montants sont corrects pour chaque commande
    for _, row in result_df.iterrows():
        ref = row['Référence']
        if ref == '#1001':
            assert row['TTC'] == 110.0, f"Montant TTC incorrect pour {ref}: {row['TTC']}"
        elif ref == '#1002':
            assert row['TTC'] == 220.0, f"Montant TTC incorrect pour {ref}: {row['TTC']}"
        elif ref == '#1003':
            assert row['TTC'] == 165.0, f"Montant TTC incorrect pour {ref}: {row['TTC']}"
    
    print("\n✅ SUCCÈS: Le même client avec plusieurs commandes distinctes")
    print("   apparaît correctement sur plusieurs lignes séparées!")
    print(f"   - Client: {result_df['Nom'].iloc[0]}")
    print(f"   - Commandes: {', '.join(result_df['Référence'])}")
    print(f"   - Montants TTC: {', '.join(f'{x:.2f}€' for x in result_df['TTC'])}")
    
    return True

def test_mixed_scenario():
    """Test avec plusieurs clients, dont un avec plusieurs commandes"""
    
    print("\n=== TEST: SCÉNARIO MIXTE ===")
    
    # Client A: 1 commande, Client B: 2 commandes, Client C: 1 commande
    orders_data = {
        'Name': ['#1001', '#1002', '#1003', '#1004'],
        'Fulfilled at': ['2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25'],
        'Billing name': ['Client A', 'Client B', 'Client B', 'Client C'],  # Client B a 2 commandes
        'Financial Status': ['paid', 'paid', 'paid', 'paid'],
        'Tax 1 Value': [10.0, 20.0, 15.0, 12.0],
        'Outstanding Balance': [0.0, 0.0, 0.0, 0.0],
        'Payment Method': ['PayPal', 'Virement', 'Carte', 'PayPal'],
        'Total': [110.0, 220.0, 165.0, 132.0],
        'Email': ['a@test.com', 'b@test.com', 'b@test.com', 'c@test.com'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C', 'Produit D'],
        'Lineitem price': [100.0, 200.0, 150.0, 120.0]
    }
    
    transactions_data = {
        'Order': ['#1001', '#1002', '#1003', '#1004'],
        'Presentment Amount': [110.0, 220.0, 165.0, 132.0],
        'Fee': [3.30, 6.60, 4.95, 3.96],
        'Net': [106.70, 213.40, 160.05, 128.04]
    }
    
    journal_data = {
        'Piece': ['#1001', '#1002', '#1003', '#1004'],
        'Référence LMB': ['LMB001', 'LMB002', 'LMB003', 'LMB004']
    }
    
    df_orders = pd.DataFrame(orders_data)
    df_transactions = pd.DataFrame(transactions_data)
    df_journal = pd.DataFrame(journal_data)
    
    print("Données initiales:")
    print(f"- Commandes: {len(df_orders)} lignes")
    print(f"- Clients distincts: {df_orders['Billing name'].nunique()}")
    print("- Répartition par client:")
    client_counts = df_orders['Billing name'].value_counts()
    for client, count in client_counts.items():
        print(f"  * {client}: {count} commande(s)")
    
    result_df = process_dataframes_directly(df_orders, df_transactions, df_journal)
    
    print(f"\nRésultat final:")
    print(f"- Nombre de lignes: {len(result_df)} (doit être 4)")
    print(f"- Clients distincts: {result_df['Nom'].nunique()} (doit être 3)")
    
    # Vérifications
    assert len(result_df) == 4, f"Attendu 4 lignes, obtenu {len(result_df)}"
    assert result_df['Nom'].nunique() == 3, f"Attendu 3 clients distincts, obtenu {result_df['Nom'].nunique()}"
    
    # Vérifier que Client B a bien 2 lignes
    client_b_orders = result_df[result_df['Nom'] == 'Client B']
    assert len(client_b_orders) == 2, f"Client B doit avoir 2 lignes, obtenu {len(client_b_orders)}"
    
    print("✅ SUCCÈS: Scénario mixte validé!")
    
    return True

if __name__ == "__main__":
    try:
        test_client_with_multiple_orders()
        test_mixed_scenario()
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ La logique est correcte: un même client peut avoir plusieurs commandes sur des lignes séparées")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
