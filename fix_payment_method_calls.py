import re

# Lire le fichier
with open(r'C:\Code\Apps\Compta LCDI V2\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern pour trouver les appels à categorize_payment_method dans df_merged_final.apply
old_pattern = r"""payment_categorization = df_merged_final\.apply\(
            lambda row: categorize_payment_method\(row\['Payment Method'\], row\['Presentment Amount'\]\), 
            axis=1
        \)"""

new_pattern = """payment_categorization = df_merged_final.apply(
            lambda row: categorize_payment_method(
                row['Payment Method'], 
                row['Presentment Amount'], 
                fallback_amount=row.get('Total', 0)  # Utiliser le montant de la commande si pas de transaction
            ), 
            axis=1
        )"""

# Remplacer toutes les occurrences
new_content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Compter les remplacements
count = len(re.findall(old_pattern, content, flags=re.MULTILINE))
new_count = len(re.findall(re.escape(new_pattern), new_content, flags=re.MULTILINE))

print(f"Trouvé {count} occurrences de l'ancien pattern")
print(f"Remplacé par {new_count} occurrences du nouveau pattern")

# Sauvegarder le fichier
with open(r'C:\Code\Apps\Compta LCDI V2\app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fichier sauvegardé avec succès!")
