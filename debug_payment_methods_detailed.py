import pandas as pd
import numpy as np
import sys
import os

# Configuration des chemins
JOURNAL_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
COMMANDES_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

# Ajouter le répertoire de l'app au path pour importer les fonctions
sys.path.insert(0, r'C:\Code\Apps\Compta LCDI V2')
from app import detect_encoding, categorize_payment_method

def analyze_payment_methods():
    """Analyse les méthodes de paiement dans les données sources et le traitement"""
    print("=== DIAGNOSTIC DES MÉTHODES DE PAIEMENT ===\n")
    
    # 1. Charger les données
    print("1. Chargement des données...")
    
    # Transactions
    encoding_transactions = detect_encoding(TRANSACTIONS_FILE)
    df_transactions = pd.read_csv(TRANSACTIONS_FILE, encoding=encoding_transactions)
    print(f"   Transactions: {len(df_transactions)} lignes")
    
    # Commandes
    encoding_commandes = detect_encoding(COMMANDES_FILE)
    df_commandes = pd.read_csv(COMMANDES_FILE, encoding=encoding_commandes)
    print(f"   Commandes: {len(df_commandes)} lignes")
      # 2. Analyser les colonnes des transactions
    print("\n2. Colonnes disponibles dans les transactions:")
    print(f"   {list(df_transactions.columns)}")
    
    # 2bis. Analyser les méthodes de paiement dans les transactions
    print("\n2bis. Analyse des méthodes de paiement dans les transactions:")
    if 'Payment Method' in df_transactions.columns:
        payment_methods = df_transactions['Payment Method'].value_counts()
        print("   Méthodes trouvées dans Payment Method:")
        for method, count in payment_methods.items():
            print(f"     - '{method}': {count} occurrences")
        
        # Test de catégorisation pour chaque méthode
        print("\n   Test de catégorisation:")
        for method in payment_methods.index:
            if pd.notna(method):
                result = categorize_payment_method(method, 100)  # Test avec montant 100
                assigned_to = [k for k, v in result.items() if v > 0]
                print(f"     '{method}' -> {assigned_to[0] if assigned_to else 'Non assigné'}")
    else:
        print("   Colonne 'Payment Method' non trouvée dans les transactions")
    
    # 3. Analyser les montants dans les transactions
    print("\n3. Analyse des montants dans les transactions:")
    if 'Presentment Amount' in df_transactions.columns:
        amounts = df_transactions['Presentment Amount']
        non_zero = amounts[amounts > 0]
        print(f"   Montants > 0: {len(non_zero)} sur {len(amounts)} transactions")
        print(f"   Montant min: {amounts.min()}, max: {amounts.max()}")
      # 4. Analyser les références pour le matching
    print("\n4. Analyse des références pour le matching:")
    ref_col = None
    for col in df_transactions.columns:
        if 'ref' in col.lower() or 'order' in col.lower():
            ref_col = col
            break
    
    if ref_col:
        print(f"   Colonne de référence trouvée: '{ref_col}'")
        refs = df_transactions[ref_col].value_counts().head(10)
        print(f"   Références les plus fréquentes:")
        for ref, count in refs.items():
            print(f"     - '{ref}': {count}")
    else:
        print("   Aucune colonne de référence trouvée")    # 5. Analyser les méthodes dans les commandes aussi
    print("\n5. Analyse des méthodes de paiement dans les commandes:")
    payment_cols = [col for col in df_commandes.columns if 'payment' in col.lower() or 'gateway' in col.lower()]
    if payment_cols:
        print(f"   Colonnes liées au paiement trouvées: {payment_cols}")
        for col in payment_cols:
            unique_values = df_commandes[col].value_counts().head(10)
            print(f"   Colonne '{col}':")
            for val, count in unique_values.items():
                print(f"     - '{val}': {count}")
    else:
        print("   Aucune colonne de paiement trouvée dans les commandes")
    
    # 6. Test de catégorisation sur les méthodes des commandes
    print("\n6. Test de catégorisation sur les méthodes trouvées:")
    if 'Payment Method' in df_commandes.columns:
        methods = df_commandes['Payment Method'].unique()
        for method in methods:
            if pd.notna(method):
                result = categorize_payment_method(method, 100)
                assigned_to = [k for k, v in result.items() if v > 0]
                print(f"   '{method}' -> {assigned_to[0] if assigned_to else 'Non assigné'}")
    
    # 7. Chercher des liens entre commandes et transactions
    print("\n7. Analyse des liens commandes <-> transactions:")
    
    # Chercher des colonnes communes
    trans_cols = set(df_transactions.columns)
    order_cols = set(df_commandes.columns)
    common_cols = trans_cols.intersection(order_cols)
    print(f"   Colonnes communes: {list(common_cols)}")
    
    # Vérifier la colonne Name/Order ID
    if 'Name' in df_commandes.columns:
        print(f"   Commandes - colonne Name: {df_commandes['Name'].head(5).tolist()}")
    if 'Order ID' in df_transactions.columns:
        print(f"   Transactions - colonne Order ID: {df_transactions['Order ID'].head(5).tolist()}")

if __name__ == "__main__":
    analyze_payment_methods()
