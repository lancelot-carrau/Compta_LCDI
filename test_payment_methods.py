#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de la fonction categorize_payment_method améliorée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import categorize_payment_method

def test_payment_categorization():
    """Test de la catégorisation des méthodes de paiement"""
    print("=== TEST CATÉGORISATION MÉTHODES DE PAIEMENT ===\n")
    
    # Test cases basés sur les vraies données
    test_cases = [
        ("Shopify Payments", 100.0, "PayPal"),
        ("Alma - Pay in 4 installments", 200.0, "ALMA"),
        ("Alma - Pay in 10 installments", 300.0, "ALMA"),
        ("custom", 150.0, "Virement bancaire"),
        ("Younited Pay", 250.0, "Younited"),
        ("PayPal", 75.0, "PayPal"),
        ("Virement bancaire", 180.0, "Virement bancaire"),
        ("Unknown Method", 50.0, "PayPal"),  # Fallback
        (None, 100.0, None),  # NaN handling
        ("Shopify Payments", None, None),  # NaN handling
    ]
    
    for payment_method, amount, expected_category in test_cases:
        result = categorize_payment_method(payment_method, amount)
        
        if expected_category is None:
            # Vérifier que tous les montants sont 0
            total = sum(result.values())
            status = "✓" if total == 0 else "✗"
            print(f"{status} {payment_method} + {amount} -> Tous à 0 (NaN)")
        else:
            # Vérifier que la bonne catégorie a le bon montant
            actual_amount = result[expected_category]
            status = "✓" if actual_amount == amount else "✗"
            print(f"{status} '{payment_method}' + {amount} -> {expected_category}: {actual_amount}")
    
    print("\n=== TEST AVEC DONNÉES RÉELLES ===")
    
    # Lire les données réelles pour tester
    import pandas as pd
    
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    df_orders = pd.read_csv(orders_file, encoding='utf-8')
    df_transactions = pd.read_csv(transactions_file, encoding='utf-8')
    
    # Fusion simplifiée pour test
    df_test = pd.merge(df_orders, df_transactions, left_on='Name', right_on='Order', how='left')
    
    print(f"Données de test: {len(df_test)} lignes")
    
    # Compter les méthodes par catégorie
    categories = {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    total_amounts = {'Virement bancaire': 0, 'ALMA': 0, 'Younited': 0, 'PayPal': 0}
    
    for idx, row in df_test.iterrows():
        payment_method = row.get('Payment Method')
        amount = row.get('Presentment Amount', 0)
        
        if pd.notna(payment_method) and pd.notna(amount) and amount > 0:
            result = categorize_payment_method(payment_method, amount)
            
            for category, value in result.items():
                if value > 0:
                    categories[category] += 1
                    total_amounts[category] += value
    
    print("\nRésultats avec données réelles:")
    for category in categories:
        count = categories[category]
        total = total_amounts[category]
        print(f"  {category}: {count} transactions, {total:.2f}€")
    
    total_transactions = sum(categories.values())
    total_amount = sum(total_amounts.values())
    print(f"\nTotal: {total_transactions} transactions, {total_amount:.2f}€")

if __name__ == "__main__":
    test_payment_categorization()
