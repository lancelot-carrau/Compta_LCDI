#!/usr/bin/env python3
"""
Analyse complète des références multiples et vérification des prix
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

def analyze_all_multiple_refs_and_prices():
    """Analyse complète des références multiples et problèmes de prix"""
    
    print("=== ANALYSE COMPLÈTE DES RÉFÉRENCES MULTIPLES ET PRIX ===\n")
    
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
    required_orders_cols = ['Name', 'Total', 'Taxes', 'Billing name']
    
    df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
    df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
    
    # 3. Nettoyer les données
    df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
    df_orders = clean_text_data(df_orders, ['Name', 'Billing name'])
    
    # 4. IDENTIFIER TOUTES LES RÉFÉRENCES MULTIPLES
    print("\n2. Recherche de toutes les références multiples...")
    
    # Chercher toutes les références qui contiennent des espaces
    multi_refs = df_journal[df_journal['Piece'].str.contains(' ', na=False)]
    
    print(f"   Total références multiples trouvées: {len(multi_refs)}")
    
    if len(multi_refs) > 0:
        print("\n   📋 LISTE COMPLÈTE DES RÉFÉRENCES MULTIPLES:")
        for idx, row in multi_refs.iterrows():
            piece = row['Piece']
            lmb_ref = row['Référence LMB']
            
            # Extraire les numéros individuels
            import re
            numbers = re.findall(r'LCDI-(\d+)', piece)
            
            # Colonnes prix du journal
            ttc_journal = row.get('Montant du document TTC', 'N/A')
            ht_journal = row.get('Montant du document HT', 'N/A')
            
            print(f"     - '{piece}' -> {lmb_ref}")
            print(f"       Numéros extraits: {numbers}")
            print(f"       Prix journal: TTC={ttc_journal}, HT={ht_journal}")
            
            # Chercher les commandes correspondantes et leurs prix
            for num in numbers:
                pattern = f"LCDI-{num}"
                matches = df_orders[df_orders['Name'].str.contains(pattern, na=False)]
                
                if len(matches) > 0:
                    for match_idx, match_row in matches.iterrows():
                        order_name = match_row['Name']
                        order_total = match_row.get('Total', 'N/A')
                        order_taxes = match_row.get('Taxes', 'N/A')
                        order_client = match_row.get('Billing name', 'N/A')
                        
                        print(f"         → Commande {order_name}: TTC={order_total}, TVA={order_taxes}, Client={order_client}")
                else:
                    print(f"         → Aucune commande trouvée pour LCDI-{num}")
            
            print()  # Ligne vide pour séparation
    
    # 5. ANALYSE SPÉCIFIQUE DES PRIX POUR 1020/1021
    print("\n3. Analyse détaillée des prix pour LCDI-1020/1021...")
    
    # Prix dans le journal
    journal_1020_1021 = df_journal[df_journal['Piece'].str.contains('1020.*1021|1021.*1020', na=False)]
    
    if len(journal_1020_1021) > 0:
        print("   📊 PRIX DANS LE JOURNAL:")
        total_journal_ttc = 0
        total_journal_ht = 0
        
        for idx, row in journal_1020_1021.iterrows():
            ttc = row.get('Montant du document TTC', 0)
            ht = row.get('Montant du document HT', 0)
            
            # Convertir les montants français (virgule -> point)
            if isinstance(ttc, str):
                ttc = float(ttc.replace(',', '.')) if ttc.replace(',', '.').replace('.', '').isdigit() else 0
            if isinstance(ht, str):
                ht = float(ht.replace(',', '.')) if ht.replace(',', '.').replace('.', '').isdigit() else 0
                
            total_journal_ttc += ttc
            total_journal_ht += ht
            
            print(f"     Ligne journal: TTC={ttc}€, HT={ht}€, LMB={row['Référence LMB']}")
        
        print(f"   TOTAL JOURNAL: TTC={total_journal_ttc}€, HT={total_journal_ht}€")
    
    # Prix dans les commandes
    print("\n   📊 PRIX DANS LES COMMANDES:")
    
    orders_1020 = df_orders[df_orders['Name'].str.contains('1020', na=False)]
    orders_1021 = df_orders[df_orders['Name'].str.contains('1021', na=False)]
    
    total_orders_ttc = 0
    total_orders_taxes = 0
    
    for orders, label in [(orders_1020, "1020"), (orders_1021, "1021")]:
        if len(orders) > 0:
            print(f"     Commande LCDI-{label}:")
            for idx, row in orders.iterrows():
                ttc = pd.to_numeric(row.get('Total', 0), errors='coerce') or 0
                taxes = pd.to_numeric(row.get('Taxes', 0), errors='coerce') or 0
                ht = ttc - taxes
                
                total_orders_ttc += ttc
                total_orders_taxes += taxes
                
                client = row.get('Billing name', 'N/A')
                print(f"       TTC={ttc}€, TVA={taxes}€, HT={ht}€, Client={client}")
    
    total_orders_ht = total_orders_ttc - total_orders_taxes
    print(f"   TOTAL COMMANDES: TTC={total_orders_ttc}€, TVA={total_orders_taxes}€, HT={total_orders_ht}€")
    
    # 6. COMPARAISON ET PROBLÈME IDENTIFIÉ
    print("\n4. Comparaison et identification du problème...")
    
    if 'total_journal_ttc' in locals() and 'total_orders_ttc' in locals():
        print(f"   📈 COMPARAISON:")
        print(f"     Journal total: {total_journal_ttc}€")
        print(f"     Commandes total: {total_orders_ttc}€")
        print(f"     Différence: {abs(total_journal_ttc - total_orders_ttc)}€")
        
        if abs(total_journal_ttc - total_orders_ttc) > 0.01:
            print(f"\n   ❌ PROBLÈME IDENTIFIÉ:")
            print(f"     Les montants du journal et des commandes ne correspondent pas !")
            print(f"     Causes possibles:")
            print(f"     1. Le journal contient le TOTAL des deux commandes")
            print(f"     2. Les commandes sont comptées séparément")
            print(f"     3. Notre logique applique le même montant journal aux deux commandes")
            print(f"     → Résultat: DOUBLAGE des montants !")
        else:
            print(f"   ✅ Les montants correspondent")
    
    # 7. SOLUTIONS PROPOSÉES
    print("\n5. Solutions proposées...")
    
    print(f"   💡 SOLUTIONS POUR CORRIGER LE PROBLÈME:")
    print(f"     1. RÉPARTITION PROPORTIONNELLE:")
    print(f"        - Calculer le poids de chaque commande individuelle")
    print(f"        - Répartir le montant journal proportionnellement")
    print(f"     2. UTILISATION DES MONTANTS COMMANDES:")
    print(f"        - Utiliser les montants individuels des commandes")
    print(f"        - Ne pas écraser avec les montants journal pour les refs multiples")
    print(f"     3. DÉTECTION ET MARQUAGE:")
    print(f"        - Marquer les lignes issues de références multiples")
    print(f"        - Appliquer une logique différente")
    
    # 8. RECHERCHE D'AUTRES CAS SIMILAIRES
    print("\n6. Recherche d'autres patterns problématiques...")
    
    # Chercher d'autres patterns de références multiples
    other_patterns = []
    
    for idx, row in df_journal.iterrows():
        piece = str(row['Piece'])
        if ' ' in piece and 'LCDI' in piece:
            # Compter le nombre de références LCDI
            lcdi_count = len(re.findall(r'LCDI-\d+', piece))
            if lcdi_count > 1:
                other_patterns.append({
                    'piece': piece,
                    'count': lcdi_count,
                    'lmb': row['Référence LMB']
                })
    
    if other_patterns:
        print(f"   🔍 AUTRES PATTERNS TROUVÉS:")
        for pattern in other_patterns:
            print(f"     - '{pattern['piece']}' ({pattern['count']} références) -> {pattern['lmb']}")
    else:
        print(f"   ✅ Aucun autre pattern problématique trouvé")
    
    return multi_refs, other_patterns

if __name__ == "__main__":
    analyze_all_multiple_refs_and_prices()
