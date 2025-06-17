import sys
sys.path.append('c:/Code/Apps/Compta LCDI V2')
from app import *
import pandas as pd

# Génération d'un nouveau fichier avec la correction des références multiples
print("=== GÉNÉRATION AVEC CORRECTION DES RÉFÉRENCES MULTIPLES ===")

# Fichiers sources
journal_path = 'c:/Users/Malo/Desktop/Compta LCDI/20250604-Journal.csv'
orders_path = 'c:/Users/Malo/Desktop/Compta LCDI/orders_export_1 (1).csv'
transactions_path = 'c:/Users/Malo/Desktop/Compta LCDI/payment_transactions_export_1 (2).csv'

# Lecture des fichiers
print("1. Lecture des fichiers...")
try:
    df_journal = pd.read_csv(journal_path, encoding='latin-1', sep=';')
    df_orders = pd.read_csv(orders_path, encoding='latin-1')
    df_transactions = pd.read_csv(transactions_path, encoding='latin-1')
    print("   ✅ Fichiers lus avec succès")
except Exception as e:
    print(f"   ❌ Erreur lecture: {e}")
    exit(1)

# Normalisation des colonnes
print("2. Normalisation des colonnes...")
df_journal = normalize_column_names(df_journal)
df_orders = normalize_column_names(df_orders)
df_transactions = normalize_column_names(df_transactions)

# Fusion intelligente avec la correction
print("3. Fusion avec gestion des références multiples...")
df_merged = merge_orders_with_journal_smart(df_orders, df_journal)

# Fusion avec les transactions
print("4. Fusion avec transactions...")
df_merged_final = merge_with_transactions(df_merged, df_transactions)

# Calcul des montants
print("5. Calcul des montants...")
df_merged_final = calculate_corrected_amounts(df_merged_final)

# Calcul des dates
print("6. Calcul des dates...")
df_merged_final = calculate_invoice_dates(df_merged_final)

# Génération du tableau final
print("7. Génération du tableau final...")
df_final = generate_final_table(df_merged_final)

# Ajout des informations de statut
print("8. Ajout des informations de statut...")
df_final = fill_missing_data_indicators(df_final, df_merged_final)

# Sauvegarde
print("9. Sauvegarde...")
output_path = f'output/tableau_correction_multiples_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
df_final.to_excel(output_path, index=False)
print(f"   ✅ Fichier sauvegardé: {output_path}")

# Analyse des résultats
print(f"\n=== RÉSULTATS ===")
print(f"Total de lignes: {len(df_final)}")
print(f"Réf. LMB remplies: {df_final['Réf. LMB'].notna().sum()}/{len(df_final)} ({df_final['Réf. LMB'].notna().sum()/len(df_final)*100:.1f}%)")

# Vérification spécifique des commandes 1020 et 1021
print(f"\n=== VÉRIFICATION COMMANDES 1020/1021 ===")
lines_1020_1021 = df_final[df_final['Réf.WEB'].astype(str).str.contains('1020|1021', na=False)]
if not lines_1020_1021.empty:
    for idx, row in lines_1020_1021.iterrows():
        print(f"  {row['Réf.WEB']}: TTC = {row['TTC']}€, Réf. LMB = {row['Réf. LMB']}")
    
    # Calcul du total
    total_1020_1021 = lines_1020_1021['TTC'].sum()
    print(f"  Total des deux commandes: {total_1020_1021}€")
    print(f"  Attendu: 2067.9 + 15.9 = 2083.8€")
    
    if abs(total_1020_1021 - 2083.8) < 0.1:
        print("  ✅ CORRECTION RÉUSSIE !")
    else:
        print("  ❌ Problème persistant")
else:
    print("  ❌ Commandes 1020/1021 non trouvées")

print(f"\n✅ Génération terminée avec succès !")
