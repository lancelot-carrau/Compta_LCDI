#!/usr/bin/env python3
"""
Test de la logique de fusion améliorée avec gestion des références multiples
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    detect_encoding, normalize_column_names, clean_text_data, 
    improve_journal_matching
)

# Chemins des fichiers
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def test_improved_fusion():
    """Test de la fusion améliorée avec références multiples"""
    
    print("=== TEST DE LA FUSION AMÉLIORÉE AVEC RÉFÉRENCES MULTIPLES ===\n")
    
    # 1. Charger les données
    print("1. Chargement des données...")
    
    journal_encoding = detect_encoding(JOURNAL_PATH)
    df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
    
    orders_encoding = detect_encoding(ORDERS_PATH)
    df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
    
    transactions_encoding = detect_encoding(TRANSACTIONS_PATH)
    df_transactions = pd.read_csv(TRANSACTIONS_PATH, encoding=transactions_encoding)
    
    print(f"   ✓ Journal: {len(df_journal)} lignes")
    print(f"   ✓ Commandes: {len(df_orders)} lignes")
    print(f"   ✓ Transactions: {len(df_transactions)} lignes")
    
    # 2. Normalisation
    print("\n2. Normalisation...")
    
    required_orders_cols = ['Name', 'Billing name', 'Financial Status', 'Outstanding Balance']
    required_transactions_cols = ['Order', 'Presentment Amount']
    required_journal_cols = ['Piece', 'Référence LMB']
    
    df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
    df_transactions = normalize_column_names(df_transactions, required_transactions_cols, "transactions")
    df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
    
    # 3. Nettoyage
    print("\n3. Nettoyage...")
    
    df_orders = clean_text_data(df_orders, ['Name', 'Billing name'])
    df_transactions = clean_text_data(df_transactions, ['Order'])
    df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
    
    # 4. Fusion commandes + transactions
    print("\n4. Fusion commandes + transactions...")
    
    df_merged_step1 = pd.merge(df_orders, df_transactions, 
                               left_on='Name', right_on='Order', how='left')
    print(f"   ✓ {len(df_merged_step1)} lignes après fusion commandes+transactions")
    
    # 5. Test de la fusion améliorée avec journal
    print("\n5. Test de la fusion améliorée avec journal...")
    
    # Avant fusion : compter les références uniques
    orders_refs = df_merged_step1['Name'].nunique()
    journal_refs = df_journal['Piece'].nunique()
    
    print(f"   Références uniques - Commandes: {orders_refs}, Journal: {journal_refs}")
    
    # Tester spécifiquement LCDI-1020 et 1021
    lcdi_1020_orders = df_merged_step1[df_merged_step1['Name'].str.contains('1020', na=False)]
    lcdi_1021_orders = df_merged_step1[df_merged_step1['Name'].str.contains('1021', na=False)]
    
    print(f"   Commandes LCDI-1020: {len(lcdi_1020_orders)}")
    print(f"   Commandes LCDI-1021: {len(lcdi_1021_orders)}")
    
    # Fusion avec la nouvelle logique
    df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
    
    # 6. Analyse des résultats
    print("\n6. Analyse des résultats...")
    
    total_lines = len(df_merged_final)
    lmb_found = df_merged_final['Référence LMB'].notna().sum()
    percentage = (lmb_found / total_lines) * 100
    
    print(f"   📊 RÉSULTATS FINAUX:")
    print(f"      - Total de lignes: {total_lines}")
    print(f"      - Réf. LMB trouvées: {lmb_found}")
    print(f"      - Pourcentage: {percentage:.1f}%")
    
    # 7. Vérification spécifique des cas LCDI-1020/1021
    print(f"\n   🔍 VÉRIFICATION LCDI-1020/1021:")
    
    # Chercher les lignes avec LCDI-1020
    lcdi_1020_results = df_merged_final[df_merged_final['Name'].str.contains('1020', na=False)]
    if len(lcdi_1020_results) > 0:
        for idx, row in lcdi_1020_results.iterrows():
            lmb = row.get('Référence LMB', 'N/A')
            print(f"      - {row['Name']} -> {lmb}")
    
    # Chercher les lignes avec LCDI-1021
    lcdi_1021_results = df_merged_final[df_merged_final['Name'].str.contains('1021', na=False)]
    if len(lcdi_1021_results) > 0:
        for idx, row in lcdi_1021_results.iterrows():
            lmb = row.get('Référence LMB', 'N/A')
            print(f"      - {row['Name']} -> {lmb}")
    
    # 8. Comparaison avec l'ancienne logique
    print(f"\n   📈 COMPARAISON:")
    print(f"      - Logique simple précédente: ~51.7%")
    print(f"      - Logique améliorée actuelle: {percentage:.1f}%")
    
    if percentage > 51.7:
        improvement = percentage - 51.7
        print(f"      - Amélioration: +{improvement:.1f} points")
        print(f"      🎉 SUCCÈS: Les références multiples sont maintenant gérées !")
    elif percentage >= 51.7:
        print(f"      ✅ MAINTENU: Performance équivalente")
    else:
        print(f"      ⚠️ RÉGRESSION: Problème à investiguer")
    
    # 9. Exemples de nouvelles correspondances
    print(f"\n   📝 NOUVELLES CORRESPONDANCES TROUVÉES:")
    with_lmb = df_merged_final[df_merged_final['Référence LMB'].notna()]
    
    if len(with_lmb) > 0:
        # Montrer quelques exemples
        for i, row in with_lmb.head(5).iterrows():
            print(f"      {row['Name']} -> {row['Référence LMB']} ({row.get('Billing name', 'N/A')})")
    
    return percentage

if __name__ == "__main__":
    test_improved_fusion()
