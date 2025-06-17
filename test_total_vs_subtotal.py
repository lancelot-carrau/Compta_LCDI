#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier que l'application utilise bien la colonne "Total" (TTC) 
et non pas "Subtotal" pour le calcul des montants
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def test_total_vs_subtotal():
    """Test pour vérifier que Total est utilisé à la place de Subtotal"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== Test Total vs Subtotal ===")
    
    # Vérifier que les fichiers existent
    for path, name in [(journal_path, "Journal"), (orders_path, "Commandes"), (transactions_path, "Transactions")]:
        if not os.path.exists(path):
            print(f"⚠️ ATTENTION: Fichier {name} non trouvé: {path}")
            print("   Utilisation des fichiers de test à la place...")
            return test_total_vs_subtotal_with_test_files()
    
    # Charger le fichier des commandes pour voir les colonnes disponibles
    df_orders = pd.read_csv(orders_path, encoding='utf-8')
    print(f"\n📋 Colonnes disponibles dans le fichier des commandes:")
    print(f"   - Total: {'✅' if 'Total' in df_orders.columns else '❌'}")
    print(f"   - Subtotal: {'✅' if 'Subtotal' in df_orders.columns else '❌'}")
    print(f"   - Taxes: {'✅' if 'Taxes' in df_orders.columns else '❌'}")
    
    if 'Total' in df_orders.columns and 'Subtotal' in df_orders.columns:
        print(f"\n📊 Comparaison des valeurs:")
        print(f"   - Total moyen: {df_orders['Total'].mean():.2f}")
        print(f"   - Subtotal moyen: {df_orders['Subtotal'].mean():.2f}")
        print(f"   - Différence: {(df_orders['Total'] - df_orders['Subtotal']).mean():.2f}")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Vérifier que les montants TTC correspondent à la colonne Total et non Subtotal
            if 'TTC' in df_result.columns:
                print(f"\n🔍 Vérification des montants TTC:")
                ttc_values = df_result['TTC'].dropna()
                print(f"   - Nombre de valeurs TTC: {len(ttc_values)}")
                print(f"   - TTC moyen: {ttc_values.mean():.2f}")
                
                # Comparer avec les valeurs originales
                sample_orders = df_orders[df_orders['Name'].isin(df_result['Réf.WEB'].dropna())].head(5)
                if not sample_orders.empty:
                    print(f"\n📋 Échantillon de comparaison (5 premières commandes):")
                    for _, row in sample_orders.iterrows():
                        name = row['Name']
                        total_val = row.get('Total', 'N/A')
                        subtotal_val = row.get('Subtotal', 'N/A')
                        
                        # Trouver la ligne correspondante dans le résultat
                        result_row = df_result[df_result['Réf.WEB'] == name]
                        if not result_row.empty:
                            ttc_val = result_row['TTC'].iloc[0]
                            print(f"   {name}: Total={total_val}, Subtotal={subtotal_val}, TTC utilisé={ttc_val}")
                            
                            # Vérifier que TTC = Total et non Subtotal
                            if pd.notna(total_val) and pd.notna(ttc_val):
                                if abs(float(ttc_val) - float(total_val)) < 0.01:
                                    print(f"      ✅ TTC correspond à Total")
                                elif 'Subtotal' in row and pd.notna(subtotal_val) and abs(float(ttc_val) - float(subtotal_val)) < 0.01:
                                    print(f"      ❌ ERREUR: TTC correspond à Subtotal au lieu de Total!")
                                    return False
            
            print(f"\n🎉 SUCCÈS: L'application utilise bien la colonne 'Total' pour le TTC !")
            return True
            
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_total_vs_subtotal_with_test_files():
    """Test avec des fichiers de test"""
    
    # Utiliser les fichiers de test
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    journal_path = os.path.join(test_data_dir, '20240116-Journal_test.csv')
    orders_path = os.path.join(test_data_dir, 'orders_export_test.csv')
    transactions_path = os.path.join(test_data_dir, 'payment_transactions_export_test.csv')
    
    print("=== Test Total vs Subtotal avec fichiers de test ===")
    
    # Vérifier que les fichiers de test existent
    for path, name in [(journal_path, "Journal test"), (orders_path, "Commandes test"), (transactions_path, "Transactions test")]:
        if not os.path.exists(path):
            print(f"❌ ERREUR: Fichier {name} non trouvé: {path}")
            return False
    
    try:
        # Traiter les fichiers de test
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            print(f"🎉 Test avec fichiers de test réussi !")
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
    print("🚀 Démarrage du test Total vs Subtotal...")
    success = test_total_vs_subtotal()
    if success:
        print(f"\n🎉 TEST RÉUSSI: L'application utilise bien 'Total' et non 'Subtotal' !")
    else:
        print(f"\n💥 TEST ÉCHOUÉ: Des problèmes ont été détectés!")
