#!/usr/bin/env python3
"""
Test spécifique pour le mapping des colonnes du fichier journal
"""
import pandas as pd
import sys
import os

# Ajouter le répertoire courant au path pour importer app
sys.path.append(os.getcwd())

def test_journal_mapping():
    print("=== TEST MAPPING FICHIER JOURNAL ===")
    
    # Simuler votre fichier journal réel
    journal_data = {
        'Référence LMB': ['LMB-001', 'LMB-002'],
        'Date du document': ['15/01/2024', '16/01/2024'],
        'Montant du document TTC': [120.00, 93.00],
        'Etat du document': ['Validé', 'Validé'],
        'Nom contact': ['Client 1', 'Client 2'],
        'Montant du document HT': [100.00, 77.50],
        'Pourcentage marge': [20.0, 15.0],
        'Référence externe': ['#1001', '#1002'],  # <- Ceci devrait mapper vers 'Piece'
        'Vendeur': ['Vendeur 1', 'Vendeur 2'],
        'Centre de profit': ['lcdi.fr', 'lcdi.fr'],
        'Montant marge HT': [20.00, 15.50]
    }
    
    df_journal = pd.DataFrame(journal_data)
    print("Colonnes disponibles dans le fichier journal simulé:")
    print(list(df_journal.columns))
    
    # Test du mapping pour 'Piece'
    piece_variants = ['Piece', 'piece', 'Pièce', 'pièce', 'Reference', 'reference', 'Ref', 'ref', 
                     'Order', 'order', 'Commande', 'Id', 'ID', 'id', 'Référence externe', 
                     'référence externe', 'Reference externe', 'reference externe', 'Externe', 'externe']
    
    print("\nTest du mapping pour 'Piece':")
    piece_found = False
    for variant in piece_variants:
        if variant in df_journal.columns:
            print(f"✓ Mapping trouvé: '{variant}' -> 'Piece'")
            piece_found = True
            break
    
    if not piece_found:
        print("❌ Aucun mapping trouvé pour 'Piece'")
        print("Suggestions:")
        for col in df_journal.columns:
            if 'ref' in col.lower() or 'extern' in col.lower():
                print(f"  - {col}")
    
    # Test du mapping pour 'Référence LMB'
    lmb_variants = ['Référence LMB', 'référence lmb', 'Reference LMB', 'reference lmb', 
                   'LMB', 'lmb', 'Ref LMB', 'ref lmb']
    
    print("\nTest du mapping pour 'Référence LMB':")
    lmb_found = False
    for variant in lmb_variants:
        if variant in df_journal.columns:
            print(f"✓ Mapping trouvé: '{variant}' -> 'Référence LMB'")
            lmb_found = True
            break
    
    if not lmb_found:
        print("❌ Aucun mapping trouvé pour 'Référence LMB'")
    
    print(f"\nRésultat: Piece={'✓' if piece_found else '❌'}, LMB={'✓' if lmb_found else '❌'}")
    
    return piece_found and lmb_found

if __name__ == "__main__":
    success = test_journal_mapping()
    if success:
        print("\n🎉 Test réussi! Le mapping devrait fonctionner.")
    else:
        print("\n❌ Test échoué. Vérifiez le mapping.")
