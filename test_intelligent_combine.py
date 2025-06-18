#!/usr/bin/env python3
"""
Test avancé pour la nouvelle logique de combinaison intelligente
Teste la priorité des anciennes données et la complétion des données manquantes
"""
import pandas as pd
import os
from app import combine_with_old_file

def create_advanced_test_files():
    """Crée des fichiers de test pour la combinaison intelligente"""
    
    # Nouvelles données avec conflits et compléments
    new_data = pd.DataFrame({
        'Réf.WEB': ['CMD001', 'CMD002', 'CMD003', 'CMD004'],
        'Date': ['2025-01-15', '2025-01-16', '2025-01-17', '2025-01-18'],
        'Client': ['Client A Modifié', 'Client B', '', 'Client D'],  # CMD001: conflit, CMD003: complément
        'TTC': [125.00, 240.00, 360.00, 480.00],  # CMD001: conflit (ancien 120)
        'HT': [104.17, '', 300.00, 400.00],  # CMD002: complément, CMD001: conflit
        'TVA': ['', 40.00, 60.00, 80.00],  # CMD001: complément (ancien vide)
        'Virement bancaire': [125.00, 0.00, 0.00, 480.00],  # CMD001: conflit
        'Carte bancaire': [0.00, 240.00, 0.00, 0.00],
        'PayPal': [0.00, 0.00, 360.00, 0.00],
        'Statut': ['COMPLET', 'COMPLET', 'COMPLET', 'COMPLET'],
        'Nouvelle_Colonne': ['Valeur1', 'Valeur2', 'Valeur3', 'Valeur4']  # Nouvelle colonne
    })
    
    # Anciennes données avec données manquantes et complètes
    old_data = pd.DataFrame({
        'Réf.WEB': ['CMD000', 'CMD001', 'CMD002', 'CMD999'],
        'Date': ['2025-01-10', '2025-01-15', '2025-01-16', '2025-01-20'],
        'Client': ['Client Ancien', 'Client A Original', 'Client B', 'Client Z'],  # CMD001: priorité ancien
        'TTC': [100.00, 120.00, 240.00, 500.00],  # CMD001: priorité ancien (120 vs 125)
        'HT': [83.33, 100.00, pd.NA, 416.67],  # CMD002: sera complété par nouveau (200)
        'TVA': [16.67, pd.NA, 40.00, 83.33],  # CMD001: sera complété par nouveau
        'Virement bancaire': [100.00, 120.00, 240.00, 500.00],  # CMD001: priorité ancien
        'Carte bancaire': [0.00, 0.00, 0.00, 0.00],
        'PayPal': [0.00, 0.00, 0.00, 0.00],
        'Statut': ['COMPLET', 'COMPLET', '', 'COMPLET'],  # CMD002: sera complété
        'Ancienne_Colonne': ['AncVal1', 'AncVal2', 'AncVal3', 'AncVal4']  # Colonne unique à l'ancien
    })
    
    # Sauvegarder les fichiers de test
    new_data.to_csv('test_new_data_advanced.csv', index=False)
    old_data.to_excel('test_old_data_advanced.xlsx', index=False)
    
    print("=== FICHIERS DE TEST AVANCÉS CRÉÉS ===")
    print(f"Nouvelles données: {len(new_data)} lignes")
    print(f"Anciennes données: {len(old_data)} lignes")
    print(f"Références communes (conflits): CMD001, CMD002")
    
    # Analyser les conflits attendus
    print("\n=== CONFLITS ET COMPLÉMENTS ATTENDUS ===")
    print("CMD001:")
    print("  - Client: 'Client A Original' (ancien) vs 'Client A Modifié' (nouveau) → ANCIEN")
    print("  - TTC: 120.00 (ancien) vs 125.00 (nouveau) → ANCIEN")
    print("  - HT: 100.00 (ancien) vs 104.17 (nouveau) → ANCIEN")
    print("  - TVA: NaN (ancien) vs '' (nouveau) → NOUVEAU (complément)")
    print("  - Virement: 120.00 (ancien) vs 125.00 (nouveau) → ANCIEN")
    
    print("\nCMD002:")
    print("  - Client: 'Client B' (identique) → Pas de conflit")
    print("  - HT: NaN (ancien) vs '' (nouveau) → Pas de complément (nouveau vide)")
    print("  - Statut: '' (ancien) vs 'COMPLET' (nouveau) → NOUVEAU (complément)")
    
    return new_data, old_data

