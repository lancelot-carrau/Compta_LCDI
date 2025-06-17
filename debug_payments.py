import pandas as pd

# Diagnostic simple des méthodes de paiement
print("=== DIAGNOSTIC MÉTHODES DE PAIEMENT ===")

fichier = "output/tableau_facturation_final_corrige_20250617_143113.xlsx"
df = pd.read_excel(fichier)

print(f"Total lignes: {len(df)}")

# Vérifier les colonnes de paiement
colonnes_paiement = ['Virement bancaire', 'ALMA', 'Younited', 'PayPal']
for col in colonnes_paiement:
    if col in df.columns:
        non_zero = (df[col] != 0).sum()
        total = df[col].sum()
        print(f"{col}: {non_zero} non-nulles, total: {total}€")

# Examiner les données sources
orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
df_orders = pd.read_csv(orders_file, encoding='utf-8')

print(f"\nCommandes sources: {len(df_orders)}")
if 'Payment Method' in df_orders.columns:
    methods = df_orders['Payment Method'].value_counts()
    print("Méthodes de paiement sources:")
    for method, count in methods.items():
        print(f"  {method}: {count}")

# Chercher les PayPal spécifiquement
paypal_count = df_orders['Payment Method'].str.contains('PayPal', case=False, na=False).sum()
print(f"\nCommandes PayPal dans source: {paypal_count}")

# Vérifier les transactions
transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
df_trans = pd.read_csv(transactions_file, encoding='utf-8')

print(f"Transactions: {len(df_trans)}")
if 'Presentment Amount' in df_trans.columns:
    non_null_amounts = df_trans['Presentment Amount'].notna().sum()
    print(f"Presentment Amount non-null: {non_null_amounts}")
    print(f"Total Presentment Amount: {df_trans['Presentment Amount'].sum()}")

print("\nProblème probable: Presentment Amount vide -> montants de paiement = 0")
