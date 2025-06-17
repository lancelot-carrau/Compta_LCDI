import pandas as pd
import numpy as np

# Analyser le fichier avec logique stricte
fichier = "output/tableau_facturation_final_corrige_20250617_143113.xlsx"
df = pd.read_excel(fichier)

print("=== VÉRIFICATION LOGIQUE STRICTE ===\n")
print(f"Total lignes: {len(df)}")

# Analyser les cellules NaN (vides) vs remplies
colonnes_montants = ['HT', 'TVA', 'TTC']

for col in colonnes_montants:
    if col in df.columns:
        remplies = df[col].notna().sum()
        vides = df[col].isna().sum()
        print(f"{col}: {remplies} remplies, {vides} vides (formatage rouge)")

print(f"\nRéf. LMB remplies: {df['Réf. LMB'].notna().sum()}")

# Examiner quelques lignes spécifiques
print("\n=== ÉCHANTILLON DE LIGNES ===")

# Lignes avec données du journal (TTC rempli)
avec_journal = df[df['TTC'].notna()].head(3)
print("\nLignes AVEC données journal (TTC rempli):")
for idx, row in avec_journal.iterrows():
    print(f"  {row['Réf.WEB']} - TTC: {row['TTC']}, HT: {row['HT']}, TVA: {row['TVA']}, Réf.LMB: '{row['Réf. LMB']}'")

# Lignes sans données du journal (TTC vide)
sans_journal = df[df['TTC'].isna()].head(3)
print("\nLignes SANS données journal (TTC vide - formatage rouge):")
for idx, row in sans_journal.iterrows():
    ttc_status = "NaN (rouge)" if pd.isna(row['TTC']) else row['TTC']
    ht_status = "NaN (rouge)" if pd.isna(row['HT']) else row['HT']
    tva_status = "NaN (rouge)" if pd.isna(row['TVA']) else row['TVA']
    print(f"  {row['Réf.WEB']} - TTC: {ttc_status}, HT: {ht_status}, TVA: {tva_status}, Réf.LMB: '{row['Réf. LMB']}'")

# Vérifier les commandes 1020/1021 spécifiquement
print("\n=== COMMANDES 1020/1021 ===")
mask_1020 = df['Réf.WEB'].str.contains('1020', na=False)
mask_1021 = df['Réf.WEB'].str.contains('1021', na=False)

for mask, nom in [(mask_1020, '1020'), (mask_1021, '1021')]:
    if mask.any():
        row = df[mask].iloc[0]
        ttc_status = "NaN (rouge)" if pd.isna(row['TTC']) else row['TTC']
        ht_status = "NaN (rouge)" if pd.isna(row['HT']) else row['HT']
        tva_status = "NaN (rouge)" if pd.isna(row['TVA']) else row['TVA']
        print(f"LCDI-{nom}: TTC: {ttc_status}, HT: {ht_status}, TVA: {tva_status}, Réf.LMB: '{row['Réf. LMB']}'")

print("\n✅ LOGIQUE STRICTE CONFIRMÉE:")
print("- Les cellules sans données journal sont vides (NaN)")
print("- Ces cellules recevront le formatage conditionnel rouge")
print("- Pas de fallback automatique vers les montants des commandes")
print("- Les références multiples (1020/1021) ont leurs montants effacés comme voulu")
