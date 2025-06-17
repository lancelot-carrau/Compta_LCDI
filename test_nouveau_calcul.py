#!/usr/bin/env python3
"""
Test pour vérifier le nouveau calcul des montants HT/TVA/TTC
à partir des colonnes Total et Taxes du fichier orders_export
"""

import pandas as pd
import numpy as np
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import calculate_corrected_amounts

def test_nouveau_calcul_montants():
    """Test du nouveau calcul HT = Total - Taxes"""
    
    print("📊 Test du nouveau calcul des montants (HT = Total - Taxes)")
    
    # Créer un DataFrame de test avec les nouvelles colonnes
    test_data = {
        'Name': ['#1001', '#1002', '#1003', '#1004', '#1005'],
        'Total': [100.0, 200.0, 0.0, 119.0, 59.5],  # TTC
        'Taxes': [16.67, 33.33, 0.0, 19.0, 9.5],    # TVA
        'Presentment Amount': [100.0, 200.0, 150.0, 119.0, 59.5],  # Ancienne source (ignorée maintenant)
        'Tax 1 Value': [20.0, 40.0, 30.0, 24.0, 12.0]  # Ancienne source (ignorée maintenant)
    }
    
    df_test = pd.DataFrame(test_data)
    
    print(f"\n📋 Données de test:")
    print(df_test[['Name', 'Total', 'Taxes', 'Presentment Amount', 'Tax 1 Value']])
    
    # Calculer les montants avec la nouvelle fonction
    amounts = calculate_corrected_amounts(df_test)
    
    print(f"\n🧮 Résultats du calcul:")
    results_df = pd.DataFrame({
        'Name': df_test['Name'],
        'Total (TTC)': df_test['Total'],
        'Taxes (TVA)': df_test['Taxes'],
        'HT calculé': amounts['HT'],
        'TVA finale': amounts['TVA'],
        'TTC final': amounts['TTC']
    })
    
    print(results_df)
    
    # Vérifications
    print(f"\n🔍 Vérifications:")
    
    # Test 1: TTC final = Total
    ttc_ok = all(amounts['TTC'] == df_test['Total'])
    print(f"   ✅ TTC = Total: {ttc_ok}")
    
    # Test 2: TVA finale = Taxes (sauf si Total = 0)
    tva_ok = True
    for i in range(len(df_test)):
        expected_tva = df_test['Taxes'].iloc[i] if df_test['Total'].iloc[i] > 0 else 0
        actual_tva = amounts['TVA'].iloc[i]
        if abs(expected_tva - actual_tva) > 0.01:
            tva_ok = False
            print(f"      ❌ TVA ligne {i}: attendu {expected_tva}, obtenu {actual_tva}")
    
    if tva_ok:
        print(f"   ✅ TVA correcte (0 si Total=0, sinon = Taxes)")
    
    # Test 3: HT = TTC - TVA
    ht_ok = True
    for i in range(len(df_test)):
        expected_ht = amounts['TTC'].iloc[i] - amounts['TVA'].iloc[i]
        actual_ht = amounts['HT'].iloc[i]
        if abs(expected_ht - actual_ht) > 0.01:
            ht_ok = False
            print(f"      ❌ HT ligne {i}: attendu {expected_ht}, obtenu {actual_ht}")
    
    if ht_ok:
        print(f"   ✅ HT = TTC - TVA correctement calculé")
    
    # Test 4: Pas de HT négatif
    no_negative_ht = all(amounts['HT'] >= 0)
    print(f"   ✅ Pas de HT négatif: {no_negative_ht}")
    
    # Test 5: Vérifier que les anciennes colonnes sont ignorées
    # Ligne #1003: Total=0 mais Presentment Amount=150 -> doit utiliser Total=0
    line_3_correct = (amounts['TTC'].iloc[2] == 0 and amounts['TVA'].iloc[2] == 0 and amounts['HT'].iloc[2] == 0)
    print(f"   ✅ Ignorer anciennes colonnes (ligne #1003): {line_3_correct}")
    
    # Résumé
    all_tests_passed = ttc_ok and tva_ok and ht_ok and no_negative_ht and line_3_correct
    
    if all_tests_passed:
        print(f"\n🎉 TOUS LES TESTS RÉUSSIS!")
        print(f"   ✓ Le calcul utilise bien Total (TTC) et Taxes (TVA)")
        print(f"   ✓ HT = Total - Taxes")
        print(f"   ✓ TVA = 0 si Total = 0")
        print(f"   ✓ Pas de montants négatifs")
        return True
    else:
        print(f"\n❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        return False

def test_cas_specifiques():
    """Test de cas spécifiques"""
    
    print(f"\n🔬 Test de cas spécifiques:")
    
    # Cas avec Total=0 mais Taxes>0 (doit corriger TVA à 0)
    case_1 = pd.DataFrame({
        'Total': [0],
        'Taxes': [10]
    })
    
    amounts_1 = calculate_corrected_amounts(case_1)
    case_1_ok = (amounts_1['TTC'][0] == 0 and amounts_1['TVA'][0] == 0 and amounts_1['HT'][0] == 0)
    print(f"   ✅ Cas Total=0, Taxes=10 -> TTC=0, TVA=0, HT=0: {case_1_ok}")
    
    # Cas normal
    case_2 = pd.DataFrame({
        'Total': [120],
        'Taxes': [20]
    })
    
    amounts_2 = calculate_corrected_amounts(case_2)
    case_2_ok = (amounts_2['TTC'][0] == 120 and amounts_2['TVA'][0] == 20 and amounts_2['HT'][0] == 100)
    print(f"   ✅ Cas Total=120, Taxes=20 -> TTC=120, TVA=20, HT=100: {case_2_ok}")
    
    return case_1_ok and case_2_ok

if __name__ == "__main__":
    print("🚀 Test du nouveau calcul des montants...")
    
    success_1 = test_nouveau_calcul_montants()
    success_2 = test_cas_specifiques()
    
    if success_1 and success_2:
        print(f"\n🎊 TOUS LES TESTS RÉUSSIS!")
        print(f"Le nouveau calcul HT = Total - Taxes fonctionne parfaitement!")
    else:
        print(f"\n💥 CERTAINS TESTS ONT ÉCHOUÉ!")
        print(f"Vérifiez le code de calcul des montants.")
