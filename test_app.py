#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement du générateur de tableau de facturation LCDI
"""

import pandas as pd
import os
import tempfile
from datetime import datetime

def create_test_data():
    """Crée des fichiers de test pour valider l'application"""
    
    print("=== CRÉATION DES FICHIERS DE TEST ===")
    
    # Créer le dossier de test
    test_folder = "test_data"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)    # 1. Fichier des commandes de test (format Shopify réaliste avec lignes multiples par commande)
    orders_data = {
        'Id': ['#1001', '#1001', '#1002', '#1003', '#1003', '#1004', '#1005'],  # Doublons intentionnels
        'Fulfilled at': ['2024-01-15', '2024-01-15', '2024-01-16', '2024-01-17', '2024-01-17', '2024-01-18', '2024-01-19'],
        'Billing Name': ['Dupont Jean', 'Dupont Jean', 'Martin Marie', 'Durand Paul', 'Durand Paul', 'Bernard Sophie', 'Leroy Pierre'],
        'Financial Status': ['paid', 'paid', 'pending', 'paid', 'paid', 'paid', 'refunded'],
        'Tax 1 Value': [10.00, 10.00, 15.50, 16.00, 16.00, 8.75, 12.30],  # Sera sommé
        'Outstanding Balance': [0.00, 0.00, 77.50, 0.00, 0.00, 0.00, 65.70],  # Sera sommé
        'Payment Method': ['PayPal', 'PayPal', 'Virement bancaire', 'ALMA', 'ALMA', 'Younited', 'PayPal'],
        'Total': [60.00, 60.00, 93.00, 96.00, 96.00, 52.50, 77.70],  # Sera sommé
        'Email': ['jean@example.com', 'jean@example.com', 'marie@example.com', 'paul@example.com', 'paul@example.com', 'sophie@example.com', 'pierre@example.com'],
        'Lineitem name': ['Produit A', 'Produit B', 'Produit C', 'Produit D', 'Produit E', 'Produit F', 'Produit G'],  # Différent par ligne
        'Lineitem price': [60.00, 60.00, 93.00, 96.00, 96.00, 52.50, 77.70]  # Sera sommé
    }
    
    df_orders = pd.DataFrame(orders_data)
    orders_file = os.path.join(test_folder, 'orders_export_test.csv')
    df_orders.to_csv(orders_file, sep=',', index=False, encoding='utf-8')
    print(f"✓ Fichier commandes créé: {orders_file}")
      # 2. Fichier des transactions de test
    transactions_data = {
        'Order': ['#1001', '#1001', '#1002', '#1003', '#1004', '#1005'],  # Doublons pour #1001 et correspondances
        'Presentment Amount': [120.00, 0.00, 93.00, 192.00, 52.50, 77.70],  # Total réel après agrégation
        'Fee': [3.60, 0.00, 2.79, 5.76, 1.58, 2.33],
        'Net': [116.40, 0.00, 90.21, 186.24, 50.92, 75.37]
    }
    
    df_transactions = pd.DataFrame(transactions_data)
    transactions_file = os.path.join(test_folder, 'payment_transactions_export_test.csv')
    df_transactions.to_csv(transactions_file, sep=',', index=False, encoding='utf-8')
    print(f"✓ Fichier transactions créé: {transactions_file}")
      # 3. Fichier journal de test (format réaliste basé sur votre fichier)
    journal_data = {
        'Référence externe': ['#1001', '#1003', '#1004'],  # Correspond aux ID des commandes
        'Référence LMB': ['LMB-2024-001', 'LMB-2024-003', 'LMB-2024-004'],
        'Date du document': ['15/01/2024', '17/01/2024', '18/01/2024'],
        'Montant du document TTC': [120.00, 192.00, 52.50],
        'Etat du document': ['Validé', 'Validé', 'Validé'],
        'Nom contact': ['Dupont Jean', 'Durand Paul', 'Bernard Sophie']
    }
    
    df_journal = pd.DataFrame(journal_data)
    journal_file = os.path.join(test_folder, '20240116-Journal_test.csv')
    df_journal.to_csv(journal_file, sep=';', index=False, encoding='utf-8')
    print(f"✓ Fichier journal créé: {journal_file}")
    
    print(f"\n=== FICHIERS DE TEST CRÉÉS DANS '{test_folder}' ===")
    return orders_file, transactions_file, journal_file

def test_processing_logic():
    """Test la logique de traitement sans l'interface web"""
    
    print("\n=== TEST DE LA LOGIQUE DE TRAITEMENT ===")
    
    # Importer la fonction de traitement
    try:
        from app import generate_consolidated_billing_table
        print("✓ Fonction de traitement importée avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    
    # Créer les fichiers de test
    orders_file, transactions_file, journal_file = create_test_data()
    
    try:
        # Exécuter le traitement
        df_result = generate_consolidated_billing_table(orders_file, transactions_file, journal_file)
        
        print(f"✓ Traitement réussi!")
        print(f"✓ Nombre de lignes générées: {len(df_result)}")
        print(f"✓ Nombre de colonnes: {len(df_result.columns)}")
        
        # Vérifier les colonnes attendues
        expected_columns = [
            'Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client',
            'HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission',
            'Virement bancaire', 'ALMA', 'Younited', 'PayPal'
        ]
        
        missing_columns = set(expected_columns) - set(df_result.columns)
        if missing_columns:
            print(f"❌ Colonnes manquantes: {missing_columns}")
            return False
        
        print("✓ Toutes les colonnes attendues sont présentes")
        
        # Sauvegarder le résultat pour inspection
        test_output = 'test_data/tableau_test_result.csv'
        df_result.to_csv(test_output, sep=';', decimal=',', index=False, encoding='utf-8-sig')
        print(f"✓ Résultat sauvegardé dans: {test_output}")
        
        # Afficher quelques statistiques
        print(f"\n=== STATISTIQUES DU TABLEAU GÉNÉRÉ ===")
        print(f"Nombre total de commandes: {len(df_result)}")
        print(f"Montant TTC total: {df_result['TTC'].sum():.2f}")
        print(f"Montant TVA total: {df_result['TVA'].sum():.2f}")
        print(f"Montant HT total: {df_result['HT'].sum():.2f}")
        
        # Répartition des méthodes de paiement
        print(f"\n=== RÉPARTITION DES PAIEMENTS ===")
        print(f"PayPal: {df_result['PayPal'].sum():.2f}")
        print(f"Virement bancaire: {df_result['Virement bancaire'].sum():.2f}")
        print(f"ALMA: {df_result['ALMA'].sum():.2f}")
        print(f"Younited: {df_result['Younited'].sum():.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        return False

def test_dependencies():
    """Test des dépendances Python"""
    
    print("=== TEST DES DÉPENDANCES ===")
    
    required_packages = ['flask', 'pandas', 'werkzeug']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installé")
        except ImportError:
            print(f"❌ {package} non installé")
            return False
    
    return True

def main():
    """Fonction principale de test"""
    
    print("🧪 TESTS DU GÉNÉRATEUR DE FACTURATION LCDI")
    print("=" * 50)
    
    # Test des dépendances
    if not test_dependencies():
        print("\n❌ Certaines dépendances sont manquantes")
        print("Exécutez: pip install -r requirements.txt")
        return
    
    # Test de la logique de traitement
    if not test_processing_logic():
        print("\n❌ Échec des tests de traitement")
        return
    
    print("\n" + "=" * 50)
    print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
    print("\nL'application est prête à être utilisée.")
    print("Lancez l'application avec: python app.py")
    print("Ou utilisez le script: start.bat")

if __name__ == "__main__":
    main()
