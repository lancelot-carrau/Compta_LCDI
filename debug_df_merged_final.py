import pandas as pd
import sys
import os

# Ajouter le répertoire de l'app au path
sys.path.insert(0, r'C:\Code\Apps\Compta LCDI V2')
from app import detect_encoding, normalize_column_names, validate_required_columns, clean_text_data, format_date_to_french, improve_journal_matching, categorize_payment_method

# Configuration des chemins
JOURNAL_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
COMMANDES_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def debug_df_merged_final():
    """Debug spécifique de df_merged_final pour comprendre les méthodes de paiement"""
    print("=== DEBUG DF_MERGED_FINAL ===\n")
    
    # 1. Charger et préparer les données comme dans le code principal
    print("1. Chargement et préparation des données...")
    
    # Charger
    encoding_orders = detect_encoding(COMMANDES_FILE)
    df_orders = pd.read_csv(COMMANDES_FILE, encoding=encoding_orders)
    
    encoding_transactions = detect_encoding(TRANSACTIONS_FILE)
    df_transactions = pd.read_csv(TRANSACTIONS_FILE, encoding=encoding_transactions)
    
    encoding_journal = detect_encoding(JOURNAL_FILE)
    df_journal = pd.read_csv(JOURNAL_FILE, encoding=encoding_journal)
    
    # Normaliser les colonnes
    required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method', 'Total', 'Taxes']
    df_orders = normalize_column_names(df_orders, required_orders_cols, 'commandes')
    
    required_trans_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
    df_transactions = normalize_column_names(df_transactions, required_trans_cols, 'transactions')
    
    required_journal_cols = ['Piece', 'Référence LMB']
    df_journal = normalize_column_names(df_journal, required_journal_cols, 'journal')
    
    # Nettoyer
    df_orders = clean_text_data(df_orders, ['Name', 'Billing name', 'Financial Status', 'Payment Method'])
    df_transactions = clean_text_data(df_transactions, ['Order'])
    df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
    
    # Formater les dates et montants
    df_orders['Fulfilled at'] = df_orders['Fulfilled at'].apply(format_date_to_french)
    
    monetary_cols_orders = ['Tax 1 Value', 'Outstanding Balance']
    monetary_cols_transactions = ['Presentment Amount', 'Fee', 'Net']
    
    for col in monetary_cols_orders:
        if col in df_orders.columns:
            df_orders[col] = pd.to_numeric(df_orders[col], errors='coerce').fillna(0)
    
    for col in monetary_cols_transactions:
        if col in df_transactions.columns:
            df_transactions[col] = pd.to_numeric(df_transactions[col], errors='coerce').fillna(0)
    
    # Agrégation des commandes
    df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
    df_orders = df_orders_aggregated
    
    # Agrégation des transactions
    df_transactions_aggregated = df_transactions.groupby('Order').agg({
        'Presentment Amount': 'sum',
        'Fee': 'sum',
        'Net': 'sum'
    }).reset_index()
    
    # 2. Fusion étape par étape
    print("\n2. Fusion étape par étape...")
    
    # Fusion commandes + transactions
    df_merged_step1 = pd.merge(df_orders, df_transactions_aggregated, 
                              left_on='Name', right_on='Order', how='left')
    print(f"   Après fusion commandes-transactions: {len(df_merged_step1)} lignes")
    
    # Vérifier Payment Method avant fusion avec journal
    print(f"\n3. Analyse Payment Method AVANT fusion avec journal:")
    if 'Payment Method' in df_merged_step1.columns:
        pm_counts = df_merged_step1['Payment Method'].value_counts()
        print(f"   Méthodes de paiement trouvées:")
        for method, count in pm_counts.items():
            print(f"     - '{method}': {count} commandes")
            
        # Test de quelques lignes
        print(f"\n   Échantillon de 5 lignes avec Payment Method et Presentment Amount:")
        for i in range(min(5, len(df_merged_step1))):
            row = df_merged_step1.iloc[i]
            name = row['Name']
            pm = row['Payment Method']
            amount = row['Presentment Amount']
            print(f"     {name}: {pm} -> {amount}€")
    
    # Fusion avec journal
    commandes_dans_journal = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
    
    if commandes_dans_journal < len(df_merged_step1):
        print(f"\n4. Fusion avec journal (avec amélioration)...")
        df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
    else:
        print(f"\n4. Fusion avec journal (standard)...")
        df_merged_final = pd.merge(df_merged_step1, df_journal, 
                                  left_on='Name', right_on='Piece', how='left')
    
    print(f"   Après fusion avec journal: {len(df_merged_final)} lignes")
    
    # 5. Vérifier Payment Method APRÈS fusion avec journal
    print(f"\n5. Analyse Payment Method APRÈS fusion avec journal:")
    if 'Payment Method' in df_merged_final.columns:
        pm_counts = df_merged_final['Payment Method'].value_counts()
        print(f"   Méthodes de paiement trouvées:")
        for method, count in pm_counts.items():
            print(f"     - '{method}': {count} commandes")
            
        # Test de quelques lignes
        print(f"\n   Échantillon de 5 lignes avec Payment Method et Presentment Amount:")
        for i in range(min(5, len(df_merged_final))):
            row = df_merged_final.iloc[i]
            name = row['Name']
            pm = row['Payment Method']
            amount = row['Presentment Amount']
            print(f"     {name}: {pm} -> {amount}€")
    
    # 6. Test direct de la logique de catégorisation sur df_merged_final
    print(f"\n6. Test de la logique de catégorisation sur df_merged_final:")
    
    for i in range(min(10, len(df_merged_final))):
        row = df_merged_final.iloc[i]
        name = row['Name']
        pm = row['Payment Method']
        amount = row['Presentment Amount']
        
        # Appliquer la fonction
        result = categorize_payment_method(pm, amount)
        assigned = [k for k, v in result.items() if v > 0]
        
        print(f"   {name}: '{pm}' ({amount}€) -> {assigned[0] if assigned else 'Non assigné'}")

if __name__ == "__main__":
    debug_df_merged_final()
