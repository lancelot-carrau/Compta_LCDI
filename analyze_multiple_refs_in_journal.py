import pandas as pd
import re

# Analyser les références multiples dans le journal pour comprendre tous les cas
try:
    journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', encoding='utf-8')
except UnicodeDecodeError:
    journal_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv', encoding='latin-1')

print("=== ANALYSE DES RÉFÉRENCES MULTIPLES DANS LE JOURNAL ===")

# Rechercher toutes les lignes avec des références multiples (pattern : LCDI-XXXX LCDI-YYYY)
multiple_refs_pattern = r'LCDI-\d+(?:\s+LCDI-\d+)+'
lines_with_multiple_refs = []

for idx, row in journal_df.iterrows():
    # Chercher dans toutes les colonnes de type string
    for col in journal_df.columns:
        if journal_df[col].dtype == 'object':
            cell_value = str(row[col]) if pd.notna(row[col]) else ""
            if re.search(multiple_refs_pattern, cell_value):
                # Extraire toutes les références de la ligne
                refs = re.findall(r'LCDI-\d+', cell_value)
                if len(refs) > 1:  # Plus d'une référence trouvée
                    lines_with_multiple_refs.append({
                        'journal_index': idx,
                        'column': col,
                        'content': cell_value,
                        'references': refs,
                        'montant_journal': row.get('Montant du document TTC', 'N/A'),
                        'ref_lmb': row.get('Réf. LMB', 'N/A')
                    })

print(f"Lignes du journal avec références multiples trouvées: {len(lines_with_multiple_refs)}")

# Afficher tous les cas trouvés
for i, case in enumerate(lines_with_multiple_refs):
    print(f"\n--- CAS {i+1} ---")
    print(f"Index journal: {case['journal_index']}")
    print(f"Colonne: {case['column']}")
    print(f"Contenu: {case['content']}")
    print(f"Références extraites: {case['references']}")
    print(f"Montant journal TTC: {case['montant_journal']}")
    print(f"Réf. LMB: {case['ref_lmb']}")

# Analyser les commandes correspondantes
print("\n=== ANALYSE DES COMMANDES CORRESPONDANTES ===")
try:
    commands_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv', encoding='utf-8')
except UnicodeDecodeError:
    commands_df = pd.read_csv('c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv', encoding='latin-1')

# Pour chaque cas de références multiples, vérifier les montants des commandes
for case in lines_with_multiple_refs:
    print(f"\n--- COMMANDES POUR {case['references']} ---")
    total_commands_amount = 0
    
    for ref in case['references']:
        # Chercher la commande correspondante (avec ou sans #)
        ref_patterns = [f"#{ref}", ref]
        command_found = False
        
        for pattern in ref_patterns:
            matching_commands = commands_df[commands_df['Name'].str.contains(pattern, na=False)]
            if not matching_commands.empty:
                command = matching_commands.iloc[0]
                command_total = command.get('Total', 'N/A')
                print(f"  {ref}: {command_total} (colonne Total)")
                if pd.notna(command_total) and str(command_total).replace(',', '.').replace('€', '').strip().replace(' ', ''):
                    try:
                        amount = float(str(command_total).replace(',', '.').replace('€', '').strip())
                        total_commands_amount += amount
                    except:
                        pass
                command_found = True
                break
        
        if not command_found:
            print(f"  {ref}: Commande non trouvée")
    
    print(f"  TOTAL des commandes: {total_commands_amount}€")
    print(f"  Montant journal: {case['montant_journal']}")
    
    # Comparer avec le montant du journal
    if case['montant_journal'] != 'N/A':
        try:
            journal_amount = float(str(case['montant_journal']).replace(',', '.').replace('€', '').strip())
            difference = abs(total_commands_amount - journal_amount)
            print(f"  DIFFÉRENCE: {difference}€")
            if difference > 0.01:
                print(f"  ⚠️ INCOHÉRENCE détectée!")
            else:
                print(f"  ✅ Montants cohérents")
        except:
            print(f"  ❓ Impossible de comparer les montants")

print("\n=== RÉSUMÉ ===")
print(f"Total de cas de références multiples: {len(lines_with_multiple_refs)}")
if lines_with_multiple_refs:
    all_refs = []
    for case in lines_with_multiple_refs:
        all_refs.extend(case['references'])
    print(f"Toutes les références concernées: {list(set(all_refs))}")
    print(f"Nombre de commandes potentiellement affectées: {len(set(all_refs))}")
