import pandas as pd

# Test simple
orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"

print("Lecture des fichiers...")
df_orders = pd.read_csv(orders_file, encoding='utf-8')
df_journal = pd.read_csv(journal_file, encoding='latin-1', delimiter=';')

print(f"Commandes brutes: {len(df_orders)}")
print(f"Commandes uniques: {df_orders['Name'].nunique()}")
print(f"Journal: {len(df_journal)}")
print(f"Références journal: {df_journal['Référence externe'].nunique()}")

# Vérifier les doublons
duplicates = df_orders[df_orders.duplicated(subset=['Name'], keep=False)]
print(f"Lignes avec doublons: {len(duplicates)}")
if len(duplicates) > 0:
    print(f"Commandes dupliquées: {duplicates['Name'].unique()}")

# Test de correspondance simple
commandes_set = set(df_orders['Name'].dropna())
references_set = set(df_journal['Référence externe'].dropna())

# Normaliser pour la comparaison
commandes_norm = set()
for cmd in commandes_set:
    commandes_norm.add(str(cmd))
    if str(cmd).startswith('#'):
        commandes_norm.add(str(cmd)[1:])
    else:
        commandes_norm.add(f"#{str(cmd)}")

correspondances = 0
for ref in references_set:
    if str(ref) in commandes_norm:
        correspondances += 1

print(f"Correspondances directes trouvées: {correspondances}")

# Analyser les références multiples
import re
multiples = 0
for ref in references_set:
    ref_str = str(ref)
    if ' ' in ref_str and ref_str.count('LCDI-') > 1:
        numbers = re.findall(r'LCDI-(\d+)', ref_str)
        for num in numbers:
            if f"#LCDI-{num}" in commandes_norm or f"LCDI-{num}" in commandes_norm:
                multiples += 1

print(f"Correspondances multiples: {multiples}")
print(f"Total théorique: {correspondances + multiples}")
print(f"Obtenu (selon le log): 22")
print(f"Différence: {correspondances + multiples - 22}")
            print(f"✓ Mapping trouvé: {variant} -> {expected_col}")
            found = True
            break
    if not found:
        print(f"❌ Aucun mapping trouvé pour: {expected_col}")

print("Test terminé avec succès!")
