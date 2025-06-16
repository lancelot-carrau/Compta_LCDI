#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic des valeurs négatives dans la colonne HT
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def analyze_negative_ht():
    """Analyser les valeurs négatives dans la colonne HT"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== DIAGNOSTIC DES VALEURS NÉGATIVES HT ===")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Analyser la colonne HT
            if 'HT' in df_result.columns:
                print(f"\n📊 ANALYSE DE LA COLONNE HT:")
                
                # Statistiques générales
                ht_values = df_result['HT']
                print(f"   - Nombre total de lignes : {len(ht_values)}")
                print(f"   - Valeur minimum HT : {ht_values.min():.2f}")
                print(f"   - Valeur maximum HT : {ht_values.max():.2f}")
                print(f"   - Valeur moyenne HT : {ht_values.mean():.2f}")
                
                # Valeurs négatives
                negative_ht = df_result[df_result['HT'] < 0]
                positive_ht = df_result[df_result['HT'] >= 0]
                
                print(f"\n🔍 RÉPARTITION DES VALEURS:")
                print(f"   - Valeurs négatives : {len(negative_ht)} lignes ({len(negative_ht)/len(df_result)*100:.1f}%)")
                print(f"   - Valeurs positives/nulles : {len(positive_ht)} lignes ({len(positive_ht)/len(df_result)*100:.1f}%)")
                
                if len(negative_ht) > 0:
                    print(f"\n❌ DÉTAIL DES VALEURS NÉGATIVES:")
                    print("   Les 10 premières lignes avec HT négatif:")
                    
                    # Colonnes importantes pour le diagnostic
                    cols_to_show = ['Réf.WEB', 'Client', 'HT', 'TVA', 'TTC']
                    for col in cols_to_show:
                        if col not in negative_ht.columns:
                            print(f"   ⚠️ Colonne manquante: {col}")
                    
                    # Afficher les données
                    available_cols = [col for col in cols_to_show if col in negative_ht.columns]
                    display_data = negative_ht[available_cols].head(10).round(2)
                    
                    print(display_data.to_string(index=False))
                    
                    # Analyse des causes potentielles
                    print(f"\n🔍 ANALYSE DES CAUSES POTENTIELLES:")
                    
                    # Cas où TVA > TTC
                    tva_gt_ttc = negative_ht[negative_ht['TVA'] > negative_ht['TTC']]
                    if len(tva_gt_ttc) > 0:
                        print(f"   - Cas où TVA > TTC : {len(tva_gt_ttc)} lignes")
                        print("     (Cela cause HT = TTC - TVA < 0)")
                    
                    # Cas où TTC est négatif
                    ttc_negative = negative_ht[negative_ht['TTC'] < 0]
                    if len(ttc_negative) > 0:
                        print(f"   - Cas où TTC < 0 : {len(ttc_negative)} lignes")
                        print("     (Probablement des remboursements)")
                    
                    # Cas où TVA est anormalement élevée
                    high_tva = negative_ht[negative_ht['TVA'] > negative_ht['TTC'] * 0.5]
                    if len(high_tva) > 0:
                        print(f"   - Cas où TVA > 50% du TTC : {len(high_tva)} lignes")
                        print("     (TVA anormalement élevée)")
                
                else:
                    print(f"\n✅ Aucune valeur négative détectée dans la colonne HT!")
                
                # Proposer des solutions
                if len(negative_ht) > 0:
                    print(f"\n💡 SOLUTIONS POSSIBLES:")
                    print("   1. Vérifier la cohérence des données sources (TTC et TVA)")
                    print("   2. Appliquer une logique de correction (ex: HT = max(0, TTC - TVA))")
                    print("   3. Utiliser la formule inverse: HT = TTC / (1 + taux_tva)")
                    print("   4. Filtrer les remboursements/annulations si nécessaire")
                
            else:
                print(f"\n❌ ERREUR: La colonne 'HT' n'existe pas!")
                print(f"Colonnes disponibles: {list(df_result.columns)}")
                
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_negative_ht()
