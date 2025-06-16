#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic des montants HT négatifs et données TTC manquantes
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def diagnostic_montants():
    """Diagnostic des problèmes de montants TTC/HT/TVA"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== DIAGNOSTIC DES MONTANTS ===")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Analyser les colonnes de montants
            print("\n📊 ANALYSE DES MONTANTS:")
            
            # TTC (Presentment Amount)
            ttc_zero = (df_result['TTC'] == 0).sum()
            ttc_null = df_result['TTC'].isna().sum()
            ttc_positif = (df_result['TTC'] > 0).sum()
            ttc_negatif = (df_result['TTC'] < 0).sum()
            
            print(f"\n🔢 TTC (Presentment Amount):")
            print(f"  - Valeurs positives: {ttc_positif}")
            print(f"  - Valeurs zéro: {ttc_zero}")
            print(f"  - Valeurs négatives: {ttc_negatif}")
            print(f"  - Valeurs nulles: {ttc_null}")
            
            # TVA (Tax 1 Value)
            tva_zero = (df_result['TVA'] == 0).sum()
            tva_null = df_result['TVA'].isna().sum()
            tva_positif = (df_result['TVA'] > 0).sum()
            tva_negatif = (df_result['TVA'] < 0).sum()
            
            print(f"\n💰 TVA (Tax 1 Value):")
            print(f"  - Valeurs positives: {tva_positif}")
            print(f"  - Valeurs zéro: {tva_zero}")
            print(f"  - Valeurs négatives: {tva_negatif}")
            print(f"  - Valeurs nulles: {tva_null}")
            
            # HT (calculé)
            ht_zero = (df_result['HT'] == 0).sum()
            ht_null = df_result['HT'].isna().sum()
            ht_positif = (df_result['HT'] > 0).sum()
            ht_negatif = (df_result['HT'] < 0).sum()
            
            print(f"\n🏷️ HT (TTC - TVA):")
            print(f"  - Valeurs positives: {ht_positif}")
            print(f"  - Valeurs zéro: {ht_zero}")
            print(f"  - Valeurs négatives: {ht_negatif} ⚠️")
            print(f"  - Valeurs nulles: {ht_null}")
            
            # Cas problématiques
            print(f"\n🚨 CAS PROBLÉMATIQUES:")
            
            # Cas 1: HT négatif
            if ht_negatif > 0:
                print(f"\n❌ {ht_negatif} lignes avec HT négatif:")
                ht_negatif_rows = df_result[df_result['HT'] < 0]
                for idx, row in ht_negatif_rows.head(10).iterrows():
                    print(f"  Ligne {idx}: TTC={row['TTC']}, TVA={row['TVA']}, HT={row['HT']}, Client={row['Client']}, Réf={row['Réf.WEB']}")
            
            # Cas 2: TVA sans TTC
            tva_sans_ttc = df_result[(df_result['TVA'] > 0) & (df_result['TTC'] == 0)]
            if not tva_sans_ttc.empty:
                print(f"\n❌ {len(tva_sans_ttc)} lignes avec TVA mais TTC=0:")
                for idx, row in tva_sans_ttc.head(10).iterrows():
                    print(f"  Ligne {idx}: TTC={row['TTC']}, TVA={row['TVA']}, HT={row['HT']}, Client={row['Client']}, Réf={row['Réf.WEB']}")
            
            # Cas 3: TTC sans TVA (normal pour certains pays)
            ttc_sans_tva = df_result[(df_result['TTC'] > 0) & (df_result['TVA'] == 0)]
            if not ttc_sans_tva.empty:
                print(f"\n📝 {len(ttc_sans_tva)} lignes avec TTC mais TVA=0 (peut être normal):")
                for idx, row in ttc_sans_tva.head(5).iterrows():
                    print(f"  Ligne {idx}: TTC={row['TTC']}, TVA={row['TVA']}, HT={row['HT']}, Client={row['Client']}, Réf={row['Réf.WEB']}")
            
            return True
                
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = diagnostic_montants()
    if success:
        print(f"\n🔍 DIAGNOSTIC TERMINÉ")
    else:
        print(f"\n💥 DIAGNOSTIC ÉCHOUÉ")
