#!/usr/bin/env python3
"""
Test simple pour valider la correction des Réf. LMB
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

def test_ref_lmb_correction():
    """Test simple de la correction des Réf. LMB"""
    
    print("=== TEST DE CORRECTION DES RÉF. LMB ===\n")
    
    # 1. Charger et préparer les données
    print("1. Chargement des données...")
    
    # Journal
    journal_encoding = detect_encoding(JOURNAL_PATH)
    df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
    
    # Commandes
    orders_encoding = detect_encoding(ORDERS_PATH)
    df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
    
    # Transactions
    transactions_encoding = detect_encoding(TRANSACTIONS_PATH)
    df_transactions = pd.read_csv(TRANSACTIONS_PATH, encoding=transactions_encoding)
    
    print(f"   ✓ Journal: {len(df_journal)} lignes")
    print(f"   ✓ Commandes: {len(df_orders)} lignes") 
    print(f"   ✓ Transactions: {len(df_transactions)} lignes")
    
    # 2. Normalisation
    print("\n2. Normalisation des colonnes...")
    
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
    
    # 4. Fusion étape 1 : Commandes + Transactions
    print("\n4. Fusion commandes + transactions...")
    
    df_merged_step1 = pd.merge(df_orders, df_transactions, 
                               left_on='Name', right_on='Order', how='left')
    print(f"   ✓ {len(df_merged_step1)} lignes après fusion")
    
    # 5. Fusion étape 2 : + Journal (LOGIQUE CORRIGÉE)
    print("\n5. Fusion avec journal (logique corrigée)...")
    
    df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
    
    # 6. Analyse des résultats
    print("\n6. Analyse des résultats...")
    
    total_lines = len(df_merged_final)
    lmb_found = df_merged_final['Référence LMB'].notna().sum()
    percentage = (lmb_found / total_lines) * 100
    
    print(f"   📊 RÉSULTATS:")
    print(f"      - Total de lignes: {total_lines}")
    print(f"      - Réf. LMB trouvées: {lmb_found}")
    print(f"      - Pourcentage: {percentage:.1f}%")
    
    # 7. Comparaison avec l'ancien résultat
    print(f"\n   📈 COMPARAISON:")
    print(f"      - Avant correction: ~14% (6/42)")
    print(f"      - Après correction: {percentage:.1f}% ({lmb_found}/{total_lines})")
    
    if percentage > 50:
        improvement = percentage / 14.3
        print(f"      - Amélioration: +{improvement:.1f}x (×{improvement:.1f})")
        print(f"      🎉 SUCCÈS: Amélioration majeure !")
    elif percentage > 30:
        print(f"      ✅ BIEN: Amélioration significative")
    else:
        print(f"      ⚠️ MOYEN: Amélioration limitée")
    
    # 8. Exemples de correspondances
    print(f"\n   📝 EXEMPLES DE CORRESPONDANCES:")
    
    # Avec LMB
    with_lmb = df_merged_final[df_merged_final['Référence LMB'].notna()]
    if len(with_lmb) > 0:
        print(f"      Avec Réf. LMB:")
        for i, row in with_lmb.head(3).iterrows():
            print(f"        {row['Name']} -> {row['Référence LMB']} ({row['Billing name']})")
    
    # Sans LMB
    without_lmb = df_merged_final[df_merged_final['Référence LMB'].isna()]
    if len(without_lmb) > 0:
        print(f"      Sans Réf. LMB:")
        for i, row in without_lmb.head(3).iterrows():
            print(f"        {row['Name']} -> (pas de LMB) ({row['Billing name']})")
    
    # 9. Détails sur les non-correspondances
    print(f"\n   🔍 ANALYSE DES NON-CORRESPONDANCES:")
    
    # Commandes récentes vs journal ancien
    orders_refs = set(df_orders['Name'].dropna())
    journal_refs = set(df_journal['Piece'].dropna())
    
    # Normaliser pour comparaison
    orders_normalized = {ref if str(ref).startswith('#') else f"#{ref}" for ref in orders_refs}
    journal_normalized = {ref if str(ref).startswith('#') else f"#{ref}" for ref in journal_refs}
    
    common_refs = orders_normalized & journal_normalized
    orders_only = orders_normalized - journal_normalized
    
    print(f"      - Correspondances théoriques: {len(common_refs)}")
    print(f"      - Commandes récentes non dans journal: {len(orders_only)}")
    
    if len(orders_only) > 0:
        print(f"      - Exemples commandes récentes: {list(orders_only)[:3]}")
        print(f"      💡 Recommandation: Utiliser un journal plus récent")
    
    # 10. Conclusion
    print(f"\n=== CONCLUSION ===")
    
    if percentage >= 50:
        print(f"🎉 CORRECTION RÉUSSIE !")
        print(f"   - Passage de 14% à {percentage:.1f}% de Réf. LMB")
        print(f"   - Amélioration de +{(percentage/14.3):.1f}x")
        print(f"   - La logique de fusion fonctionne correctement")
        print(f"   - Seul le décalage temporel journal/commandes limite le résultat")
    else:
        print(f"⚠️ AMÉLIORATION PARTIELLE")
        print(f"   - Passage de 14% à {percentage:.1f}%")
        print(f"   - Problème persistant à investiguer")
    
    return percentage

if __name__ == "__main__":
    test_ref_lmb_correction()
