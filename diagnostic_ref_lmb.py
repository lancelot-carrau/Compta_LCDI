#!/usr/bin/env python3
"""
Script de diagnostic pour analyser le problème des Réf. LMB manquantes
"""

import pandas as pd
import os
from pathlib import Path

# Chemins des fichiers utilisés par l'application
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def detect_encoding(file_path):
    """Détecte l'encodage d'un fichier"""
    import chardet
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']

def analyze_reference_matching():
    """Analyse la correspondance entre les références des commandes et du journal"""
    
    print("=== DIAGNOSTIC DES RÉFÉRENCES LMB ===\n")
    
    # 1. Charger les fichiers avec détection d'encodage
    print("1. Chargement des fichiers...")
    
    # Journal
    journal_encoding = detect_encoding(JOURNAL_PATH)
    print(f"   Journal - Encodage détecté: {journal_encoding}")
    df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
    print(f"   Journal - {len(df_journal)} lignes chargées")
    
    # Commandes
    orders_encoding = detect_encoding(ORDERS_PATH)
    print(f"   Commandes - Encodage détecté: {orders_encoding}")
    df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
    print(f"   Commandes - {len(df_orders)} lignes chargées")
    
    print("\n2. Analyse des colonnes de référence...")
      # Colonnes du journal
    print(f"   Journal - Colonnes disponibles: {list(df_journal.columns)}")
    
    # Chercher la colonne de référence (peut être 'Piece' ou 'Référence externe')
    journal_ref_col = None
    if 'Piece' in df_journal.columns:
        journal_ref_col = 'Piece'
        print(f"   Journal - Colonne 'Piece' trouvée")
    elif 'Référence externe' in df_journal.columns:
        journal_ref_col = 'Référence externe'
        print(f"   Journal - Colonne 'Référence externe' trouvée")
    else:
        print("   ❌ Journal - Aucune colonne de référence trouvée ('Piece' ou 'Référence externe')")
        return
    
    journal_refs = df_journal[journal_ref_col].dropna().unique()
    print(f"   Journal - {len(journal_refs)} références uniques dans '{journal_ref_col}'")
    print(f"   Journal - Exemples: {journal_refs[:5].tolist()}")
    
    if 'Référence LMB' in df_journal.columns:
        print(f"   Journal - Colonne 'Référence LMB' trouvée")
        lmb_refs = df_journal['Référence LMB'].dropna().unique()
        print(f"   Journal - {len(lmb_refs)} références LMB uniques")
        print(f"   Journal - Exemples LMB: {lmb_refs[:5].tolist()}")
    else:
        print("   ❌ Journal - Colonne 'Référence LMB' NON TROUVÉE")
        return
    
    # Colonnes des commandes
    print(f"\n   Commandes - Colonnes disponibles: {list(df_orders.columns)}")
    if 'Name' in df_orders.columns:
        print(f"   Commandes - Colonne 'Name' trouvée")
        order_refs = df_orders['Name'].dropna().unique()
        print(f"   Commandes - {len(order_refs)} références uniques dans 'Name'")
        print(f"   Commandes - Exemples: {order_refs[:5].tolist()}")
    else:
        print("   ❌ Commandes - Colonne 'Name' NON TROUVÉE")
        return
    
    print("\n3. Analyse des formats de référence...")
    
    # Analyser les formats
    journal_formats = {}
    for ref in journal_refs:
        if pd.notna(ref):
            ref_str = str(ref)
            if ref_str.startswith('#LCDI-'):
                journal_formats['#LCDI-XXXX'] = journal_formats.get('#LCDI-XXXX', 0) + 1
            elif ref_str.startswith('LCDI-'):
                journal_formats['LCDI-XXXX'] = journal_formats.get('LCDI-XXXX', 0) + 1
            else:
                journal_formats['Autre'] = journal_formats.get('Autre', 0) + 1
    
    print(f"   Journal - Formats de références: {journal_formats}")
    
    order_formats = {}
    for ref in order_refs:
        if pd.notna(ref):
            ref_str = str(ref)
            if ref_str.startswith('#LCDI-'):
                order_formats['#LCDI-XXXX'] = order_formats.get('#LCDI-XXXX', 0) + 1
            elif ref_str.startswith('LCDI-'):
                order_formats['LCDI-XXXX'] = order_formats.get('LCDI-XXXX', 0) + 1
            else:
                order_formats['Autre'] = order_formats.get('Autre', 0) + 1
    
    print(f"   Commandes - Formats de références: {order_formats}")
    
    print("\n4. Test de correspondance directe...")
    
    # Correspondance directe
    direct_matches = set(journal_refs) & set(order_refs)
    print(f"   Correspondances directes: {len(direct_matches)}")
    if direct_matches:
        print(f"   Exemples de correspondances directes: {list(direct_matches)[:5]}")
    
    print("\n5. Test de correspondance avec normalisation...")
      # Normalisation des références
    def normalize_ref(ref):
        if pd.isna(ref):
            return None
        ref_str = str(ref).strip()
        if ref_str.startswith('#'):
            return ref_str
        else:
            return f"#{ref_str}"
    
    journal_normalized = {normalize_ref(ref) for ref in journal_refs if pd.notna(ref)}
    orders_normalized = {normalize_ref(ref) for ref in order_refs if pd.notna(ref)}
    
    normalized_matches = journal_normalized & orders_normalized
    print(f"   Correspondances avec normalisation: {len(normalized_matches)}")
    if normalized_matches:
        print(f"   Exemples de correspondances normalisées: {list(normalized_matches)[:5]}")
    
    print("\n6. Analyse détaillée des non-correspondances...")
    
    # Références dans le journal mais pas dans les commandes
    journal_only = journal_normalized - orders_normalized
    if journal_only:
        print(f"   Références dans le journal SEULEMENT: {len(journal_only)}")
        print(f"   Exemples: {list(journal_only)[:5]}")
    
    # Références dans les commandes mais pas dans le journal
    orders_only = orders_normalized - journal_normalized
    if orders_only:
        print(f"   Références dans les commandes SEULEMENT: {len(orders_only)}")
        print(f"   Exemples: {list(orders_only)[:5]}")
    
    print("\n7. Vérification de la fusion actuelle...")
      # Simuler la logique de fusion actuelle
    df_orders_test = df_orders.copy()
    df_journal_test = df_journal.copy()
    
    # Normaliser comme dans le code actuel
    df_orders_test['Name_normalized'] = df_orders_test['Name'].apply(
        lambda x: x if str(x).startswith('#') else f"#{x}" if pd.notna(x) else None
    )
    df_journal_test['Ref_normalized'] = df_journal_test[journal_ref_col].apply(
        lambda x: x if str(x).startswith('#') else f"#{x}" if pd.notna(x) else None
    )
    
    # Fusion
    df_merged = pd.merge(
        df_orders_test, 
        df_journal_test, 
        left_on='Name_normalized', 
        right_on='Ref_normalized', 
        how='left'
    )
    
    lmb_found = df_merged['Référence LMB'].notna().sum()
    total_orders = len(df_merged)
    
    print(f"   Fusion simulée: {lmb_found}/{total_orders} Réf. LMB trouvées ({lmb_found/total_orders*100:.1f}%)")
      # Montrer quelques exemples de lignes avec et sans LMB
    print("\n   Exemples de lignes AVEC Réf. LMB:")
    with_lmb = df_merged[df_merged['Référence LMB'].notna()][['Name', 'Name_normalized', 'Ref_normalized', 'Référence LMB']].head(3)
    for idx, row in with_lmb.iterrows():
        print(f"     {row['Name']} -> {row['Name_normalized']} = {row['Ref_normalized']} -> {row['Référence LMB']}")
    
    print("\n   Exemples de lignes SANS Réf. LMB:")
    without_lmb = df_merged[df_merged['Référence LMB'].isna()][['Name', 'Name_normalized']].head(5)
    for idx, row in without_lmb.iterrows():
        print(f"     {row['Name']} -> {row['Name_normalized']} (pas de correspondance)")
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Journal: {len(journal_refs)} références, {len(lmb_refs)} Réf. LMB")
    print(f"Commandes: {len(order_refs)} références")
    print(f"Correspondances directes: {len(direct_matches)}")
    print(f"Correspondances normalisées: {len(normalized_matches)}")
    print(f"Fusion finale: {lmb_found}/{total_orders} ({lmb_found/total_orders*100:.1f}%)")
    
    if lmb_found < total_orders * 0.8:  # Si moins de 80% de correspondances
        print(f"\n❌ PROBLÈME DÉTECTÉ: Faible taux de correspondance ({lmb_found/total_orders*100:.1f}%)")
        print("Causes possibles:")
        print("- Formats de références incompatibles")
        print("- Données manquantes dans le journal")
        print("- Périodes différentes entre commandes et journal")
        print("- Erreur dans la logique de normalisation")
    else:
        print(f"\n✅ Taux de correspondance acceptable ({lmb_found/total_orders*100:.1f}%)")

if __name__ == "__main__":
    analyze_reference_matching()
