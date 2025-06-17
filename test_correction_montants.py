#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la correction du problème de duplication des montants
lors de références multiples dans le journal.

Ce script teste spécifiquement le cas LCDI-1020 et LCDI-1021 pour s'assurer que :
1. Les deux commandes reçoivent bien la même Réf. LMB du journal
2. Chaque commande garde ses montants individuels (pas de duplication)
3. La somme des montants des deux commandes correspond au montant total du journal
"""

import pandas as pd
import sys
import os

# Ajouter le dossier parent au chemin pour importer app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app import improve_journal_matching, calculate_corrected_amounts

def test_correction_montants_multiples():
    """Test la correction du problème de duplication des montants"""
    print("=== TEST CORRECTION MONTANTS MULTIPLES ===\n")
    
    # Créer des données de test
    print("1. Création des données de test...")
    
    # Données des commandes (2 commandes séparées)
    df_orders = pd.DataFrame({
        'Name': ['#LCDI-1020', '#LCDI-1021'],
        'Total': [2067.9, 15.9],  # Montants individuels
        'Taxes': [344.65, 2.65],  # TVA individuelle
        'Billing name': ['Client Test 1', 'Client Test 2'],
        'Financial Status': ['paid', 'paid'],
        'Payment Method': ['Virement bancaire', 'PayPal']
    })
    
    # Données du journal (1 ligne avec référence multiple)
    df_journal = pd.DataFrame({
        'Piece': ['LCDI-1020 LCDI-1021'],  # Référence multiple
        'Référence LMB': ['LMB-2024-001'],
        'Montant du document TTC': ['2083,8'],  # Montant total (somme des deux commandes)
        'Montant du document HT': ['1736,5']   # HT total
    })
    
    print(f"   - Commandes: {len(df_orders)} lignes")
    print(f"     * LCDI-1020: {df_orders.loc[0, 'Total']} € TTC")
    print(f"     * LCDI-1021: {df_orders.loc[1, 'Total']} € TTC")
    print(f"   - Journal: {len(df_journal)} lignes")
    print(f"     * Référence multiple: {df_journal.loc[0, 'Piece']}")
    print(f"     * Montant total journal: {df_journal.loc[0, 'Montant du document TTC']} €")
    
    # Test de la fusion améliorée
    print("\n2. Test de la fusion améliorée...")
    df_merged = improve_journal_matching(df_orders, df_journal)
    
    # Vérifications de la fusion
    print("\n3. Vérification de la fusion...")
    
    # Vérifier que les deux commandes ont la Réf. LMB
    ref_lmb_count = df_merged['Référence LMB'].notna().sum()
    print(f"   ✓ Commandes avec Réf. LMB: {ref_lmb_count}/2")
    
    # Vérifier que c'est la même Réf. LMB
    ref_lmb_unique = df_merged['Référence LMB'].dropna().unique()
    print(f"   ✓ Réf. LMB partagée: {ref_lmb_unique}")
    
    # Vérifier que les montants du journal ont été effacés (pour éviter la duplication)
    montant_journal_ttc = df_merged['Montant du document TTC'].dropna()
    print(f"   ✓ Montants TTC du journal (doivent être None): {montant_journal_ttc.tolist()}")
    
    # Test du calcul des montants corrigés
    print("\n4. Test du calcul des montants corrigés...")
    corrected_amounts = calculate_corrected_amounts(df_merged)
    
    # Vérification des montants
    print("\n5. Vérification des montants finaux...")
    
    for i, (index, row) in enumerate(df_merged.iterrows()):
        commande = row['Name']
        ttc_original = row['Total']
        ttc_final = corrected_amounts['TTC'].iloc[i]
        ht_final = corrected_amounts['HT'].iloc[i]
        tva_final = corrected_amounts['TVA'].iloc[i]
        ref_lmb = row['Référence LMB']
        
        print(f"   {commande}:")
        print(f"     - Réf. LMB: {ref_lmb}")
        print(f"     - TTC original: {ttc_original} €")
        print(f"     - TTC final: {ttc_final} €")
        print(f"     - HT final: {ht_final} €")
        print(f"     - TVA final: {tva_final} €")
        print(f"     - Montants préservés: {'✓' if ttc_final == ttc_original else '✗'}")
        print()
    
    # Vérification globale
    print("6. Vérification globale...")
    
    total_ttc_final = corrected_amounts['TTC'].sum()
    total_ttc_journal = 2083.8  # Montant attendu du journal
    
    print(f"   - Somme TTC finale: {total_ttc_final} €")
    print(f"   - Montant TTC journal: {total_ttc_journal} €")
    print(f"   - Cohérence: {'✓' if abs(total_ttc_final - total_ttc_journal) < 0.1 else '✗'}")
    
    # Résumé du test
    print("\n=== RÉSUMÉ DU TEST ===")
    
    success = True
    
    # Test 1: Les deux commandes ont la Réf. LMB
    if ref_lmb_count == 2:
        print("✓ Test 1 RÉUSSI: Les deux commandes ont reçu la Réf. LMB")
    else:
        print("✗ Test 1 ÉCHOUÉ: Toutes les commandes n'ont pas reçu la Réf. LMB")
        success = False
    
    # Test 2: Montants individuels préservés
    montants_preserves = all(
        corrected_amounts['TTC'].iloc[i] == df_orders.iloc[i]['Total'] 
        for i in range(len(df_orders))
    )
    if montants_preserves:
        print("✓ Test 2 RÉUSSI: Les montants individuels sont préservés")
    else:
        print("✗ Test 2 ÉCHOUÉ: Les montants individuels ne sont pas préservés")
        success = False
    
    # Test 3: Somme cohérente
    if abs(total_ttc_final - total_ttc_journal) < 0.1:
        print("✓ Test 3 RÉUSSI: La somme des montants est cohérente avec le journal")
    else:
        print("✗ Test 3 ÉCHOUÉ: La somme des montants n'est pas cohérente")
        success = False
    
    if success:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("   La correction du problème de duplication des montants fonctionne correctement.")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("   La correction nécessite des ajustements supplémentaires.")
    
    return success

if __name__ == "__main__":
    test_correction_montants_multiples()
