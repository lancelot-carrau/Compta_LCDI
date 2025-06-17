import pandas as pd
import sys
import os

# Ajouter le répertoire de l'app au path
sys.path.insert(0, r'C:\Code\Apps\Compta LCDI V2')
from app import generate_consolidated_billing_table, detect_encoding, categorize_payment_method

# Configuration des chemins
JOURNAL_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
COMMANDES_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def test_payment_method_processing():
    """Test spécifique pour vérifier le traitement des méthodes de paiement"""
    print("=== TEST TRAITEMENT MÉTHODES DE PAIEMENT ===\n")
    
    try:        # Traiter les fichiers avec la fonction principale
        print("1. Traitement avec la fonction principale...")
        result_df = generate_consolidated_billing_table(COMMANDES_FILE, TRANSACTIONS_FILE, JOURNAL_FILE)
        
        if result_df is None:
            print("❌ Échec du traitement")
            return
            
        print(f"✅ Traitement réussi - {len(result_df)} lignes générées")
        
        # 2. Analyser les colonnes de méthodes de paiement dans le résultat
        print("\n2. Analyse des colonnes de méthodes de paiement dans le résultat:")
        payment_columns = ['Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        
        for col in payment_columns:
            if col in result_df.columns:
                non_zero_count = (result_df[col] > 0).sum()
                total_amount = result_df[col].sum()
                print(f"   {col}: {non_zero_count} commandes non-nulles, total = {total_amount:.2f}€")
            else:
                print(f"   {col}: ❌ Colonne manquante")
        
        # 3. Analyser quelques lignes spécifiques
        print("\n3. Analyse détaillée de quelques lignes:")
        
        # Afficher les 5 premières lignes avec leurs méthodes de paiement
        for idx in range(min(5, len(result_df))):
            row = result_df.iloc[idx]
            ref = row.get('Référence commande', 'N/A')
            payment_method = row.get('Payment Method', 'N/A')  # Si elle existe
            
            payment_amounts = {}
            for col in payment_columns:
                if col in result_df.columns:
                    payment_amounts[col] = row[col]
            
            print(f"   Ligne {idx+1}: Ref={ref}")
            print(f"      Payment Method (si disponible): {payment_method}")
            print(f"      Montants: {payment_amounts}")
            
        # 4. Vérifier s'il y a des données dans Payment Method
        if 'Payment Method' in result_df.columns:
            print(f"\n4. Colonne 'Payment Method' trouvée dans le résultat:")
            payment_methods = result_df['Payment Method'].value_counts()
            print("   Méthodes présentes:")
            for method, count in payment_methods.items():
                print(f"     - '{method}': {count} commandes")
        else:
            print(f"\n4. ❌ Colonne 'Payment Method' non trouvée dans le résultat")
            print("   Colonnes disponibles:", list(result_df.columns))
        
        # 5. Test de la fonction de catégorisation sur les vraies données
        print(f"\n5. Test direct de la fonction categorize_payment_method:")
        test_methods = [
            'Shopify Payments',
            'Alma - Pay in 4 installments', 
            'Alma - Pay in 10 installments',
            'Younited Pay',
            'custom',
            'PayPal'
        ]
        
        for method in test_methods:
            result = categorize_payment_method(method, 100)
            assigned = [k for k, v in result.items() if v > 0]
            print(f"   '{method}' -> {assigned[0] if assigned else 'Non assigné'}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_method_processing()
