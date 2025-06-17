#!/usr/bin/env python3
"""
Analyse des commandes doubles/scindées entre journal et commandes
Cas spécifique: LCDI-1020 et LCDI-1021 dans le journal vs commandes séparées
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import detect_encoding, normalize_column_names, clean_text_data

# Chemins des fichiers
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"

def analyze_split_commands():
    """Analyse des commandes scindées/fusionnées"""
    
    print("=== ANALYSE DES COMMANDES SCINDÉES/FUSIONNÉES ===\n")
    
    # 1. Charger les fichiers
    print("1. Chargement des fichiers...")
    
    journal_encoding = detect_encoding(JOURNAL_PATH)
    df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
    
    orders_encoding = detect_encoding(ORDERS_PATH)
    df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
    
    print(f"   Journal: {len(df_journal)} lignes")
    print(f"   Commandes: {len(df_orders)} lignes")
    
    # 2. Normaliser les colonnes
    required_journal_cols = ['Piece', 'Référence LMB']
    required_orders_cols = ['Name']
    
    df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
    df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
    
    # 3. Nettoyer les données
    df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
    df_orders = clean_text_data(df_orders, ['Name'])
    
    # 4. Analyser le cas spécifique LCDI-1020 et 1021
    print("\n2. Analyse du cas LCDI-1020/1021...")
    
    # Chercher dans le journal
    journal_1020_1021 = df_journal[df_journal['Piece'].str.contains('1020|1021', na=False)]
    print(f"   Journal - Lignes avec 1020/1021: {len(journal_1020_1021)}")
    
    if len(journal_1020_1021) > 0:
        print("   Détails journal:")
        for idx, row in journal_1020_1021.iterrows():
            print(f"     {row['Piece']} -> {row['Référence LMB']}")
    
    # Chercher dans les commandes
    orders_1020 = df_orders[df_orders['Name'].str.contains('1020', na=False)]
    orders_1021 = df_orders[df_orders['Name'].str.contains('1021', na=False)]
    
    print(f"   Commandes - Lignes avec 1020: {len(orders_1020)}")
    print(f"   Commandes - Lignes avec 1021: {len(orders_1021)}")
    
    if len(orders_1020) > 0:
        print("   Détails commandes 1020:")
        for idx, row in orders_1020.iterrows():
            print(f"     {row['Name']}")
    
    if len(orders_1021) > 0:
        print("   Détails commandes 1021:")
        for idx, row in orders_1021.iterrows():
            print(f"     {row['Name']}")
    
    # 5. Analyser toutes les références multiples dans le journal
    print("\n3. Analyse des références multiples dans le journal...")
    
    # Rechercher les références qui contiennent plusieurs numéros
    multi_refs = df_journal[df_journal['Piece'].str.contains(' ', na=False)]
    print(f"   Références multiples trouvées: {len(multi_refs)}")
    
    if len(multi_refs) > 0:
        print("   Détails des références multiples:")
        for idx, row in multi_refs.iterrows():
            print(f"     '{row['Piece']}' -> {row['Référence LMB']}")
    
    # 6. Analyser les correspondances manquées
    print("\n4. Analyse des correspondances manquées...")
    
    # Créer des ensembles pour comparaison
    journal_refs = set(df_journal['Piece'].dropna())
    orders_refs = set(df_orders['Name'].dropna())
    
    # Normaliser
    def normalize_ref(ref):
        if pd.isna(ref):
            return None
        ref_str = str(ref).strip()
        return ref_str if ref_str.startswith('#') else f"#{ref_str}"
    
    journal_normalized = {normalize_ref(ref) for ref in journal_refs}
    orders_normalized = {normalize_ref(ref) for ref in orders_refs}
    
    # Correspondances manquées
    missing_in_journal = orders_normalized - journal_normalized
    missing_in_orders = journal_normalized - orders_normalized
    
    print(f"   Commandes sans correspondance journal: {len(missing_in_journal)}")
    print(f"   Exemples: {list(missing_in_journal)[:5]}")
    
    print(f"   Journal sans correspondance commandes: {len(missing_in_orders)}")
    print(f"   Exemples: {list(missing_in_orders)[:5]}")
    
    # 7. Proposer des correspondances multiples
    print("\n5. Recherche de correspondances multiples...")
    
    # Pour chaque référence multiple du journal, chercher les commandes individuelles
    for idx, row in multi_refs.iterrows():
        piece = row['Piece']
        lmb_ref = row['Référence LMB']
        
        print(f"\n   Référence multiple: '{piece}' -> {lmb_ref}")
        
        # Extraire les numéros individuels
        import re
        numbers = re.findall(r'LCDI-(\d+)', piece)
        print(f"   Numéros extraits: {numbers}")
        
        # Chercher les commandes correspondantes
        matching_orders = []
        for num in numbers:
            pattern = f"LCDI-{num}"
            matches = df_orders[df_orders['Name'].str.contains(pattern, na=False)]
            if len(matches) > 0:
                matching_orders.extend(matches['Name'].tolist())
        
        if matching_orders:
            print(f"   Commandes correspondantes trouvées: {matching_orders}")
            print(f"   💡 Suggestion: Mapper {matching_orders} -> {lmb_ref}")
    
    return multi_refs, missing_in_journal, missing_in_orders

if __name__ == "__main__":
    analyze_split_commands()
