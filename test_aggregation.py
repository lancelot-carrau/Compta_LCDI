#!/usr/bin/env python3
"""
Test spécifique pour l'agrégation des commandes multiples
"""
import pandas as pd

def test_orders_aggregation():
    print("=== TEST AGRÉGATION DES COMMANDES MULTIPLES ===")
    
    # Simuler des données avec doublons (plusieurs produits par commande)
    orders_data = {
        'Name': ['#1001', '#1001', '#1002', '#1003', '#1003'],
        'Fulfilled at': ['2024-01-15', '2024-01-15', '2024-01-16', '2024-01-17', '2024-01-17'],
        'Billing name': ['Client A', 'Client A', 'Client B', 'Client C', 'Client C'],
        'Financial Status': ['paid', 'paid', 'pending', 'paid', 'paid'],
        'Tax 1 Value': [10.00, 15.00, 20.00, 12.00, 18.00],  # À sommer
        'Outstanding Balance': [0.00, 0.00, 50.00, 0.00, 0.00],  # À sommer
        'Payment Method': ['PayPal', 'PayPal', 'Virement', 'ALMA', 'ALMA'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C', 'Produit D', 'Produit E']
    }
    
    df = pd.DataFrame(orders_data)
    print(f"Données avant agrégation: {len(df)} lignes")
    print(df[['Name', 'Tax 1 Value', 'Outstanding Balance']].to_string())
    
    # Simuler l'agrégation
    first_value_cols = ['Fulfilled at', 'Billing name', 'Financial Status', 'Payment Method']
    sum_cols = ['Tax 1 Value', 'Outstanding Balance']
    
    agg_operations = {}
    for col in first_value_cols:
        if col in df.columns:
            agg_operations[col] = 'first'
    
    for col in sum_cols:
        if col in df.columns:
            agg_operations[col] = 'sum'
    
    df_aggregated = df.groupby('Name').agg(agg_operations).reset_index()
    
    print(f"\nDonnées après agrégation: {len(df_aggregated)} lignes")
    print(df_aggregated[['Name', 'Tax 1 Value', 'Outstanding Balance']].to_string())
    
    # Vérifications
    expected_results = {
        '#1001': {'Tax 1 Value': 25.00, 'Outstanding Balance': 0.00},
        '#1002': {'Tax 1 Value': 20.00, 'Outstanding Balance': 50.00},
        '#1003': {'Tax 1 Value': 30.00, 'Outstanding Balance': 0.00}
    }
    
    print("\n=== VÉRIFICATIONS ===")
    success = True
    for name, expected in expected_results.items():
        row = df_aggregated[df_aggregated['Name'] == name]
        if len(row) == 1:
            actual_tax = row['Tax 1 Value'].iloc[0]
            actual_balance = row['Outstanding Balance'].iloc[0]
            
            if actual_tax == expected['Tax 1 Value'] and actual_balance == expected['Outstanding Balance']:
                print(f"✓ {name}: TVA={actual_tax}, Balance={actual_balance}")
            else:
                print(f"❌ {name}: attendu TVA={expected['Tax 1 Value']}, Balance={expected['Outstanding Balance']}, obtenu TVA={actual_tax}, Balance={actual_balance}")
                success = False
        else:
            print(f"❌ {name}: nombre de lignes incorrect ({len(row)})")
            success = False
    
    return success

if __name__ == "__main__":
    success = test_orders_aggregation()
    if success:
        print("\n🎉 Test d'agrégation réussi!")
    else:
        print("\n❌ Test d'agrégation échoué.")
