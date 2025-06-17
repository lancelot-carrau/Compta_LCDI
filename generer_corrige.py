#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour générer un nouveau tableau final avec la correction appliquée.
"""

import sys
import os

# Ajouter le dossier parent au chemin pour importer app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app import process_files

def generer_tableau_corrige():
    """Génère un nouveau tableau avec la correction appliquée"""
    print("=== GÉNÉRATION DU TABLEAU CORRIGÉ ===\n")
    
    # Chemins des fichiers
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    # Vérifier que les fichiers existent
    files_to_check = [
        ("Commandes", orders_file),
        ("Transactions", transactions_file),
        ("Journal", journal_file)
    ]
    
    for name, path in files_to_check:
        if not os.path.exists(path):
            print(f"❌ Fichier {name} non trouvé: {path}")
            return False
    
    print("✓ Tous les fichiers source sont présents")
    
    # Générer le tableau
    try:
        print("\n📊 Génération du tableau en cours...")
        output_file = process_files(orders_file, transactions_file, journal_file)
        
        if output_file:
            print(f"\n✅ Tableau généré avec succès: {output_file}")
            return output_file
        else:
            print("\n❌ Erreur lors de la génération")
            return None
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    output_file = generer_tableau_corrige()
    
    if output_file:
        print(f"\n🎉 Génération terminée!")
        print(f"Fichier de sortie: {output_file}")
        print("\nVous pouvez maintenant:")
        print("1. Ouvrir le fichier pour vérifier les montants")
        print("2. Exécuter 'python verifier_correction.py' pour valider")
    else:
        print("\n❌ Échec de la génération")
