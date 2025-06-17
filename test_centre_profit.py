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
      # Vérifier que les fichiers existent
    for path, name in [(journal_path, "Journal"), (orders_path, "Commandes"), (transactions_path, "Transactions")]:
        if not os.path.exists(path):
            print(f"⚠️ ATTENTION: Fichier {name} non trouvé: {path}")
            print("   Utilisation des fichiers de test à la place...")
            return test_centre_profit_with_test_files()
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            return verify_centre_profit_column(df_result)
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_centre_profit_with_test_files():
    """Test avec des fichiers de test pour vérifier que Centre de profit = lcdi.fr"""
    
    # Utiliser les fichiers de test
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    journal_path = os.path.join(test_data_dir, '20240116-Journal_test.csv')
    orders_path = os.path.join(test_data_dir, 'orders_export_test.csv')
    transactions_path = os.path.join(test_data_dir, 'payment_transactions_export_test.csv')
    
    print("=== Test Centre de profit avec les fichiers de test ===")
    
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
            return verify_centre_profit_column(df_result)
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_centre_profit_column(df_result):
    """Fonction auxiliaire pour vérifier la colonne Centre de profit"""
    
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
            
            # Vérifier aussi les nouvelles fonctionnalités
            verify_additional_features(df_result)
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

def verify_additional_features(df_result):
    """Vérifier les nouvelles fonctionnalités ajoutées"""
    
    print(f"\n🔍 Vérification des nouvelles fonctionnalités:")
    
    # Vérifier la traduction des états
    if 'Etat' in df_result.columns:
        etat_values = df_result['Etat'].dropna().unique()
        print(f"   📋 États trouvés: {list(etat_values)}")
        
        # Vérifier qu'on a des états en français
        french_states = ['payée', 'en attente', 'payée partiellement', 'remboursée', 'annulée']
        has_french = any(state in french_states for state in etat_values if isinstance(state, str))
        
        if has_french:
            print(f"   ✅ États traduits en français détectés")
        else:
            print(f"   ⚠️ Aucun état en français détecté")
    
    # Vérifier la colonne Statut
    if 'Statut' in df_result.columns:
        statut_values = df_result['Statut'].value_counts()
        print(f"   📊 Répartition des statuts:")
        for statut, count in statut_values.items():
            print(f"      {statut}: {count} lignes")
        
        expected_statuts = ['COMPLET', 'INCOMPLET']
        has_expected = all(statut in expected_statuts for statut in statut_values.index)
        
        if has_expected:
            print(f"   ✅ Colonne Statut correcte (COMPLET/INCOMPLET)")
        else:
            print(f"   ⚠️ Valeurs inattendues dans la colonne Statut")

if __name__ == "__main__":
    print("🚀 Démarrage du test Centre de profit...")
    success = test_centre_profit_with_real_files()
    if success:
        print(f"\n🎉 TEST RÉUSSI: La colonne 'Centre de profit' contient bien 'lcdi.fr' partout!")
    else:
        print(f"\n💥 TEST ÉCHOUÉ: Des problèmes ont été détectés!")
