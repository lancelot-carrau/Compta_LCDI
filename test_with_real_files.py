#!/usr/bin/env python3
"""
Test avec les vrais fichiers pour vérifier le taux de correspondance
"""

import sys
import os
import pandas as pd
sys.path.append('.')
from app import process_dataframes_directly, detect_encoding

def test_with_real_files():
    """Test avec les vrais fichiers"""
    
    # Chemin des fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    try:
        print("=== CHARGEMENT DES FICHIERS RÉELS ===")
        
        # Chargement du journal
        journal_encoding = detect_encoding(journal_path)
        df_journal = pd.read_csv(journal_path, encoding=journal_encoding, sep=';')
        print(f"Journal chargé : {len(df_journal)} lignes")
        print(f"Colonnes journal : {list(df_journal.columns)}")
        
        # Chargement des commandes 
        orders_encoding = detect_encoding(orders_path)
        df_orders = pd.read_csv(orders_path, encoding=orders_encoding)
        print(f"Commandes chargées : {len(df_orders)} lignes")
        print(f"Colonnes commandes : {list(df_orders.columns)}")
        
        # Chargement des transactions
        trans_encoding = detect_encoding(transactions_path)
        df_transactions = pd.read_csv(transactions_path, encoding=trans_encoding)
        print(f"Transactions chargées : {len(df_transactions)} lignes")
        print(f"Colonnes transactions : {list(df_transactions.columns)}")
        
        print("\n=== APERÇU DES RÉFÉRENCES ===")
        print("Journal (Référence externe) :")
        journal_refs = df_journal['Référence externe'].dropna().head(10).tolist()
        for ref in journal_refs:
            print(f"  - {ref}")
            
        print("\nCommandes (Name) :")
        order_refs = df_orders['Name'].dropna().head(10).tolist()
        for ref in order_refs:
            print(f"  - {ref}")
            
        print("\nTransactions (Order) :")
        trans_refs = df_transactions['Order'].dropna().head(10).tolist()
        for ref in trans_refs:
            print(f"  - {ref}")
        
        print("\n=== TRAITEMENT AVEC L'APPLICATION ===")
          # Traitement avec notre fonction améliorée
        df_final = process_dataframes_directly(df_orders, df_transactions, df_journal)
        
        print(f"\n=== RÉSULTAT FINAL ===")
        print(f"Tableau final : {len(df_final)} lignes")
        print(f"Colonnes du tableau final : {list(df_final.columns)}")
        
        # Analyser les Réf. LMB trouvées
        ref_lmb_non_vides = df_final['Réf. LMB'].notna() & (df_final['Réf. LMB'] != '')
        nb_ref_lmb = ref_lmb_non_vides.sum()
        print(f"Réf. LMB trouvées : {nb_ref_lmb}/{len(df_final)} ({nb_ref_lmb/len(df_final)*100:.1f}%)")
          # Afficher quelques exemples
        print("\nExemples de correspondances trouvées :")
        exemples = df_final[ref_lmb_non_vides][['Référence', 'Réf. LMB']].head(10)
        for _, row in exemples.iterrows():
            print(f"  {row['Référence']} -> {row['Réf. LMB']}")
        
        print("\nExemples de correspondances manquantes :")
        manquantes = df_final[~ref_lmb_non_vides][['Référence', 'Réf. LMB']].head(10)
        for _, row in manquantes.iterrows():
            print(f"  {row['Référence']} -> [MANQUANT]")
        
    except Exception as e:
        print(f"ERREUR : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_real_files()
