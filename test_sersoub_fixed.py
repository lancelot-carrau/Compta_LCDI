#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app import (
    detect_encoding, safe_read_csv, normalize_column_names, 
    validate_required_columns, clean_text_data, format_date_to_french,
    improve_journal_matching, calculate_corrected_amounts
)

def test_sersoub_fixed():
    """Test de la correction pour les commandes de Sersoub Dylan"""
    
    print("=== TEST DE LA CORRECTION SERSOUB DYLAN ===")
    
    # Chemins des fichiers
    orders_file = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    try:
        # Charger les fichiers
        print("1. Chargement des fichiers...")
        df_orders = safe_read_csv(orders_file)
        df_journal = safe_read_csv(journal_file, separator=';')
        
        print(f"   - Commandes: {len(df_orders)} lignes")
        print(f"   - Journal: {len(df_journal)} lignes")
        
        # Filtrer sur les commandes de Sersoub Dylan
        sersoub_orders = df_orders[
            (df_orders['Email'].str.contains('sersoub', case=False, na=False)) |
            (df_orders['Billing Name'].str.contains('Sersoub', case=False, na=False))
        ].copy()
        
        print(f"   - Commandes Sersoub: {len(sersoub_orders)}")
        for _, row in sersoub_orders.iterrows():
            print(f"     - {row['Name']}: {row['Total']}€ (TVA: {row['Taxes']}€)")
        
        # Normaliser les colonnes
        print("\n2. Normalisation des colonnes...")
        required_orders_cols = ['Name', 'Total', 'Taxes']
        required_journal_cols = ['Piece', 'Référence LMB']
        
        sersoub_orders = normalize_column_names(sersoub_orders, required_orders_cols, "commandes")
        df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
        
        # Afficher les colonnes du journal
        print("Colonnes du journal après normalisation:")
        for col in df_journal.columns:
            print(f"   - {col}")
        
        # Test de la fusion avec la nouvelle logique
        print("\n3. Test de la fusion améliorée...")
        df_merged = improve_journal_matching(sersoub_orders, df_journal)
        
        print(f"   - Résultat de la fusion: {len(df_merged)} lignes")
        
        # Examiner les résultats pour Sersoub
        print("\n4. Résultats pour les commandes de Sersoub:")
        for _, row in df_merged.iterrows():
            print(f"\n--- Commande {row['Name']} ---")
            print(f"Total commande: {row['Total']}")
            print(f"Taxes commande: {row['Taxes']}")
            print(f"Référence LMB: {row.get('Référence LMB', 'N/A')}")
            print(f"Montant TTC journal: {row.get('Montant du document TTC', 'N/A')}")
            print(f"Montant HT journal: {row.get('Montant du document HT', 'N/A')}")
        
        # Test du calcul des montants
        print("\n5. Test du calcul des montants corrigés...")
        corrected_amounts = calculate_corrected_amounts(df_merged)
        
        print("\n6. Montants calculés:")
        for i, (_, row) in enumerate(df_merged.iterrows()):
            print(f"\n--- Commande {row['Name']} ---")
            print(f"TTC calculé: {corrected_amounts['TTC'].iloc[i]}")
            print(f"HT calculé: {corrected_amounts['HT'].iloc[i]}")
            print(f"TVA calculée: {corrected_amounts['TVA'].iloc[i]}")
        
        # Vérifier que les montants ne sont plus vides
        ttc_filled = corrected_amounts['TTC'].notna().sum()
        ht_filled = corrected_amounts['HT'].notna().sum()
        tva_filled = corrected_amounts['TVA'].notna().sum()
        total_rows = len(df_merged)
        
        print(f"\n7. Résumé des corrections:")
        print(f"   - TTC rempli: {ttc_filled}/{total_rows} ({ttc_filled/total_rows*100:.1f}%)")
        print(f"   - HT rempli: {ht_filled}/{total_rows} ({ht_filled/total_rows*100:.1f}%)")
        print(f"   - TVA rempli: {tva_filled}/{total_rows} ({tva_filled/total_rows*100:.1f}%)")
        
        if ttc_filled == total_rows:
            print("✅ SUCCÈS: Tous les montants TTC sont maintenant remplis!")
        else:
            print("❌ PROBLÈME: Certains montants TTC sont encore manquants")
            
        return df_merged, corrected_amounts
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    test_sersoub_fixed()
