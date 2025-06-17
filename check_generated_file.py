import pandas as pd

# Analyser le fichier généré pour voir les lignes 1020/1021
df = pd.read_excel('c:/Code/Apps/Compta LCDI V2/output/tableau_facturation_final_20250617_125250.xlsx')

print("=== ANALYSE DU FICHIER GÉNÉRÉ ===")
print(f"Total de lignes: {len(df)}")
print(f"Colonnes: {list(df.columns)}")

# Chercher les lignes contenant 1020 ou 1021
print(f"\n=== RECHERCHE DES LIGNES 1020/1021 ===")

# Chercher dans toutes les colonnes possibles
for col in df.columns:
    if df[col].dtype == 'object':  # Colonnes de texte
        lines_with_refs = df[df[col].astype(str).str.contains('1020|1021', na=False)]
        if not lines_with_refs.empty:
            print(f"\nTrouvé dans la colonne '{col}': {len(lines_with_refs)} lignes")
            for idx, row in lines_with_refs.iterrows():
                print(f"  Ligne {idx}: {row[col]} - TTC: {row.get('TTC', 'N/A')} - Réf. LMB: {row.get('Réf. LMB', 'N/A')}")

# Si on ne trouve rien, afficher quelques lignes d'exemple
if not any(df[col].astype(str).str.contains('1020|1021', na=False).any() for col in df.columns if df[col].dtype == 'object'):
    print("❌ Aucune ligne 1020/1021 trouvée dans le fichier généré")
    print("\nPremières lignes du fichier:")
    print(df.head())
    
    # Chercher des références LCDI en général
    for col in df.columns:
        if df[col].dtype == 'object':
            lcdi_lines = df[df[col].astype(str).str.contains('LCDI|#', na=False)]
            if not lcdi_lines.empty:
                print(f"\nExemples de références dans '{col}':")
                print(lcdi_lines[col].head().tolist())
                break

print(f"\n=== STATISTIQUES GÉNÉRALES ===")
print(f"Réf. LMB remplies: {df['Réf. LMB'].notna().sum()}/{len(df)} ({df['Réf. LMB'].notna().sum()/len(df)*100:.1f}%)")
if 'TTC' in df.columns:
    print(f"Somme TTC totale: {df['TTC'].sum():.2f}€")
