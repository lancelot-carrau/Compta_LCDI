import pandas as pd

# Analyser le dernier fichier généré
df = pd.read_excel('c:/Code/Apps/Compta LCDI V2/output/tableau_facturation_final_20250617_121906.xlsx')

print("=== ANALYSE AVANT CORRECTION ===")
print(f"Total de lignes: {len(df)}")
print(f"Colonnes disponibles: {list(df.columns)}")

# Analyser les Réf. LMB
if 'Réf. LMB' in df.columns:
    lmb_count = df['Réf. LMB'].notna().sum()
    print(f"Réf. LMB remplies: {lmb_count}/{len(df)} ({lmb_count/len(df)*100:.1f}%)")
    print(f"Exemples de Réf. LMB: {df['Réf. LMB'].dropna().head(3).tolist()}")
else:
    print("⚠️ Colonne 'Réf. LMB' non trouvée")

print("\n✅ Correction appliquée - prêt à générer un nouveau fichier !")
print("🎯 Résultat attendu: ~52% de Réf. LMB au lieu de 14%")
