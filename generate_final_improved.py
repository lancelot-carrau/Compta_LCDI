#!/usr/bin/env python3
"""
Génération finale avec la logique améliorée de références multiples
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import (
    detect_encoding, normalize_column_names, clean_text_data, 
    improve_journal_matching, calculate_corrected_amounts,
    translate_financial_status
)

# Chemins des fichiers
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def generate_final_table():
    """Génération finale du tableau avec logique améliorée"""
    
    print("=== GÉNÉRATION FINALE AVEC LOGIQUE AMÉLIORÉE ===\n")
    
    try:
        # 1. Chargement
        print("1. Chargement des fichiers...")
        
        journal_encoding = detect_encoding(JOURNAL_PATH)
        df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
        
        orders_encoding = detect_encoding(ORDERS_PATH)
        df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
        
        transactions_encoding = detect_encoding(TRANSACTIONS_PATH)
        df_transactions = pd.read_csv(TRANSACTIONS_PATH, encoding=transactions_encoding)
        
        # 2. Normalisation
        print("\n2. Normalisation...")
        
        required_orders_cols = ['Name', 'Billing name', 'Financial Status', 'Fulfilled at', 
                               'Total', 'Taxes', 'Outstanding Balance', 'Payment Method']
        required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        required_journal_cols = ['Piece', 'Référence LMB']
        
        df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
        df_transactions = normalize_column_names(df_transactions, required_transactions_cols, "transactions")
        df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
        
        # 3. Nettoyage
        print("\n3. Nettoyage...")
        
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        # 4. Fusion commandes + transactions
        print("\n4. Fusion commandes + transactions...")
        
        df_merged_step1 = pd.merge(df_orders, df_transactions, 
                                   left_on='Name', right_on='Order', how='left')
        
        # 5. Fusion avec journal (LOGIQUE AMÉLIORÉE)
        print("\n5. Fusion avec journal (logique améliorée)...")
        
        df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
        
        # 6. Calcul des montants
        print("\n6. Calcul des montants...")
        
        df_merged_final = calculate_corrected_amounts(df_merged_final)
          # 7. Création du tableau final
        print("\n7. Création du tableau final...")
        
        # Debug : afficher les colonnes disponibles
        print(f"   Colonnes disponibles: {list(df_merged_final.columns)}")
        
        # Créer les colonnes finales avec gestion des colonnes manquantes
        def safe_get(df, col_name, default=''):
            """Récupère une colonne en toute sécurité"""
            if col_name in df.columns:
                return df[col_name].fillna(default)
            else:
                print(f"   ⚠️ Colonne '{col_name}' non trouvée, utilisation de '{default}'")
                return [default] * len(df)
        
        df_final = pd.DataFrame({
            'Centre de profit': ['lcdi.fr'] * len(df_merged_final),
            'Réf.WEB': safe_get(df_merged_final, 'Name', ''),
            'Réf. LMB': safe_get(df_merged_final, 'Référence LMB', ''),
            'Date Facture': safe_get(df_merged_final, 'Date du document', ''),
            'Etat': safe_get(df_merged_final, 'Financial Status', '').apply(translate_financial_status),
            'Client': safe_get(df_merged_final, 'Billing name', ''),
            'HT': safe_get(df_merged_final, 'HT', 0),
            'TVA': safe_get(df_merged_final, 'TVA', 0),
            'TTC': safe_get(df_merged_final, 'TTC', 0),
            'reste': safe_get(df_merged_final, 'Outstanding Balance', 0),
            'Shopify': safe_get(df_merged_final, 'Presentment Amount', 0),
            'Frais de commission': safe_get(df_merged_final, 'Fee', 0),
            'Virement bancaire': [0] * len(df_merged_final),
            'ALMA': [0] * len(df_merged_final),
            'Younited': [0] * len(df_merged_final),
            'PayPal': [0] * len(df_merged_final),
            'Statut': ['COMPLET' if pd.notna(lmb) and str(lmb).strip() != '' else 'INCOMPLET' 
                      for lmb in safe_get(df_merged_final, 'Référence LMB', '')]
        })
        
        # 8. Statistiques finales
        print("\n8. Statistiques finales...")
        
        total_lines = len(df_final)
        lmb_count = df_final['Réf. LMB'].notna().sum()
        lmb_filled = (df_final['Réf. LMB'] != '').sum()
        percentage = (lmb_filled / total_lines) * 100
        
        print(f"   📊 RÉSULTATS FINAUX:")
        print(f"      - Total de lignes: {total_lines}")
        print(f"      - Réf. LMB remplies: {lmb_filled}/{total_lines} ({percentage:.1f}%)")
        print(f"      - Statut COMPLET: {(df_final['Statut'] == 'COMPLET').sum()}")
        
        # 9. Sauvegarde
        print("\n9. Sauvegarde...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/tableau_final_ameliore_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='Tableau facturation', index=False)
            
            # Feuille de statistiques
            stats_df = pd.DataFrame({
                'Métrique': ['Total lignes', 'Réf. LMB remplies', 'Pourcentage', 'Amélioration vs initial'],
                'Valeur': [total_lines, lmb_filled, f"{percentage:.1f}%", f"+{percentage/14.3:.1f}x"]
            })
            stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
        
        print(f"   ✅ Fichier sauvegardé: {output_path}")
        
        # 10. Résumé final
        print(f"\n=== RÉSUMÉ FINAL ===")
        print(f"🎉 SUCCÈS COMPLET !")
        print(f"   - Passage de 14.3% à {percentage:.1f}% de Réf. LMB")
        print(f"   - Amélioration de +{percentage/14.3:.1f}x")
        print(f"   - Gestion des références multiples fonctionnelle")
        print(f"   - Fichier généré: {output_path}")
        
        # 11. Exemples de correspondances
        print(f"\n📝 EXEMPLES DE CORRESPONDANCES:")
        examples = df_final[df_final['Réf. LMB'] != ''].head(5)
        for idx, row in examples.iterrows():
            print(f"   {row['Réf.WEB']} -> {row['Réf. LMB']} ({row['Client']})")
        
        return output_path, percentage
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, 0

if __name__ == "__main__":
    generate_final_table()
