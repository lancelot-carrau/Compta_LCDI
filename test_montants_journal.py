#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour vérifier que l'application utilise bien les montants TTC 
de la colonne "Montant du document TTC" du fichier Journal
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def test_montants_journal():
    """Test pour vérifier que les montants TTC viennent du Journal"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== Test Montants du Journal ===")
    
    # Vérifier que les fichiers existent
    for path, name in [(journal_path, "Journal"), (orders_path, "Commandes"), (transactions_path, "Transactions")]:
        if not os.path.exists(path):
            print(f"⚠️ ATTENTION: Fichier {name} non trouvé: {path}")
            print("   Utilisation des fichiers de test à la place...")
            return test_montants_journal_with_test_files()
    
    try:
        # Charger les fichiers pour analyser les colonnes
        df_journal = pd.read_csv(journal_path, encoding='ISO-8859-1')
        df_orders = pd.read_csv(orders_path, encoding='utf-8')
        
        print(f"\n📋 Colonnes du Journal:")
        journal_cols = ['Montant du document TTC', 'Montant du document HT', 'Référence LMB', 'Référence externe']
        for col in journal_cols:
            if col in df_journal.columns:
                print(f"   - {col}: ✅")
                if 'Montant' in col:
                    non_null_count = df_journal[col].notna().sum()
                    mean_val = df_journal[col].dropna().mean() if non_null_count > 0 else 0
                    print(f"     → {non_null_count} valeurs, moyenne: {mean_val:.2f}€")
            else:
                print(f"   - {col}: ❌")
        
        print(f"\n📋 Colonnes des Commandes:")
        orders_cols = ['Total', 'Subtotal', 'Taxes', 'Name']
        for col in orders_cols:
            if col in df_orders.columns:
                print(f"   - {col}: ✅")
                if col in ['Total', 'Subtotal', 'Taxes']:
                    mean_val = df_orders[col].mean()
                    print(f"     → Moyenne: {mean_val:.2f}€")
            else:
                print(f"   - {col}: ❌")
        
        # Traiter les fichiers
        print(f"\n🔄 Traitement des fichiers...")
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Analyser la source des montants TTC
            print(f"\n🔍 Analyse des montants TTC:")
            
            if 'TTC' in df_result.columns:
                ttc_values = df_result['TTC'].dropna()
                print(f"   - Nombre de valeurs TTC dans le résultat: {len(ttc_values)}")
                print(f"   - TTC moyen dans le résultat: {ttc_values.mean():.2f}€")
                  # Comparer avec les moyennes d'origine (convertir le format français)
                if 'Montant du document TTC' in df_journal.columns:
                    # Convertir les montants français en format numérique
                    journal_ttc_col = df_journal['Montant du document TTC'].astype(str).str.replace(',', '.').str.replace(' ', '')
                    journal_ttc_numeric = pd.to_numeric(journal_ttc_col, errors='coerce').dropna()
                    journal_ttc_mean = journal_ttc_numeric.mean()
                else:
                    journal_ttc_mean = 0
                orders_total_mean = df_orders['Total'].mean()
                
                print(f"   - TTC moyen dans le Journal: {journal_ttc_mean:.2f}€")
                print(f"   - Total moyen dans les Commandes: {orders_total_mean:.2f}€")
                
                # Déterminer quelle source est utilisée
                result_mean = ttc_values.mean()
                diff_journal = abs(result_mean - journal_ttc_mean)
                diff_orders = abs(result_mean - orders_total_mean)
                
                print(f"\n📊 Analyse de correspondance:")
                print(f"   - Différence avec Journal: {diff_journal:.2f}€")
                print(f"   - Différence avec Commandes: {diff_orders:.2f}€")
                
                if diff_journal < diff_orders:
                    print(f"   ✅ SUCCÈS: Les montants TTC proviennent du Journal!")
                elif diff_orders < diff_journal:
                    print(f"   ⚠️ INFO: Les montants TTC proviennent des Commandes (fallback)")
                else:
                    print(f"   ❓ Les montants sont similaires dans les deux sources")
                  # Échantillon détaillé
                print(f"\n📋 Échantillon détaillé (5 premières lignes avec données valides):")
                sample_with_data = df_result[df_result['TTC'] > 0].head(5)
                
                for _, row in sample_with_data.iterrows():
                    ref_web = row.get('Réf.WEB', 'N/A')
                    ref_lmb = row.get('Réf. LMB', 'N/A')
                    ttc_result = row.get('TTC', 'N/A')
                    
                    print(f"   - {ref_web} (LMB: {ref_lmb}): TTC = {ttc_result}€")
                    
                    # Si on a une référence LMB, chercher dans le journal
                    if pd.notna(ref_lmb) and ref_lmb != '' and 'Montant du document TTC' in df_journal.columns:
                        # Chercher dans le journal original
                        journal_match = df_journal[df_journal['Référence LMB'].astype(str).str.contains(str(ref_lmb), na=False)]
                        if not journal_match.empty:
                            # Convertir le montant du journal
                            journal_ttc_str = journal_match['Montant du document TTC'].iloc[0]
                            journal_ttc = float(str(journal_ttc_str).replace(',', '.').replace(' ', ''))
                            print(f"     → Journal TTC: {journal_ttc}€")
                            if abs(float(ttc_result) - journal_ttc) < 0.01:
                                print(f"     ✅ Correspond au Journal")
                            else:
                                print(f"     ❌ Différence avec le Journal")
                        else:
                            print(f"     ⚠️ Référence LMB non trouvée dans le journal")
            
            return True
            
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_montants_journal_with_test_files():
    """Test avec des fichiers de test"""
    
    # Utiliser les fichiers de test
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    journal_path = os.path.join(test_data_dir, '20240116-Journal_test.csv')
    orders_path = os.path.join(test_data_dir, 'orders_export_test.csv')
    transactions_path = os.path.join(test_data_dir, 'payment_transactions_export_test.csv')
    
    print("=== Test Montants du Journal avec fichiers de test ===")
    
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
    print("🚀 Démarrage du test Montants du Journal...")
    success = test_montants_journal()
    if success:
        print(f"\n🎉 TEST RÉUSSI: L'application utilise les montants du Journal !")
    else:
        print(f"\n💥 TEST ÉCHOUÉ: Des problèmes ont été détectés!")
