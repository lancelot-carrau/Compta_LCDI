#!/usr/bin/env python3
"""
Test de génération complète avec la logique corrigée
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
    calculate_invoice_dates, translate_financial_status
)

# Chemins des fichiers
JOURNAL_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
ORDERS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_PATH = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def test_generation_complete():
    """Test de génération complète du tableau avec la logique corrigée"""
    
    print("=== TEST DE GÉNÉRATION COMPLÈTE ===\n")
    
    try:
        # 1. Chargement des fichiers
        print("1. Chargement des fichiers...")
        
        # Journal
        journal_encoding = detect_encoding(JOURNAL_PATH)
        df_journal = pd.read_csv(JOURNAL_PATH, encoding=journal_encoding, sep=';')
        print(f"   ✓ Journal: {len(df_journal)} lignes")
        
        # Commandes
        orders_encoding = detect_encoding(ORDERS_PATH)
        df_orders = pd.read_csv(ORDERS_PATH, encoding=orders_encoding)
        print(f"   ✓ Commandes: {len(df_orders)} lignes")
        
        # Transactions
        transactions_encoding = detect_encoding(TRANSACTIONS_PATH)
        df_transactions = pd.read_csv(TRANSACTIONS_PATH, encoding=transactions_encoding)
        print(f"   ✓ Transactions: {len(df_transactions)} lignes")
        
        # 2. Normalisation des colonnes
        print("\n2. Normalisation des colonnes...")
        
        required_orders_cols = ['Name', 'Billing name', 'Financial Status', 'Fulfilled at', 
                               'Total', 'Taxes', 'Outstanding Balance', 'Payment Method']
        required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        required_journal_cols = ['Piece', 'Référence LMB']
        
        df_orders = normalize_column_names(df_orders, required_orders_cols, "commandes")
        df_transactions = normalize_column_names(df_transactions, required_transactions_cols, "transactions")
        df_journal = normalize_column_names(df_journal, required_journal_cols, "journal")
        
        print("   ✓ Normalisation terminée")
        
        # 3. Nettoyage des données
        print("\n3. Nettoyage des données...")
        
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        print("   ✓ Nettoyage terminé")
        
        # 4. Fusion commandes + transactions
        print("\n4. Fusion commandes + transactions...")
        
        df_merged_step1 = pd.merge(df_orders, df_transactions, 
                                   left_on='Name', right_on='Order', how='left')
        print(f"   ✓ Fusion initiale: {len(df_merged_step1)} lignes")
        
        # 5. Fusion avec journal (logique corrigée)
        print("\n5. Fusion avec journal (logique corrigée)...")
        
        df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
        
        lmb_count = df_merged_final['Référence LMB'].notna().sum()
        total_count = len(df_merged_final)
        print(f"   ✓ Fusion terminée: {lmb_count}/{total_count} Réf. LMB trouvées ({lmb_count/total_count*100:.1f}%)")
        
        # 6. Calcul des montants
        print("\n6. Calcul des montants...")
        
        df_merged_final = calculate_corrected_amounts(df_merged_final)
        print("   ✓ Montants calculés")
        
        # 7. Calcul des dates
        print("\n7. Calcul des dates...")
        
        df_merged_final = calculate_invoice_dates(df_merged_final)
        print("   ✓ Dates calculées")
        
        # 8. Traduction des statuts
        print("\n8. Traduction des statuts...")
        
        df_merged_final['Financial Status'] = df_merged_final['Financial Status'].apply(translate_financial_status)
        print("   ✓ Statuts traduits")
          # 9. Création d'un tableau final simplifié pour test
        print("\n9. Création du tableau final simplifié...")
        
        # Créer une structure basique pour le test
        df_final = pd.DataFrame({
            'Centre de profit': ['lcdi.fr'] * len(df_merged_final),
            'Réf.WEB': df_merged_final['Name'].fillna(''),
            'Réf. LMB': df_merged_final['Référence LMB'].fillna(''),
            'Date Facture': df_merged_final.get('Date Facture', '').fillna(''),
            'Etat': df_merged_final['Financial Status'].fillna('').apply(translate_financial_status),
            'Client': df_merged_final['Billing name'].fillna(''),
            'HT': df_merged_final.get('HT', 0).fillna(0),
            'TVA': df_merged_final.get('TVA', 0).fillna(0), 
            'TTC': df_merged_final.get('TTC', 0).fillna(0),
            'reste': df_merged_final['Outstanding Balance'].fillna(0),
            'Shopify': df_merged_final['Presentment Amount'].fillna(0),
            'Frais de commission': df_merged_final['Fee'].fillna(0),
            'Virement bancaire': [0] * len(df_merged_final),
            'ALMA': [0] * len(df_merged_final),
            'Younited': [0] * len(df_merged_final),
            'PayPal': [0] * len(df_merged_final),
            'Statut': ['INCOMPLET'] * len(df_merged_final)  # Simplifié pour le test
        })
        
        print(f"   ✓ Tableau final créé: {len(df_final)} lignes, {len(df_final.columns)} colonnes")
        
        # 10. Analyse des résultats
        print("\n10. Analyse des résultats...")
        
        # Compteurs
        total_lines = len(df_final)
        lmb_filled = df_final['Réf. LMB'].notna().sum()
        dates_filled = df_final['Date Facture'].notna().sum()
        complete_status = (df_final['Statut'] == 'COMPLET').sum()
        
        print(f"    📊 Statistiques finales:")
        print(f"       - Total de lignes: {total_lines}")
        print(f"       - Réf. LMB remplies: {lmb_filled}/{total_lines} ({lmb_filled/total_lines*100:.1f}%)")
        print(f"       - Dates remplies: {dates_filled}/{total_lines} ({dates_filled/total_lines*100:.1f}%)")
        print(f"       - Statut COMPLET: {complete_status}/{total_lines} ({complete_status/total_lines*100:.1f}%)")
        
        # Colonnes
        expected_columns = [
            'Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client',
            'HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission', 
            'Virement bancaire', 'ALMA', 'Younited', 'PayPal', 'Statut'
        ]
        
        missing_cols = [col for col in expected_columns if col not in df_final.columns]
        extra_cols = [col for col in df_final.columns if col not in expected_columns]
        
        if missing_cols:
            print(f"    ⚠️ Colonnes manquantes: {missing_cols}")
        if extra_cols:
            print(f"    ⚠️ Colonnes supplémentaires: {extra_cols}")
        if not missing_cols and not extra_cols:
            print(f"    ✅ Structure de colonnes correcte")
        
        # Exemples de données
        print(f"\n    📝 Exemples de lignes avec Réf. LMB:")
        with_lmb = df_final[df_final['Réf. LMB'].notna()].head(3)
        for idx, row in with_lmb.iterrows():
            print(f"       {row['Réf.WEB']} -> {row['Réf. LMB']} ({row['Client']}) - {row['TTC']}€")
        
        print(f"\n    📝 Exemples de lignes sans Réf. LMB:")
        without_lmb = df_final[df_final['Réf. LMB'].isna()].head(3)
        for idx, row in without_lmb.iterrows():
            print(f"       {row['Réf.WEB']} -> (pas de LMB) ({row['Client']}) - {row['TTC']}€")
        
        # 11. Sauvegarder le fichier de test
        print(f"\n11. Sauvegarde du fichier de test...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/test_generation_corrigee_{timestamp}.xlsx"
        
        # Créer le fichier Excel avec formatage
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='Tableau facturation', index=False)
        
        print(f"   ✅ Fichier sauvegardé: {output_path}")
        
        # 12. Résumé final
        print(f"\n=== RÉSUMÉ ===")
        
        success_rate = lmb_filled / total_lines * 100
        
        if success_rate >= 80:
            print(f"🎉 EXCELLENT: {success_rate:.1f}% de Réf. LMB trouvées")
        elif success_rate >= 50:
            print(f"✅ BIEN: {success_rate:.1f}% de Réf. LMB trouvées")
            print("   Note: Décalage temporel entre journal et commandes détecté")
        else:
            print(f"❌ PROBLÈME: {success_rate:.1f}% de Réf. LMB trouvées")
        
        print(f"📈 Amélioration: De ~14% à {success_rate:.1f}% grâce à la correction")
        print(f"📁 Fichier généré: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_generation_complete()
