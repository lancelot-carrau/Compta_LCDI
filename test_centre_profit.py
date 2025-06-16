#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier que la colonne "Centre de profit" contient toujours "lcdi.fr"
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def test_centre_profit_with_real_files():
    """Test avec les vrais fichiers pour vérifier que Centre de profit = lcdi.fr"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
      print("=== Test Centre de profit avec les vrais fichiers ===")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Vérifier la colonne "Centre de profit"
            if 'Centre de profit' in df_result.columns:
                unique_values = df_result['Centre de profit'].unique()
                print(f"\n📊 Valeurs uniques dans 'Centre de profit': {unique_values}")
                
                # Compter les valeurs
                value_counts = df_result['Centre de profit'].value_counts()
                print(f"\n📈 Répartition des valeurs:")
                for value, count in value_counts.items():
                    print(f"  '{value}': {count} lignes ({count/len(df_result)*100:.1f}%)")
                
                # Vérifier que toutes les valeurs sont "lcdi.fr"
                if len(unique_values) == 1 and unique_values[0] == 'lcdi.fr':
                    print(f"\n✅ SUCCÈS: Toutes les {len(df_result)} lignes ont 'Centre de profit' = 'lcdi.fr'")
                    return True
                else:
                    print(f"\n❌ ERREUR: La colonne 'Centre de profit' contient des valeurs incorrectes!")
                    # Afficher les lignes avec des valeurs incorrectes
                    incorrect_rows = df_result[df_result['Centre de profit'] != 'lcdi.fr']
                    if not incorrect_rows.empty:
                        print(f"\n🔍 Lignes avec des valeurs incorrectes ({len(incorrect_rows)} lignes):")
                        print(incorrect_rows[['Centre de profit', 'Réf.WEB', 'Client']].head(10))
                    return False
            else:
                print(f"\n❌ ERREUR: La colonne 'Centre de profit' n'existe pas!")
                print(f"Colonnes disponibles: {list(df_result.columns)}")
                return False
                
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_centre_profit_with_real_files()
    if success:
        print(f"\n🎉 TEST RÉUSSI: La colonne 'Centre de profit' contient bien 'lcdi.fr' partout!")
    else:
        print(f"\n💥 TEST ÉCHOUÉ: Des problèmes ont été détectés!")
