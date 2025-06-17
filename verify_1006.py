#!/usr/bin/env python3
"""Test spécifique pour vérifier la date finale de #LCDI-1006"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

# Fichiers de test
orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"

print("=== VÉRIFICATION FINALE DE #LCDI-1006 ===")

# Générer le tableau
df_result = generate_consolidated_billing_table(orders_file, transactions_file, journal_file)

# Rechercher #LCDI-1006
lcdi_1006 = df_result[df_result['Réf.WEB'] == '#LCDI-1006']

if len(lcdi_1006) > 0:
    row = lcdi_1006.iloc[0]
    print(f"\n✅ RÉSULTAT FINAL POUR #LCDI-1006:")
    print(f"   - Date Facture: {row['Date Facture']}")
    print(f"   - Réf. LMB: {row['Réf. LMB']}")
    print(f"   - TTC: {row['TTC']}€")
    print(f"   - Client: {row['Client']}")
    
    # Vérification
    if row['Date Facture'] == '19/05/2025':
        print("✅ SUCCESS: Date correcte!")
    else:
        print(f"❌ ÉCHEC: Date incorrecte. Attendu: 19/05/2025, Obtenu: {row['Date Facture']}")
    
    if row['Réf. LMB'] == 'FAC-L-04287':
        print("✅ SUCCESS: Référence LMB correcte!")
    else:
        print(f"❌ ÉCHEC: Référence LMB incorrecte. Attendu: FAC-L-04287, Obtenu: {row['Réf. LMB']}")
else:
    print("❌ ÉCHEC: Commande #LCDI-1006 non trouvée")
