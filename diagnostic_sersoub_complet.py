#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os

def diagnostic_sersoub_complet():
    """Diagnostic complet des commandes de Sersoub Dylan"""
    
    print("=== DIAGNOSTIC COMPLET SERSOUB DYLAN ===")
    
    # Chemins des fichiers
    orders_file = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    transactions_file = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    try:
        # Charger les fichiers
        print("Chargement des fichiers...")
        orders_df = pd.read_csv(orders_file, encoding='utf-8', dtype=str)
        
        # Le journal semble avoir un problème de séparateur, essayons avec ;
        try:
            journal_df = pd.read_csv(journal_file, encoding='latin-1', sep=';', dtype=str)
            print("Journal chargé avec séparateur ;")
        except:
            try:
                journal_df = pd.read_csv(journal_file, encoding='latin-1', dtype=str)
                print("Journal chargé avec séparateur par défaut")
            except:
                journal_df = pd.read_csv(journal_file, encoding='cp1252', dtype=str)
                print("Journal chargé avec encoding cp1252")
        
        transactions_df = pd.read_csv(transactions_file, encoding='utf-8', dtype=str)
        
        print(f"- Commandes: {len(orders_df)} lignes")
        print(f"- Journal: {len(journal_df)} lignes, {len(journal_df.columns)} colonnes")
        print(f"- Transactions: {len(transactions_df)} lignes")
        
        # Afficher les colonnes du journal
        print(f"\nColonnes du journal:")
        for i, col in enumerate(journal_df.columns):
            print(f"{i:2d}: {col}")
        
        # Rechercher les commandes de Sersoub Dylan
        print("\n=== COMMANDES DE SERSOUB DYLAN ===")
        sersoub_orders = orders_df[
            (orders_df['Email'].str.contains('sersoub', case=False, na=False)) |
            (orders_df['Billing Name'].str.contains('Sersoub', case=False, na=False))
        ]
        
        print(f"Trouvé {len(sersoub_orders)} commandes de Sersoub Dylan")
        
        for idx, row in sersoub_orders.iterrows():
            print(f"\n--- Commande {row['Name']} ---")
            print(f"Email: {row['Email']}")
            print(f"Billing Name: {row['Billing Name']}")
            print(f"Total: {row['Total']}")
            print(f"Subtotal: {row['Subtotal']}")
            print(f"Taxes: {row['Taxes']}")
            print(f"Payment Method: {row['Payment Method']}")
            
            order_name = row['Name']
            order_ref = order_name.replace('#', '').replace('LCDI-', '')
            
            print(f"Référence à chercher: {order_name} / {order_ref}")
            
            # Chercher dans le journal
            print("\n--- Recherche dans le journal ---")
            journal_matches = []
            
            # Recherche dans toutes les colonnes du journal
            for col in journal_df.columns:
                if journal_df[col].dtype == 'object':  # Colonnes texte
                    # Recherche exacte
                    exact_matches = journal_df[journal_df[col].str.contains(order_name, case=False, na=False)]
                    if len(exact_matches) > 0:
                        print(f"  Correspondance exacte dans {col}: {len(exact_matches)}")
                        journal_matches.extend(exact_matches.to_dict('records'))
                    
                    # Recherche par référence courte
                    short_matches = journal_df[journal_df[col].str.contains(order_ref, case=False, na=False)]
                    if len(short_matches) > 0:
                        print(f"  Correspondance courte dans {col}: {len(short_matches)}")
                        for _, match in short_matches.iterrows():
                            print(f"    - {col}: {match[col]}")
            
            if not journal_matches:
                print("  Aucune correspondance trouvée dans le journal")
                
                # Afficher quelques lignes du journal pour debug
                print("\n  Échantillon du journal (premières lignes):")
                for i, (_, row_j) in enumerate(journal_df.head(5).iterrows()):
                    print(f"    Ligne {i}: {dict(row_j)}")
            
            # Chercher dans les transactions
            print("\n--- Recherche dans les transactions ---")
            transaction_matches = transactions_df[
                transactions_df['Order'].str.contains(order_name, case=False, na=False)
            ]
            
            if len(transaction_matches) > 0:
                print(f"  Trouvé {len(transaction_matches)} transactions:")
                for _, trans in transaction_matches.iterrows():
                    print(f"    - Order: {trans['Order']}")
                    print(f"    - Amount: {trans['Amount']}")
                    print(f"    - Payment Method: {trans['Payment Method Name']}")
                    print(f"    - Card Brand: {trans['Card Brand']}")
            else:
                print("  Aucune transaction trouvée")
            
            print("-" * 70)
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_sersoub_complet()
