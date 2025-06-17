import pandas as pd
import re

# Analyser spécifiquement le cas LCDI-1020/1021 et chercher d'autres cas similaires
try:
    journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', encoding='utf-8')
except UnicodeDecodeError:
    journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', encoding='latin-1')

try:
    commands_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv', encoding='utf-8')
except UnicodeDecodeError:
    commands_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv', encoding='latin-1')

print("=== ANALYSE PRÉCISE DES RÉFÉRENCES MULTIPLES ===")
print(f"Colonnes du journal: {list(journal_df.columns)}")

# Chercher spécifiquement des patterns comme "1020 1021" ou "LCDI-1020 LCDI-1021"
patterns_to_check = [
    r'1020.*1021',  # 1020 suivi de 1021
    r'LCDI-1020.*LCDI-1021',  # Format complet
    r'\d{4}.*\d{4}',  # Deux nombres à 4 chiffres
    r'LCDI-\d+.*LCDI-\d+',  # Deux références LCDI
]

cases_found = []

for idx, row in journal_df.iterrows():
    for col in journal_df.columns:
        if journal_df[col].dtype == 'object':
            cell_value = str(row[col]) if pd.notna(row[col]) else ""
            
            # Vérifier chaque pattern
            for pattern in patterns_to_check:
                if re.search(pattern, cell_value, re.IGNORECASE):
                    # Extraire toutes les références LCDI de la ligne
                    refs = re.findall(r'LCDI-\d+', cell_value, re.IGNORECASE)
                    if not refs:
                        # Essayer d'extraire juste les numéros
                        nums = re.findall(r'\b\d{4}\b', cell_value)
                        refs = [f"LCDI-{num}" for num in nums if num.startswith('10')]
                    
                    if len(refs) >= 2 or len(re.findall(r'\b10\d{2}\b', cell_value)) >= 2:
                        cases_found.append({
                            'journal_index': idx,
                            'column': col,
                            'content': cell_value,
                            'pattern_matched': pattern,
                            'references_found': refs,
                            'montant_journal': row.get('Montant du document TTC', row.get('Total', 'N/A')),
                            'ref_lmb': row.get('Réf. LMB', 'N/A')
                        })

print(f"Cas potentiels trouvés: {len(cases_found)}")

# Afficher les premiers cas
for i, case in enumerate(cases_found[:10]):  # Limiter à 10 premiers cas
    print(f"\n--- CAS {i+1} ---")
    print(f"Index: {case['journal_index']}")
    print(f"Colonne: {case['column']}")
    print(f"Contenu: {case['content'][:200]}...")  # Tronquer si trop long
    print(f"Pattern: {case['pattern_matched']}")
    print(f"Références: {case['references_found']}")
    print(f"Montant: {case['montant_journal']}")
    print(f"Réf. LMB: {case['ref_lmb']}")

# Recherche spécifique du cas 1020/1021
print(f"\n=== RECHERCHE SPÉCIFIQUE 1020/1021 ===")
specific_search = journal_df[journal_df.astype(str).apply(lambda row: row.str.contains('1020.*1021|1021.*1020', case=False, na=False).any(), axis=1)]
print(f"Lignes contenant '1020' et '1021': {len(specific_search)}")

if not specific_search.empty:
    for idx, row in specific_search.iterrows():
        print(f"\nLigne {idx}:")
        for col in journal_df.columns:
            if pd.notna(row[col]) and ('1020' in str(row[col]) or '1021' in str(row[col])):
                print(f"  {col}: {row[col]}")

# Analyser les montants des commandes 1020 et 1021
print(f"\n=== MONTANTS DES COMMANDES 1020 ET 1021 ===")
for ref in ['1020', '1021']:
    # Chercher avec différents formats
    patterns = [f"#{ref}", f"LCDI-{ref}", f"#LCDI-{ref}"]
    
    for pattern in patterns:
        matching = commands_df[commands_df['Name'].str.contains(pattern, na=False)]
        if not matching.empty:
            cmd = matching.iloc[0]
            print(f"Commande {ref} (format {pattern}):")
            print(f"  Name: {cmd.get('Name', 'N/A')}")
            print(f"  Total: {cmd.get('Total', 'N/A')}")
            print(f"  Subtotal: {cmd.get('Subtotal', 'N/A')}")
            print(f"  Taxes: {cmd.get('Taxes', 'N/A')}")
            break
    else:
        print(f"Commande {ref}: Non trouvée")

print(f"\n=== ANALYSE DU FICHIER GÉNÉRÉ ===")
# Vérifier le fichier généré le plus récent
import glob
import os

output_files = glob.glob('c:/Code/Apps/Compta LCDI V2/output/tableau_*.xlsx')
if output_files:
    latest_file = max(output_files, key=os.path.getctime)
    df = pd.read_excel(latest_file)
    
    print(f"Fichier analysé: {latest_file}")
    
    # Chercher les lignes 1020 et 1021
    lines_1020_1021 = df[df['Commande'].str.contains('1020|1021', na=False)]
    if not lines_1020_1021.empty:
        print(f"Lignes 1020/1021 trouvées: {len(lines_1020_1021)}")
        for idx, row in lines_1020_1021.iterrows():
            print(f"  {row['Commande']}: Prix TTC = {row.get('Prix TTC', 'N/A')}, Réf. LMB = {row.get('Réf. LMB', 'N/A')}")
    else:
        print("Aucune ligne 1020/1021 trouvée dans le fichier généré")
