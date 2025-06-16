#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour diagnostiquer le problème des Réf. LMB manquantes
"""

import pandas as pd
from app import process_dataframes_with_normalization
import os

def test_lmb_references_issue():
    """Test pour comprendre pourquoi les Réf. LMB sont manquantes"""
    
    print("=== DIAGNOSTIC: RÉFÉRENCES LMB MANQUANTES ===")
    
    # Créer des données de test avec différents formats de références
    orders_data = {
        'Name': ['#1001', '#1002', 'ORDER-1003', '1004', '#1005'],
        'Fulfilled at': ['2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25', '2024-01-30'],
        'Billing name': ['Client A', 'Client B', 'Client C', 'Client D', 'Client A'],
        'Financial Status': ['paid', 'paid', 'paid', 'paid', 'paid'],
        'Tax 1 Value': [10.0, 20.0, 15.0, 12.0, 8.0],
        'Outstanding Balance': [0.0, 0.0, 0.0, 0.0, 0.0],
        'Payment Method': ['PayPal', 'Virement', 'Carte', 'PayPal', 'Virement'],
        'Total': [110.0, 220.0, 165.0, 132.0, 88.0],
        'Email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'a@test.com'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C', 'Produit D', 'Produit E'],
        'Lineitem price': [100.0, 200.0, 150.0, 120.0, 80.0]
    }
    
    transactions_data = {
        'Order': ['#1001', '#1002', 'ORDER-1003', '1004', '#1005'],
        'Presentment Amount': [110.0, 220.0, 165.0, 132.0, 88.0],
        'Fee': [3.30, 6.60, 4.95, 3.96, 2.64],
        'Net': [106.70, 213.40, 160.05, 128.04, 85.36]
    }
    
    # Journal avec différents formats de Piece (certains correspondent, d'autres non)
    journal_data = {
        'Piece': ['#1001', '#1002', '#1003', 'ORDER-1004', '#1005'],  # Formats variés
        'Référence LMB': ['LMB001', 'LMB002', 'LMB003', 'LMB004', 'LMB005']
    }
    
    # Créer les DataFrames
    df_orders = pd.DataFrame(orders_data)
    df_transactions = pd.DataFrame(transactions_data)
    df_journal = pd.DataFrame(journal_data)
    
    print("ANALYSE DES DONNÉES D'ENTRÉE:")
    print(f"- Commandes: {len(df_orders)} lignes")
    print("  Références commandes:", list(df_orders['Name']))
    
    print(f"- Transactions: {len(df_transactions)} lignes")
    print("  Références transactions:", list(df_transactions['Order']))
    
    print(f"- Journal: {len(df_journal)} lignes")
    print("  Références journal:", list(df_journal['Piece']))
    
    print("\nANALYSE DES CORRESPONDANCES:")
    # Vérifier les correspondances entre commandes et journal
    correspondances = []
    for order in df_orders['Name']:
        if order in df_journal['Piece'].values:
            lmb_ref = df_journal[df_journal['Piece'] == order]['Référence LMB'].iloc[0]
            correspondances.append(f"✅ {order} -> {lmb_ref}")
        else:
            correspondances.append(f"❌ {order} -> PAS DE CORRESPONDANCE")
    
    for corresp in correspondances:
        print(f"  {corresp}")
    
    print(f"\nCorrespondances trouvées: {len([c for c in correspondances if '✅' in c])}/{len(correspondances)}")
    
    # Traiter les données
    print("\n" + "="*50)
    result_df = process_dataframes_with_normalization(df_orders, df_transactions, df_journal)
    print("="*50)
    
    print(f"\nRÉSULTAT FINAL:")
    print(f"- Nombre de lignes: {len(result_df)}")
    
    # Analyser les Réf. LMB dans le résultat
    ref_lmb_col = 'Réf. LMB' if 'Réf. LMB' in result_df.columns else None
    if ref_lmb_col:
        refs_non_vides = result_df[ref_lmb_col].notna() & (result_df[ref_lmb_col] != '')
        print(f"- Réf. LMB non vides: {refs_non_vides.sum()}/{len(result_df)} ({refs_non_vides.sum()/len(result_df)*100:.1f}%)")
        
        print("\nDÉTAIL DES RÉFÉRENCES LMB:")
        for i, row in result_df.iterrows():
            ref_web = row.get('Référence', row.get('Réf.WEB', 'N/A'))
            ref_lmb = row.get(ref_lmb_col, 'VIDE')
            status = "✅" if pd.notna(ref_lmb) and ref_lmb != '' else "❌"
            print(f"  {status} {ref_web} -> {ref_lmb}")
    else:
        print("❌ Colonne 'Réf. LMB' non trouvée dans le résultat!")
        print("Colonnes disponibles:", list(result_df.columns))
    
    return result_df

if __name__ == "__main__":
    try:
        test_lmb_references_issue()
        print("\n🔍 Diagnostic terminé")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
