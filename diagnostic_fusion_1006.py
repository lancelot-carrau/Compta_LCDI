#!/usr/bin/env python3
"""Script pour analyser en détail le problème avec la commande #LCDI-1006"""

import pandas as pd
import chardet
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def safe_read_csv(file_path, separator=','):
    """Lit un fichier CSV avec détection automatique de l'encodage"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    
    df = pd.read_csv(file_path, encoding=encoding, sep=separator)
    return df

def analyze_journal_entries():
    """Analyser toutes les entrées du Journal"""
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    df_journal = safe_read_csv(journal_file, separator=';')
    
    print("=== ANALYSE COMPLÈTE DU JOURNAL ===")
    print(f"Nombre total d'entrées: {len(df_journal)}")
    
    # Rechercher toutes les références contenant LCDI-1006
    lcdi_1006_entries = df_journal[df_journal['Référence externe'].str.contains('LCDI-1006', na=False)]
    
    print(f"\n📋 ENTRÉES CONTENANT 'LCDI-1006': {len(lcdi_1006_entries)}")
    for idx, row in lcdi_1006_entries.iterrows():
        print(f"   Ligne {idx}:")
        print(f"   - Référence externe: {row['Référence externe']}")
        print(f"   - Date du document: {row['Date du document']}")
        print(f"   - Référence LMB: {row['Référence LMB']}")
        print(f"   - Montant TTC: {row['Montant du document TTC']}")
        print("   ---")
    
    # Rechercher par référence LMB FAC-L-04299 (trouvée dans le résultat)
    fac_04299_entries = df_journal[df_journal['Référence LMB'].str.contains('FAC-L-04299', na=False)]
    
    print(f"\n📋 ENTRÉES AVEC RÉFÉRENCE LMB 'FAC-L-04299': {len(fac_04299_entries)}")
    for idx, row in fac_04299_entries.iterrows():
        print(f"   Ligne {idx}:")
        print(f"   - Référence externe: {row['Référence externe']}")
        print(f"   - Date du document: {row['Date du document']}")
        print(f"   - Référence LMB: {row['Référence LMB']}")
        print(f"   - Montant TTC: {row['Montant du document TTC']}")
        print("   ---")
    
    # Rechercher toutes les entrées avec date 21/05/2025
    date_21_05_entries = df_journal[df_journal['Date du document'].str.contains('21/05/2025', na=False)]
    
    print(f"\n📋 ENTRÉES AVEC DATE '21/05/2025': {len(date_21_05_entries)}")
    for idx, row in date_21_05_entries.iterrows():
        print(f"   Ligne {idx}:")
        print(f"   - Référence externe: {row['Référence externe']}")
        print(f"   - Date du document: {row['Date du document']}")
        print(f"   - Référence LMB: {row['Référence LMB']}")
        print(f"   - Montant TTC: {row['Montant du document TTC']}")
        print("   ---")

def analyze_fusion_logic():
    """Analyser la logique de fusion pour comprendre le problème"""
    from app import safe_read_csv, normalize_column_names, calculate_invoice_dates
    
    print("\n=== ANALYSE DE LA LOGIQUE DE FUSION ===")
    
    # Charger les fichiers
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    df_orders = safe_read_csv(orders_file, separator=',')
    df_journal = safe_read_csv(journal_file, separator=';')
    
    # Normaliser les colonnes
    df_orders = normalize_column_names(df_orders, 'orders')
    df_journal = normalize_column_names(df_journal, 'journal')
    
    print(f"Commandes chargées: {len(df_orders)}")
    print(f"Journal chargé: {len(df_journal)}")
    
    # Faire une fusion simple pour voir ce qui correspond
    print("\n🔍 FUSION SIMPLE (LEFT JOIN):")
    df_merged = pd.merge(df_orders, df_journal, left_on='Name', right_on='Piece', how='left')
    
    # Rechercher la commande #LCDI-1006 dans le résultat de fusion
    lcdi_1006_merged = df_merged[df_merged['Name'] == '#LCDI-1006']
    
    if len(lcdi_1006_merged) > 0:
        row = lcdi_1006_merged.iloc[0]
        print(f"   ✅ Commande #LCDI-1006 trouvée après fusion:")
        print(f"   - Name: {row['Name']}")
        print(f"   - Fulfilled at: {row['Fulfilled at']}")
        print(f"   - Piece: {row.get('Piece', 'N/A')}")
        print(f"   - Date du document: {row.get('Date du document', 'N/A')}")
        print(f"   - Référence LMB: {row.get('Référence LMB', 'N/A')}")
        
        # Test de calcul de date avec cette ligne
        print(f"\n🧪 TEST DE CALCUL DE DATE:")
        dates = calculate_invoice_dates(lcdi_1006_merged)
        print(f"   - Date calculée: {dates.iloc[0]}")
    else:
        print("   ❌ Commande #LCDI-1006 non trouvée après fusion")

if __name__ == "__main__":
    analyze_journal_entries()
    analyze_fusion_logic()
