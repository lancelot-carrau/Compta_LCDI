#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os

def diagnostic_sersoub_dylan():
    """Diagnostic détaillé des commandes de Sersoub Dylan"""
    
    print("=== DIAGNOSTIC SERSOUB DYLAN ===")
    
    # Chemins des fichiers
    orders_file = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    transactions_file = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    try:
        # Charger les fichiers
        print("Chargement des fichiers...")
        orders_df = pd.read_csv(orders_file, encoding='utf-8', dtype=str)
        
        # Essayer différents encodages pour le journal
        try:
            journal_df = pd.read_csv(journal_file, encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            try:
                journal_df = pd.read_csv(journal_file, encoding='latin-1', dtype=str)
                print("Journal chargé avec encoding latin-1")
            except:
                journal_df = pd.read_csv(journal_file, encoding='cp1252', dtype=str)
                print("Journal chargé avec encoding cp1252")
        
        transactions_df = pd.read_csv(transactions_file, encoding='utf-8', dtype=str)
        
        print(f"- Commandes: {len(orders_df)} lignes")
        print(f"- Journal: {len(journal_df)} lignes")
        print(f"- Transactions: {len(transactions_df)} lignes")
        
        # Rechercher les commandes de Sersoub Dylan
        print("\n=== COMMANDES DE SERSOUB DYLAN ===")
        sersoub_orders = orders_df[
            (orders_df['Billing First Name'].str.contains('Sersoub', case=False, na=False)) |
            (orders_df['Billing Last Name'].str.contains('Dylan', case=False, na=False)) |
            (orders_df['Billing Name'].str.contains('Sersoub Dylan', case=False, na=False))
        ]
        
        if len(sersoub_orders) == 0:
            # Recherche plus large
            print("Recherche plus large...")
            sersoub_orders = orders_df[
                orders_df.apply(lambda row: any('sersoub' in str(val).lower() or 'dylan' in str(val).lower() 
                                               for val in row.values if pd.notna(val)), axis=1)
            ]
        
        print(f"Trouvé {len(sersoub_orders)} commandes")
        
        if len(sersoub_orders) > 0:
            # Afficher les détails des commandes
            for idx, row in sersoub_orders.iterrows():
                print(f"\n--- Commande {idx} ---")
                print(f"Name: {row.get('Name', 'N/A')}")
                print(f"Billing Name: {row.get('Billing Name', 'N/A')}")
                print(f"Total: {row.get('Total', 'N/A')}")
                print(f"Subtotal: {row.get('Subtotal', 'N/A')}")
                print(f"Shipping: {row.get('Shipping', 'N/A')}")
                print(f"Taxes: {row.get('Taxes', 'N/A')}")
                
                order_name = row.get('Name', '')
                print(f"Référence commande: {order_name}")
                
                # Chercher dans le journal
                print("\n--- Recherche dans le journal ---")
                print(f"Colonnes du journal: {list(journal_df.columns)}")
                
                # Recherche par référence
                journal_matches = []
                for col in journal_df.columns:
                    if 'ref' in col.lower() or 'référence' in col.lower():
                        matches = journal_df[journal_df[col].str.contains(order_name, case=False, na=False)]
                        if len(matches) > 0:
                            journal_matches.extend(matches.to_dict('records'))
                
                if journal_matches:
                    print(f"Trouvé {len(journal_matches)} correspondances dans le journal:")
                    for match in journal_matches:
                        print(f"  - {match}")
                else:
                    print("Aucune correspondance trouvée dans le journal")
                    
                    # Recherche plus large dans le journal
                    print("Recherche plus large dans le journal...")
                    for col in journal_df.columns:
                        if any(term in col.lower() for term in ['libellé', 'description', 'ref']):
                            partial_matches = journal_df[
                                journal_df[col].str.contains(order_name.split('#')[-1] if '#' in order_name else order_name, 
                                                            case=False, na=False)
                            ]
                            if len(partial_matches) > 0:
                                print(f"  Correspondances partielles dans {col}: {len(partial_matches)}")
                                for _, match in partial_matches.head(3).iterrows():
                                    print(f"    - {match[col]}")
                
                # Chercher dans les transactions
                print("\n--- Recherche dans les transactions ---")
                transaction_matches = transactions_df[
                    transactions_df['Order'].str.contains(order_name, case=False, na=False)
                ]
                
                if len(transaction_matches) > 0:
                    print(f"Trouvé {len(transaction_matches)} transactions:")
                    for _, trans in transaction_matches.iterrows():
                        print(f"  - Order: {trans.get('Order', 'N/A')}")
                        print(f"  - Amount: {trans.get('Amount', 'N/A')}")
                        print(f"  - Gateway: {trans.get('Gateway', 'N/A')}")
                else:
                    print("Aucune transaction trouvée")
                
                print("-" * 50)
        else:
            print("Aucune commande trouvée pour Sersoub Dylan")
        
        # Afficher quelques exemples du journal pour comprendre le format
        print("\n=== ÉCHANTILLON DU JOURNAL ===")
        print("Colonnes du journal:")
        for i, col in enumerate(journal_df.columns):
            print(f"{i}: {col}")
        
        print(f"\nPremières lignes du journal:")
        print(journal_df.head(3).to_string())
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_sersoub_dylan()
