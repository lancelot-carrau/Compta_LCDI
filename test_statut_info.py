#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la nouvelle colonne "Statut Info" avec les indicateurs d'informations manquantes
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def test_statut_info():
    """Test de la colonne Statut Info avec les indicateurs"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== TEST DES INDICATEURS D'INFORMATIONS MANQUANTES ===")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
              # Vérifier si la colonne "Statut" existe
            if 'Statut' in df_result.columns:
                print(f"\n📊 COLONNE 'Statut' trouvée !")
                
                # Analyser les différents statuts
                statut_counts = df_result['Statut'].value_counts()
                print(f"\n📈 RÉPARTITION DES STATUTS:")
                for statut, count in statut_counts.items():
                    print(f"  '{statut}': {count} lignes")
                
                # Afficher quelques exemples de chaque type
                print(f"\n🔍 EXEMPLES DE CHAQUE TYPE:")
                
                for statut in statut_counts.index:  # Tous les statuts
                    examples = df_result[df_result['Statut'] == statut]
                    print(f"\n▶️ Statut: '{statut}' ({len(examples)} lignes)")
                    for idx, row in examples.head(5).iterrows():
                        lmb_display = row['Réf. LMB'] if row['Réf. LMB'] != '' else '[VIDE]'
                        date_display = row['Date Facture'] if row['Date Facture'] != '' else '[VIDE]'
                        print(f"  - Ligne {idx}: Réf={row['Réf.WEB']}, Client={row['Client'][:25]}, TTC={row['TTC']}, LMB={lmb_display}, Date={date_display}")
                
                # Afficher un exemple détaillé de chaque statut
                print(f"\n🔧 EXEMPLES DÉTAILLÉS:")
                for statut in statut_counts.index:
                    example = df_result[df_result['Statut'] == statut].iloc[0]
                    print(f"\n� Exemple {statut}:")
                    print(f"  Réf.WEB: {example['Réf.WEB']}")
                    print(f"  Client: {example['Client']}")
                    print(f"  Réf. LMB: '{example['Réf. LMB']}' {'[VIDE]' if example['Réf. LMB'] == '' else ''}")
                    print(f"  Date Facture: '{example['Date Facture']}' {'[VIDE]' if example['Date Facture'] == '' else ''}")
                    print(f"  TTC: {example['TTC']}")
                    print(f"  Statut: {example['Statut']}")
                
                return True
            else:
                print(f"\n❌ ERREUR: La colonne 'Statut' n'existe pas!")
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
    success = test_statut_info()
    if success:
        print(f"\n🎉 TEST RÉUSSI: Les indicateurs d'informations manquantes fonctionnent!")
    else:
        print(f"\n💥 TEST ÉCHOUÉ: Des problèmes ont été détectés!")