def test_intelligent_combine():
    """Test la fonctionnalité de combinaison intelligente"""
    
    print("=== TEST DE LA COMBINAISON INTELLIGENTE ===")
    
    # Créer les fichiers de test
    new_data, old_data = create_advanced_test_files()
    
    # Tester la combinaison intelligente
    result = combine_with_old_file(new_data, 'test_old_data_advanced.xlsx')
    
    print(f"\n=== ANALYSE DES RÉSULTATS ===")
    print(f"Données finales: {len(result)} lignes")
    
    # Vérifier CMD001 (conflits)
    cmd001_result = result[result['Réf.WEB'] == 'CMD001'].iloc[0]
    print(f"\nCMD001 - Vérification des priorités:")
    print(f"  Client: '{cmd001_result['Client']}' (attendu: 'Client A Original')")
    print(f"  TTC: {cmd001_result['TTC']} (attendu: 120.00)")
    print(f"  HT: {cmd001_result['HT']} (attendu: 100.00)")
    print(f"  TVA: '{cmd001_result['TVA']}' (attendu: complété par nouveau)")
    print(f"  Virement: {cmd001_result['Virement bancaire']} (attendu: 120.00)")
    
    # Vérifier CMD002 (compléments)
    cmd002_result = result[result['Réf.WEB'] == 'CMD002'].iloc[0]
    print(f"\nCMD002 - Vérification des compléments:")
    print(f"  Client: '{cmd002_result['Client']}' (identique)")
    print(f"  HT: '{cmd002_result['HT']}' (ancien vide, nouveau vide → reste vide)")
    print(f"  Statut: '{cmd002_result['Statut']}' (attendu: 'COMPLET' complété)")
    
    # Vérifier les nouvelles entrées
    new_entries = result[result['Réf.WEB'].isin(['CMD003', 'CMD004'])]
    print(f"\nNouveaux enregistrements: {len(new_entries)} (CMD003, CMD004)")
    
    # Vérifier les colonnes
    print(f"\nColonnes finales: {len(result.columns)}")
    print(f"Nouvelle_Colonne présente: {'Nouvelle_Colonne' in result.columns}")
    print(f"Ancienne_Colonne présente: {'Ancienne_Colonne' in result.columns}")
    
    # Afficher un aperçu
    print(f"\n=== APERÇU DU RÉSULTAT ===")
    display_columns = ['Réf.WEB', 'Client', 'TTC', 'HT', 'TVA', 'Statut']
    available_columns = [col for col in display_columns if col in result.columns]
    print(result[available_columns].to_string(index=False))
    
    # Tests de validation
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Nombre total correct
    expected_total = 6  # 4 ancien + 2 nouveau (CMD003, CMD004)
    if len(result) == expected_total:
        print(f"\n✅ Test 1 RÉUSSI: Nombre total correct ({len(result)})")
        tests_passed += 1
    else:
        print(f"\n❌ Test 1 ÉCHOUÉ: Attendu {expected_total}, obtenu {len(result)}")
    
    # Test 2: Priorité ancien pour CMD001 Client
    if cmd001_result['Client'] == 'Client A Original':
        print("✅ Test 2 RÉUSSI: Priorité ancien pour Client CMD001")
        tests_passed += 1
    else:
        print(f"❌ Test 2 ÉCHOUÉ: Client CMD001 = '{cmd001_result['Client']}'")
    
    # Test 3: Priorité ancien pour CMD001 TTC
    if cmd001_result['TTC'] == 120.00:
        print("✅ Test 3 RÉUSSI: Priorité ancien pour TTC CMD001")
        tests_passed += 1
    else:
        print(f"❌ Test 3 ÉCHOUÉ: TTC CMD001 = {cmd001_result['TTC']}")
    
    # Test 4: Complément pour CMD002 Statut
    if cmd002_result['Statut'] == 'COMPLET':
        print("✅ Test 4 RÉUSSI: Complément Statut CMD002")
        tests_passed += 1
    else:
        print(f"❌ Test 4 ÉCHOUÉ: Statut CMD002 = '{cmd002_result['Statut']}'")
    
    # Test 5: Nouvelles colonnes harmonisées
    if 'Nouvelle_Colonne' in result.columns and 'Ancienne_Colonne' in result.columns:
        print("✅ Test 5 RÉUSSI: Harmonisation des colonnes")
        tests_passed += 1
    else:
        print("❌ Test 5 ÉCHOUÉ: Harmonisation des colonnes")
    
    print(f"\n=== RÉSULTATS DES TESTS ===")
    print(f"Tests réussis: {tests_passed}/{total_tests}")
    success_rate = (tests_passed / total_tests) * 100
    print(f"Taux de réussite: {success_rate:.1f}%")
    
    # Nettoyer les fichiers de test
    for file in ['test_new_data_advanced.csv', 'test_old_data_advanced.xlsx']:
        if os.path.exists(file):
            os.remove(file)
    
    return success_rate >= 80

if __name__ == "__main__":
    success = test_intelligent_combine()
    if success:
        print("\n🎉 TEST GLOBAL RÉUSSI - Combinaison intelligente fonctionnelle!")
    else:
        print("\n⚠️ TEST GLOBAL ÉCHOUÉ - Révision nécessaire")
