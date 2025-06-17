#!/usr/bin/env python3
"""
Test de la fusion améliorée pour les Réf. LMB
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer les fonctions de app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    detect_encoding, normalize_column_names, clean_text_data, 
    improve_journal_matching
)

# Chemins des fichiers
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"

def test_fusion_logique():
    """Test de la logique de fusion améliorée"""
    
    print("=== TEST DE LA FUSION AMÉLIORÉE ===\n")
    
    # 1. Charger les fichiers
    print("1. Chargement des fichiers...")
    
    # Journal
    journal_encoding = detect_encoding(JOURNAL_PATH)
    df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
    print(f"   Journal chargé: {len(df_journal)} lignes")
    
    # Commandes  
    orders_encoding = detect_encoding(ORDERS_PATH)
    df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
    print(f"   Commandes chargées: {len(df_orders)} lignes")
    
    # 2. Normaliser les colonnes
    print("\n2. Normalisation des colonnes...")
    
    required_orders_cols = ['Name', 'Billing name', 'Financial Status', 'Fulfilled at', 
                           'Total', 'Taxes', 'Outstanding Balance', 'Payment Method']
    required_journal_cols = ['Piece', 'Référence LMB']
    
    df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
    df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
    
    # 3. Nettoyer les données textuelles
    print("\n3. Nettoyage des données...")
    
    df_orders = clean_text_data(df_orders, ['Name', 'Billing name'])
    df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
    
    # 4. Statistiques avant fusion
    print("\n4. Statistiques avant fusion...")
    print(f"   Commandes uniques: {df_orders['Name'].nunique()}")
    print(f"   Références journal uniques: {df_journal['Piece'].nunique()}")
    print(f"   Réf. LMB dans journal: {df_journal['Référence LMB'].notna().sum()}")
    
    # 5. Test de la fusion améliorée
    print("\n5. Test de la fusion améliorée...")
    
    df_merged = improve_journal_matching(df_orders, df_journal)
    
    # 6. Analyse des résultats
    print("\n6. Analyse des résultats...")
    
    total_commandes = len(df_merged)
    lmb_trouvees = df_merged['Référence LMB'].notna().sum()
    pourcentage = (lmb_trouvees / total_commandes) * 100
    
    print(f"   Total de commandes: {total_commandes}")
    print(f"   Réf. LMB trouvées: {lmb_trouvees}")
    print(f"   Pourcentage de réussite: {pourcentage:.1f}%")
    
    # 7. Exemples de correspondances
    print("\n7. Exemples de correspondances réussies:")
    with_lmb = df_merged[df_merged['Référence LMB'].notna()][['Name', 'Name_normalized', 'Piece_normalized', 'Référence LMB']].head(5)
    for idx, row in with_lmb.iterrows():
        print(f"   {row['Name']} -> {row['Name_normalized']} = {row['Piece_normalized']} -> {row['Référence LMB']}")
    
    # 8. Exemples de non-correspondances
    print("\n8. Exemples de non-correspondances:")
    without_lmb = df_merged[df_merged['Référence LMB'].isna()][['Name', 'Name_normalized']].head(5)
    for idx, row in without_lmb.iterrows():
        print(f"   {row['Name']} -> {row['Name_normalized']} (pas de correspondance)")
    
    # 9. Analyse détaillée des références
    print("\n9. Analyse des références:")
    journal_refs = set(df_journal['Piece'].dropna())
    orders_refs = set(df_orders['Name'].dropna())
    
    # Normaliser pour comparaison
    journal_normalized = {ref if str(ref).startswith('#') else f"#{ref}" for ref in journal_refs}
    orders_normalized = {ref if str(ref).startswith('#') else f"#{ref}" for ref in orders_refs}
    
    correspondances_possibles = journal_normalized & orders_normalized
    print(f"   Correspondances théoriques possibles: {len(correspondances_possibles)}")
    print(f"   Correspondances réelles obtenues: {lmb_trouvees}")
    
    # 10. Recommandations
    print(f"\n=== RÉSUMÉ ===")
    if pourcentage >= 80:
        print(f"✅ SUCCÈS: {pourcentage:.1f}% de correspondances (≥80%)")
    elif pourcentage >= 50:
        print(f"⚠️ MOYEN: {pourcentage:.1f}% de correspondances (50-80%)")
        print("   Vérifier la synchronisation des données journal/commandes")
    else:
        print(f"❌ ÉCHEC: {pourcentage:.1f}% de correspondances (<50%)")
        print("   Problème majeur dans les données ou la logique")
    
    return pourcentage

if __name__ == "__main__":
    test_fusion_logique()
