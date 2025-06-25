import pandas as pd

# Lire le fichier Excel
df = pd.read_excel(r'output\Compta_LCDI_Amazon_23_06_2025_11_03_48.xlsx', header=1)

print('=== ANALYSE DU FICHIER EXCEL ===')
print('Nombre total de factures:', len(df))

# Vérifier les noms vides
empty_names = df[df['Nom contact'].isna() | (df['Nom contact'] == '') | (df['Nom contact'].astype(str) == 'nan')]
print('Factures SANS nom:', len(empty_names))

if len(empty_names) > 0:
    print('\nDétails des factures sans nom:')
    for i, row in empty_names.iterrows():
        pays = row['Pays']
        facture = row['Facture AMAZON'] 
        print(f'  - Pays: {pays} | Facture: {facture}')

# Vérifier spécifiquement les factures maltaises
malta_rows = df[df['Pays'] == 'MT']
if len(malta_rows) > 0:
    print(f'\n=== FACTURES MALTAISES ({len(malta_rows)}) ===')
    for i, row in malta_rows.iterrows():
        facture = row['Facture AMAZON']
        nom = row['Nom contact']
        if pd.isna(nom) or nom == '' or str(nom) == 'nan':
            nom = 'VIDE'
        print(f'  - Facture: {facture} | Nom: "{nom}"')
else:
    print('\n=== AUCUNE FACTURE MALTAISE TROUVÉE ===')

# Compter par pays
print('\n=== RÉPARTITION PAR PAYS ===')
pays_counts = df['Pays'].value_counts()
for pays, count in pays_counts.items():
    print(f'  {pays}: {count} factures')
