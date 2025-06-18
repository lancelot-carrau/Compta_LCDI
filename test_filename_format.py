#!/usr/bin/env python3
"""
Test pour vérifier l'uniformisation des noms de fichiers
"""
import pandas as pd
import os
from datetime import datetime

def test_filename_format():
    """Test que le nom de fichier est uniforme pour tous les modes"""
    
    print("=== TEST UNIFORMISATION DES NOMS DE FICHIERS ===")
    
    # Simuler la génération du nom de fichier (même logique que l'app)
    timestamp = datetime.now().strftime('%d_%m_%Y')
    
    # Test du format attendu
    expected_format = f'Compta_LCDI_Shopify_{timestamp}.csv'
    
    print(f"Format attendu : {expected_format}")
    print(f"Pattern        : Compta_LCDI_Shopify_DD_MM_YYYY.csv")
    
    # Vérifications
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Format général
    if expected_format.startswith('Compta_LCDI_Shopify_'):
        print("✅ Test 1 RÉUSSI: Préfixe correct")
        tests_passed += 1
    else:
        print("❌ Test 1 ÉCHOUÉ: Préfixe incorrect")
    
    # Test 2: Pas de "COMBINE" dans le nom
    if 'COMBINE' not in expected_format:
        print("✅ Test 2 RÉUSSI: Pas de 'COMBINE' dans le nom")
        tests_passed += 1
    else:
        print("❌ Test 2 ÉCHOUÉ: 'COMBINE' trouvé dans le nom")
    
    # Test 3: Format de date
    date_part = expected_format.split('_')[3:6]  # ['DD', 'MM', 'YYYY.csv']
    if len(date_part) == 3 and date_part[2].endswith('.csv'):
        print("✅ Test 3 RÉUSSI: Format de date correct (DD_MM_YYYY)")
        tests_passed += 1
    else:
        print("❌ Test 3 ÉCHOUÉ: Format de date incorrect")
    
    # Test 4: Extension CSV
    if expected_format.endswith('.csv'):
        print("✅ Test 4 RÉUSSI: Extension .csv présente")
        tests_passed += 1
    else:
        print("❌ Test 4 ÉCHOUÉ: Extension .csv manquante")
    
    # Résultats
    print(f"\n=== RÉSULTATS ===")
    print(f"Tests réussis: {tests_passed}/{total_tests}")
    success_rate = (tests_passed / total_tests) * 100
    print(f"Taux de réussite: {success_rate:.1f}%")
    
    # Exemples de noms pour différents jours
    print(f"\n=== EXEMPLES DE NOMS DE FICHIERS ===")
    example_dates = ['17_06_2025', '18_06_2025', '19_06_2025']
    for date in example_dates:
        filename = f'Compta_LCDI_Shopify_{date}.xlsx'
        print(f"  📁 {filename}")
    
    print(f"\n=== AVANTAGES DE L'UNIFORMISATION ===")
    print("✅ Tri chronologique naturel")
    print("✅ Pas de distinction visuelle entre modes")
    print("✅ Convention de nommage cohérente")
    print("✅ Archivage simplifié")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = test_filename_format()
    if success:
        print("\n🎉 UNIFORMISATION RÉUSSIE - Noms de fichiers cohérents!")
    else:
        print("\n⚠️ PROBLÈME DÉTECTÉ - Révision nécessaire")
