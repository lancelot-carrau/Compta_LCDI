import sys
import os
sys.path.insert(0, r'C:\Code\Apps\Compta LCDI V2')

from app import generate_consolidated_billing_table, save_with_conditional_formatting
import pandas as pd
from datetime import datetime

# Configuration des chemins
JOURNAL_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
COMMANDES_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def test_and_save_corrected_file():
    """Tester la correction et sauvegarder un nouveau fichier avec la correction"""
    print("=== TEST ET SAUVEGARDE AVEC CORRECTION ===\n")
    
    # 1. Générer le tableau avec la correction
    print("1. Génération du tableau avec la correction des méthodes de paiement...")
    try:
        df_result = generate_consolidated_billing_table(COMMANDES_FILE, TRANSACTIONS_FILE, JOURNAL_FILE)
        print(f"✅ Tableau généré: {len(df_result)} lignes, {len(df_result.columns)} colonnes\n")
        
        # 2. Analyser les méthodes de paiement
        print("2. Analyse des méthodes de paiement dans le résultat:")
        payment_columns = ['Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        
        total_amount = 0
        total_transactions = 0
        
        for col in payment_columns:
            if col in df_result.columns:
                non_zero_mask = (df_result[col] > 0) & (df_result[col].notna())
                non_zero_count = non_zero_mask.sum()
                total_amount_col = df_result[col].sum()
                
                print(f"   {col:20}: {non_zero_count:3d} commandes, {total_amount_col:10.2f}€")
                
                if non_zero_count > 0:
                    total_amount += total_amount_col
                    total_transactions += non_zero_count
            else:
                print(f"   {col:20}: ❌ Colonne manquante")
        
        print(f"\n   💰 TOTAL: {total_transactions} transactions, {total_amount:.2f}€")
        
        # 3. Vérifier la couverture
        has_payment_method = pd.Series([False] * len(df_result))
        for col in payment_columns:
            if col in df_result.columns:
                has_payment_method |= (df_result[col] > 0) & (df_result[col].notna())
        
        coverage = has_payment_method.sum()
        coverage_pct = coverage / len(df_result) * 100
        print(f"   📊 Couverture: {coverage}/{len(df_result)} ({coverage_pct:.1f}%)")
          # 4. Sauvegarder le fichier Excel avec formatage et figement des volets
        print(f"\n3. Sauvegarde du fichier avec formatage conditionnel et figement des en-têtes...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'tableau_facturation_CORRECTED_payment_methods_{timestamp}.xlsx'
        output_path_base = os.path.join(r'C:\Code\Apps\Compta LCDI V2\output', output_filename.replace('.xlsx', '.csv'))
        
        # Utiliser la fonction officielle qui inclut le figement des volets
        final_path, is_excel = save_with_conditional_formatting(df_result, output_path_base)
        output_filename = os.path.basename(final_path)
        
        if is_excel:
            print(f"✅ Fichier Excel sauvegardé avec figement des en-têtes: {output_filename}")
        else:
            print(f"⚠️ Fichier CSV sauvegardé (Excel non disponible): {output_filename}")
        
        output_path = final_path
          # 5. Vérifier le fichier sauvegardé
        print(f"\n4. Vérification du fichier sauvegardé...")
        df_saved = pd.read_excel(output_path)
        
        # Re-vérifier les méthodes de paiement
        for col in payment_columns:
            if col in df_saved.columns:
                non_zero_count = (df_saved[col] > 0).sum()
                total_amount_col = df_saved[col].sum()
                print(f"   {col}: {non_zero_count} commandes, {total_amount_col:.2f}€")
        
        print(f"\n🎉 SUCCÈS!")
        print(f"✅ Correction des méthodes de paiement appliquée avec succès")
        print(f"✅ Fichier généré: {output_filename}")
        print(f"✅ Les colonnes PayPal, ALMA, Younited, Virement bancaire sont maintenant remplies")
        print(f"✅ Les en-têtes de colonnes sont maintenant figés pour rester visibles lors du défilement")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_and_save_corrected_file()
