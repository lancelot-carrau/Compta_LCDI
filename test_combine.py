#!/usr/bin/env python3
"""
Test script pour vérifier la fonctionnalité de combinaison
"""
import pandas as pd
import os
from app import combine_with_old_file

def create_test_files():
    """Crée des fichiers de test pour la combinaison"""
    
    # Créer des données de test - nouvelles données
    new_data = pd.DataFrame({
        'Réf.WEB': ['CMD001', 'CMD002', 'CMD003'],
        'Date': ['2025-01-15', '2025-01-16', '2025-01-17'],
        'Client': ['Client A', 'Client B', 'Client C'],
        'TTC': [120.00, 240.00, 360.00],
        'HT': [100.00, 200.00, 300.00],
        'TVA': [20.00, 40.00, 60.00],
        'Virement bancaire': [120.00, 0.00, 0.00],
        'Carte bancaire': [0.00, 240.00, 0.00],
        'PayPal': [0.00, 0.00, 360.00],
        'Statut': ['COMPLET', 'COMPLET', 'COMPLET']
    })
    
    # Créer des données anciennes (avec un doublon)
    old_data = pd.DataFrame({
        'Réf.WEB': ['CMD000', 'CMD001', 'CMD999'],  # CMD001 est un doublon
        'Date': ['2025-01-10', '2025-01-15', '2025-01-20'],
        'Client': ['Client Ancien', 'Client A', 'Client Z'],
        'TTC': [100.00, 120.00, 500.00],
        'HT': [83.33, 100.00, 416.67],
        'TVA': [16.67, 20.00, 83.33],
        'Virement bancaire': [100.00, 120.00, 500.00],
        'Carte bancaire': [0.00, 0.00, 0.00],
        'PayPal': [0.00, 0.00, 0.00],
        'Statut': ['COMPLET', 'COMPLET', 'COMPLET']
    })
    
    # Sauvegarder les fichiers de test
    new_data.to_csv('test_new_data.csv', index=False)
    old_data.to_excel('test_old_data.xlsx', index=False)
    
    print("Fichiers de test créés:")
    print(f"- test_new_data.csv: {len(new_data)} lignes")
    print(f"- test_old_data.xlsx: {len(old_data)} lignes")
    print(f"- Doublon attendu: CMD001")
    
    return new_data, old_data

def test_combine_functionality():
    """Test la fonctionnalité de combinaison"""
    
    print("=== TEST DE LA FONCTIONNALITÉ DE COMBINAISON ===")
    
    # Créer les fichiers de test
    new_data, old_data = create_test_files()
    
    # Tester la combinaison
    result = combine_with_old_file(new_data, 'test_old_data.xlsx')
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Données anciennes: {len(old_data)} lignes")
    print(f"Nouvelles données: {len(new_data)} lignes")
    print(f"Résultat combiné: {len(result)} lignes")
    
    # Vérifications
    expected_total = len(old_data) + len(new_data) - 1  # -1 car un doublon
    
    if len(result) == expected_total:
        print("✅ Test réussi: Nombre de lignes correct")
    else:
        print(f"❌ Test échoué: Attendu {expected_total}, obtenu {len(result)}")
    
    # Vérifier que le doublon a été évité
    refs_in_result = result['Réf.WEB'].tolist()
    cmd001_count = refs_in_result.count('CMD001')
    
    if cmd001_count == 1:
        print("✅ Test réussi: Doublon évité correctement")
    else:
        print(f"❌ Test échoué: CMD001 apparaît {cmd001_count} fois")
    
    # Vérifier que toutes les colonnes sont présentes
    expected_columns = set(new_data.columns).union(set(old_data.columns))
    result_columns = set(result.columns)
    
    if expected_columns == result_columns:
        print("✅ Test réussi: Toutes les colonnes présentes")
    else:
        missing = expected_columns - result_columns
        extra = result_columns - expected_columns
        if missing:
            print(f"❌ Colonnes manquantes: {missing}")
        if extra:
            print(f"❌ Colonnes en trop: {extra}")
    
    print(f"\n=== APERÇU DU RÉSULTAT ===")
    print(result[['Réf.WEB', 'Date', 'Client', 'TTC']].head(10))
    
    # Nettoyer les fichiers de test
    for file in ['test_new_data.csv', 'test_old_data.xlsx']:
        if os.path.exists(file):
            os.remove(file)
    
    print(f"\n=== Test terminé ===")

if __name__ == "__main__":
    test_combine_functionality()
