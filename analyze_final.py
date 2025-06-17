import pandas as pd

# Analyser le fichier généré
fichier = "output/tableau_facturation_final_corrige_20250617_141130.xlsx"
df = pd.read_excel(fichier)

print(f"Total lignes: {len(df)}")
print(f"Réf. LMB remplies: {df['Réf. LMB'].notna().sum()}")
print(f"Réf. LMB vides: {df['Réf. LMB'].isna().sum()}")

# Analyser les commandes sans Réf. LMB
sans_lmb = df[df['Réf. LMB'].isna() | (df['Réf. LMB'] == '')]
print(f"\nCommandes sans Réf. LMB: {len(sans_lmb)}")
if len(sans_lmb) > 0:
    print("Échantillon commandes sans LMB:")
    for idx, row in sans_lmb.head(10).iterrows():
        print(f"  {row['Réf.WEB']} - {row['Client']}")

# Analyser les sources de données originales
print("\nAnalyse des sources originales...")

orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"

df_orders = pd.read_csv(orders_file, encoding='utf-8')
df_journal = pd.read_csv(journal_file, encoding='latin-1', delimiter=';')

print(f"Commandes brutes: {len(df_orders)}")
print(f"Commandes uniques: {df_orders['Name'].nunique()}")
print(f"Journal: {len(df_journal)}")
print(f"Références journal uniques: {df_journal['Référence externe'].nunique()}")

# Agrégation comme dans l'app
df_orders_agg = df_orders.drop_duplicates(subset=['Name'], keep='first')
print(f"Commandes après agrégation: {len(df_orders_agg)}")

# Correspondances théoriques
import re
references_journal = df_journal['Référence externe'].dropna().unique()
correspondances_directes = 0
correspondances_multiples = 0

commandes_set = set()
for cmd in df_orders_agg['Name'].dropna():
    cmd_str = str(cmd).strip()
    commandes_set.add(cmd_str)
    if cmd_str.startswith('#'):
        commandes_set.add(cmd_str[1:])
    else:
        commandes_set.add(f"#{cmd_str}")

for ref in references_journal:
    if pd.isna(ref):
        continue
    ref_str = str(ref).strip()
    
    if ' ' in ref_str and ref_str.count('LCDI-') > 1:
        # Référence multiple
        numbers = re.findall(r'LCDI-(\d+)', ref_str)
        for num in numbers:
            if f"#LCDI-{num}" in commandes_set or f"LCDI-{num}" in commandes_set:
                correspondances_multiples += 1
    else:
        # Référence simple
        if ref_str in commandes_set:
            correspondances_directes += 1

total_theorique = correspondances_directes + correspondances_multiples
print(f"\nCorrespondances théoriques:")
print(f"- Directes: {correspondances_directes}")
print(f"- Multiples: {correspondances_multiples}")
print(f"- Total: {total_theorique}")
print(f"- Obtenu: 22")
print(f"- Écart: {total_theorique - 22}")
