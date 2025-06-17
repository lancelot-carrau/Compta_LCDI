#!/usr/bin/env python3
"""Script pour remplacer les affectations directes de Date Facture"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_pattern = "df_final['Date Facture'] = df_merged_final['Fulfilled at']"
new_pattern = "df_final['Date Facture'] = calculate_invoice_dates(df_merged_final)"

new_content = content.replace(old_pattern, new_pattern)

# Compter les remplacements
count = content.count(old_pattern)
print(f"Nombre d'occurrences trouvées: {count}")

if count > 0:
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Remplacements effectués avec succès!")
else:
    print("Aucune occurrence trouvée à remplacer.")
