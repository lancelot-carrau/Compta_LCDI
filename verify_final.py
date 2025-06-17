#!/usr/bin/env python3
"""Vérification finale de #LCDI-1006 et d'autres références"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

# Fichiers de test
orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"

print("=== VÉRIFICATION DES RÉFÉRENCES LMB ===")

# Générer le tableau
df_result = generate_consolidated_billing_table(orders_file, transactions_file, journal_file)

# Vérifier #LCDI-1006
lcdi_1006 = df_result[df_result['Réf.WEB'] == '#LCDI-1006']
if len(lcdi_1006) > 0:
    row = lcdi_1006.iloc[0]
    print(f"\n✅ #LCDI-1006:")
    print(f"   - Date Facture: {row['Date Facture']}")
    print(f"   - Réf. LMB: {row['Réf. LMB']}")
    print(f"   - TTC: {row['TTC']}€")
    
    # Vérification
    if row['Date Facture'] == '19/05/2025' and row['Réf. LMB'] == 'FAC-L-04287':
        print("   ✅ CORRECT!")
    else:
        print("   ❌ PROBLÈME!")

# Compter les références LMB remplies
lmb_filled = df_result['Réf. LMB'].notna().sum()
lmb_total = len(df_result)
print(f"\n📊 STATISTIQUES RÉFÉRENCES LMB:")
print(f"   - Références LMB remplies: {lmb_filled}/{lmb_total} ({lmb_filled/lmb_total*100:.1f}%)")

# Échantillon des références LMB
lmb_samples = df_result[df_result['Réf. LMB'].notna()][['Réf.WEB', 'Réf. LMB', 'Date Facture']].head(10)
print(f"\n📋 ÉCHANTILLON DES RÉFÉRENCES LMB:")
for _, row in lmb_samples.iterrows():
    print(f"   {row['Réf.WEB']:12} → {row['Réf. LMB']:15} (Date: {row['Date Facture']})")

# Vérifier les lignes complètes
complete_lines = df_result[
    (df_result['Réf. LMB'].notna()) & 
    (df_result['TTC'].notna()) & 
    (df_result['Date Facture'].notna())
]
print(f"\n✅ LIGNES COMPLÈTES: {len(complete_lines)}/{lmb_total}")
print("   (avec Réf. LMB + TTC + Date Facture)")
