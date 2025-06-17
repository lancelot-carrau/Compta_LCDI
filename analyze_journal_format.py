import pandas as pd
import re

# Analyser le fichier journal avec différents séparateurs
print("=== ANALYSE DU FORMAT DU JOURNAL ===")

# Essayer différents délimiteurs
for separator in [';', ',', '\t']:
    try:
        print(f"\nTest avec séparateur '{separator}':")
        if separator == ';':
            journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', 
                                   encoding='latin-1', sep=';')
        elif separator == ',':
            journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', 
                                   encoding='latin-1', sep=',')
        else:
            journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', 
                                   encoding='latin-1', sep='\t')
        
        print(f"Nombre de colonnes: {len(journal_df.columns)}")
        print(f"Colonnes: {list(journal_df.columns)[:5]}")  # Premières 5 colonnes
        
        if len(journal_df.columns) > 5:  # Si on a plus de colonnes, c'est probablement le bon séparateur
            print("✅ Ce séparateur semble correct!")
            
            # Chercher les références multiples dans les bonnes colonnes
            print(f"\n=== RECHERCHE DES RÉFÉRENCES MULTIPLES ===")
            
            multiple_cases = []
            for idx, row in journal_df.iterrows():
                # Chercher dans la colonne "Référence externe" principalement
                ref_externe = str(row.get('Référence externe', '')) if 'Référence externe' in journal_df.columns else ''
                
                # Chercher des patterns de références multiples
                if '1020' in ref_externe and '1021' in ref_externe:
                    multiple_cases.append({
                        'index': idx,
                        'ref_externe': ref_externe,
                        'montant_ttc': row.get('Montant du document TTC', 'N/A'),
                        'ref_lmb': row.get('Référence LMB', 'N/A'),
                        'nom_contact': row.get('Nom contact', 'N/A')
                    })
                    print(f"TROUVÉ - Ligne {idx}: {ref_externe}")
                
                # Chercher aussi d'autres patterns
                for col in journal_df.columns:
                    cell_value = str(row[col]) if pd.notna(row[col]) else ""
                    if re.search(r'LCDI-\d+.*LCDI-\d+', cell_value) or re.search(r'\d{4}.*\d{4}', cell_value):
                        if idx not in [case['index'] for case in multiple_cases]:
                            multiple_cases.append({
                                'index': idx,
                                'column': col,
                                'content': cell_value,
                                'montant_ttc': row.get('Montant du document TTC', 'N/A'),
                                'ref_lmb': row.get('Référence LMB', 'N/A')
                            })
            
            print(f"Cas de références multiples trouvés: {len(multiple_cases)}")
            
            for case in multiple_cases:
                print(f"\n--- CAS ---")
                print(f"Index: {case['index']}")
                if 'ref_externe' in case:
                    print(f"Référence externe: {case['ref_externe']}")
                    print(f"Nom contact: {case['nom_contact']}")
                else:
                    print(f"Colonne: {case['column']}")
                    print(f"Contenu: {case['content']}")
                print(f"Montant TTC: {case['montant_ttc']}")
                print(f"Réf. LMB: {case['ref_lmb']}")
            
            break
            
    except Exception as e:
        print(f"Erreur avec séparateur '{separator}': {e}")
        continue

# Analyser le fichier généré pour comprendre le problème des montants
print(f"\n=== ANALYSE DU FICHIER GÉNÉRÉ ===")
import glob
import os

output_files = glob.glob('c:/Code/Apps/Compta LCDI V2/output/tableau_*.xlsx')
if output_files:
    latest_file = max(output_files, key=os.path.getctime)
    df = pd.read_excel(latest_file)
    
    print(f"Fichier: {os.path.basename(latest_file)}")
    print(f"Colonnes: {list(df.columns)}")
    
    # Chercher les lignes avec 1020 et 1021
    if 'Name' in df.columns:
        col_name = 'Name'
    elif 'Commande' in df.columns:
        col_name = 'Commande'
    elif 'Order' in df.columns:
        col_name = 'Order'
    else:
        col_name = df.columns[0]  # Première colonne par défaut
    
    lines_1020_1021 = df[df[col_name].astype(str).str.contains('1020|1021', na=False)]
    
    print(f"\nLignes 1020/1021 trouvées: {len(lines_1020_1021)}")
    
    if not lines_1020_1021.empty:
        for idx, row in lines_1020_1021.iterrows():
            print(f"\n--- LIGNE {idx} ---")
            print(f"Référence: {row[col_name]}")
            
            # Chercher la colonne de prix
            price_cols = ['Prix TTC', 'Montant TTC', 'Total', 'Prix', 'Montant']
            for price_col in price_cols:
                if price_col in df.columns:
                    print(f"{price_col}: {row[price_col]}")
                    break
            
            # Chercher la colonne Réf. LMB
            lmb_cols = ['Réf. LMB', 'Référence LMB', 'LMB']
            for lmb_col in lmb_cols:
                if lmb_col in df.columns:
                    print(f"{lmb_col}: {row[lmb_col]}")
                    break

# Analyse des montants originaux des commandes
print(f"\n=== MONTANTS ORIGINAUX DES COMMANDES ===")
try:
    commands_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv', encoding='latin-1')
    
    for ref in ['1020', '1021']:
        cmd_line = commands_df[commands_df['Name'].str.contains(f'LCDI-{ref}', na=False)]
        if not cmd_line.empty:
            cmd = cmd_line.iloc[0]
            print(f"\nCommande LCDI-{ref}:")
            print(f"  Total: {cmd.get('Total', 'N/A')}")
            print(f"  Subtotal: {cmd.get('Subtotal', 'N/A')}")
            print(f"  Taxes: {cmd.get('Taxes', 'N/A')}")
except Exception as e:
    print(f"Erreur lecture commandes: {e}")
