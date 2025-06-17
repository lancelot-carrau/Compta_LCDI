#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os

def diagnostic_colonnes():
    """Diagnostic des colonnes disponibles dans les fichiers"""
    
    print("=== DIAGNOSTIC DES COLONNES ===")
    
    # Chemins des fichiers
    orders_file = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    transactions_file = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    try:
        # Charger les fichiers
        print("=== COMMANDES ===")
        orders_df = pd.read_csv(orders_file, encoding='utf-8', dtype=str)
        print(f"Colonnes des commandes ({len(orders_df.columns)}):")
        for i, col in enumerate(orders_df.columns):
            print(f"{i:2d}: {col}")
        
        print(f"\nPremières lignes des commandes:")
        print(orders_df.head(2).to_string())
        
        print("\n=== JOURNAL ===")
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
        
        print(f"Colonnes du journal ({len(journal_df.columns)}):")
        for i, col in enumerate(journal_df.columns):
            print(f"{i:2d}: {col}")
        
        print(f"\nPremières lignes du journal:")
        print(journal_df.head(2).to_string())
        
        print("\n=== TRANSACTIONS ===")
        transactions_df = pd.read_csv(transactions_file, encoding='utf-8', dtype=str)
        print(f"Colonnes des transactions ({len(transactions_df.columns)}):")
        for i, col in enumerate(transactions_df.columns):
            print(f"{i:2d}: {col}")
        
        print(f"\nPremières lignes des transactions:")
        print(transactions_df.head(2).to_string())
        
        # Recherche des commandes contenant "sersoub" ou "dylan"
        print("\n=== RECHERCHE SERSOUB/DYLAN ===")
        for col in orders_df.columns:
            if orders_df[col].dtype == 'object':  # Colonnes texte
                matches = orders_df[orders_df[col].str.contains('sersoub|dylan', case=False, na=False)]
                if len(matches) > 0:
                    print(f"Trouvé dans colonne '{col}': {len(matches)} correspondances")
                    for _, row in matches.iterrows():
                        print(f"  - {row['Name']}: {row[col]}")
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_colonnes()
