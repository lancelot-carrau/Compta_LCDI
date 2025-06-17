#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test final : génération complète avec les vrais fichiers pour vérifier la correction
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Ajouter le dossier parent au chemin pour importer app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importer les fonctions nécessaires
from app import (
    normalize_column_names, validate_required_columns, clean_text_data,
    format_date_to_french, improve_journal_matching, calculate_corrected_amounts,
    calculate_invoice_dates, translate_financial_status, categorize_payment_method,
    fill_missing_data_indicators
)

def generer_tableau_final():
    """Génère le tableau final avec les vraies données"""
    print("=== GÉNÉRATION TABLEAU FINAL AVEC CORRECTION ===\n")
    
    # Chemins des fichiers
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    # Vérifier que les fichiers existent
    for name, path in [("Commandes", orders_file), ("Transactions", transactions_file), ("Journal", journal_file)]:
        if not os.path.exists(path):
            print(f"❌ Fichier {name} non trouvé: {path}")
            return None
    
    print("✓ Tous les fichiers source sont présents")
    
    try:        # ÉTAPE 1: Lecture des fichiers
        print("\n1. Lecture des fichiers...")
        df_orders = pd.read_csv(orders_file, encoding='utf-8')
        df_transactions = pd.read_csv(transactions_file, encoding='utf-8')
        
        # Essayer différents encodages pour le journal
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df_journal = None
        
        for encoding in encodings:
            try:
                df_journal = pd.read_csv(journal_file, encoding=encoding, delimiter=';')
                print(f"   - Journal lu avec succès (encodage: {encoding})")
                break
            except UnicodeDecodeError:
                continue
        
        if df_journal is None:
            print("❌ Impossible de lire le fichier journal avec les encodages testés")
            return None
        
        print(f"   - Commandes: {len(df_orders)} lignes")
        print(f"   - Transactions: {len(df_transactions)} lignes")
        print(f"   - Journal: {len(df_journal)} lignes")
        
        # ÉTAPE 2: Normalisation des colonnes
        print("\n2. Normalisation des colonnes...")
        required_orders_cols = ['Name', 'Fulfilled at', 'Billing name', 'Financial Status', 'Tax 1 Value', 'Outstanding Balance', 'Payment Method', 'Total', 'Taxes']
        df_orders = normalize_column_names(df_orders, required_orders_cols, 'commandes')
        validate_required_columns(df_orders, required_orders_cols, "fichier des commandes")
        
        required_trans_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']
        df_transactions = normalize_column_names(df_transactions, required_trans_cols, 'transactions')
        validate_required_columns(df_transactions, required_trans_cols, "fichier des transactions")
        
        required_journal_cols = ['Piece', 'Référence LMB']
        df_journal = normalize_column_names(df_journal, required_journal_cols, 'journal')
        validate_required_columns(df_journal, required_journal_cols, "fichier journal")
        
        # ÉTAPE 3: Nettoyage des données
        print("\n3. Nettoyage des données...")
        df_orders = clean_text_data(df_orders, ['Name', 'Billing name', 'Financial Status', 'Payment Method'])
        df_transactions = clean_text_data(df_transactions, ['Order'])
        df_journal = clean_text_data(df_journal, ['Piece', 'Référence LMB'])
        
        # Formatage des dates
        df_orders['Fulfilled at'] = df_orders['Fulfilled at'].apply(format_date_to_french)
        
        # Formatage des montants
        monetary_cols_orders = ['Tax 1 Value', 'Outstanding Balance', 'Total', 'Taxes']
        for col in monetary_cols_orders:
            if col in df_orders.columns:
                df_orders[col] = pd.to_numeric(df_orders[col], errors='coerce').fillna(0)
        
        monetary_cols_transactions = ['Presentment Amount', 'Fee', 'Net']
        for col in monetary_cols_transactions:
            if col in df_transactions.columns:
                df_transactions[col] = pd.to_numeric(df_transactions[col], errors='coerce').fillna(0)
        
        # ÉTAPE 4: Agrégation des commandes
        print("\n4. Agrégation des commandes...")
        df_orders_aggregated = df_orders.drop_duplicates(subset=['Name'], keep='first')
        print(f"   - Après agrégation: {len(df_orders_aggregated)} lignes")
        df_orders = df_orders_aggregated
        
        # ÉTAPE 5: Agrégation des transactions
        print("\n5. Agrégation des transactions...")
        df_transactions_aggregated = df_transactions.groupby('Order').agg({
            'Presentment Amount': 'sum',
            'Fee': 'sum',
            'Net': 'sum'
        }).reset_index()
        print(f"   - Après agrégation: {len(df_transactions_aggregated)} lignes")
        
        # ÉTAPE 6: Fusion des DataFrames
        print("\n6. Fusion des DataFrames...")
        df_merged_step1 = pd.merge(df_orders, df_transactions_aggregated, 
                                  left_on='Name', right_on='Order', how='left')
        print(f"   - Après fusion commandes-transactions: {len(df_merged_step1)} lignes")
        
        # Fusion avec journal (avec amélioration)
        print("   - Application de la fusion améliorée avec journal...")
        df_merged_final = improve_journal_matching(df_merged_step1, df_journal)
        print(f"   - Après fusion avec journal: {len(df_merged_final)} lignes")
        
        # Diagnostic
        ref_lmb_non_nulles = df_merged_final['Référence LMB'].notna().sum()
        print(f"   - Références LMB trouvées: {ref_lmb_non_nulles}/{len(df_merged_final)} ({ref_lmb_non_nulles/len(df_merged_final)*100:.1f}%)")
        
        # ÉTAPE 7: Création du tableau final
        print("\n7. Création du tableau final...")
        df_final = pd.DataFrame()
        
        df_final['Centre de profit'] = 'lcdi.fr'
        df_final['Réf.WEB'] = df_merged_final['Name']
        df_final['Réf. LMB'] = df_merged_final['Référence LMB'].fillna('')
        df_final['Date Facture'] = calculate_invoice_dates(df_merged_final)
        df_final['Etat'] = df_merged_final['Financial Status'].fillna('').apply(translate_financial_status)
        df_final['Client'] = df_merged_final['Billing name'].fillna('')
        
        # Calculs des montants (avec correction)
        print("   - Calcul des montants avec correction...")
        corrected_amounts = calculate_corrected_amounts(df_merged_final)
        
        df_final['HT'] = corrected_amounts['HT']
        df_final['TVA'] = corrected_amounts['TVA']
        df_final['TTC'] = corrected_amounts['TTC']
        df_final['reste'] = df_merged_final['Outstanding Balance'].fillna(0)
        df_final['Shopify'] = df_merged_final['Net'].fillna(0)
        df_final['Frais de commission'] = df_merged_final['Fee'].fillna(0)
        
        # Traitement des méthodes de paiement
        payment_categorization = df_merged_final.apply(
            lambda row: categorize_payment_method(row['Payment Method'], row['Presentment Amount']), 
            axis=1
        )
        
        df_final['Virement bancaire'] = [pm['Virement bancaire'] for pm in payment_categorization]
        df_final['ALMA'] = [pm['ALMA'] for pm in payment_categorization]
        df_final['Younited'] = [pm['Younited'] for pm in payment_categorization]
        df_final['PayPal'] = [pm['PayPal'] for pm in payment_categorization]
        
        # ÉTAPE 8: Nettoyage final
        print("\n8. Nettoyage final...")
        
        # Remplacer les NaN par des chaînes vides pour les colonnes texte
        text_columns = ['Centre de profit', 'Réf.WEB', 'Réf. LMB', 'Date Facture', 'Etat', 'Client']
        for col in text_columns:
            df_final[col] = df_final[col].fillna('')
        
        # Arrondir les montants
        numeric_columns = ['HT', 'TVA', 'TTC', 'reste', 'Shopify', 'Frais de commission', 
                          'Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        for col in numeric_columns:
            df_final[col] = df_final[col].round(2)
        
        # Ajouter les informations de statut
        df_final = fill_missing_data_indicators(df_final, df_merged_final)
        
        # ÉTAPE 9: Sauvegarde
        print("\n9. Sauvegarde du fichier...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/tableau_facturation_final_corrige_{timestamp}.xlsx"
        
        os.makedirs("output", exist_ok=True)
        df_final.to_excel(output_file, index=False)
        
        print(f"✅ Fichier généré: {output_file}")
        
        # ÉTAPE 10: Vérification spécifique des commandes 1020/1021
        print("\n10. Vérification des commandes 1020/1021...")
        
        mask_1020 = df_final['Réf.WEB'].str.contains('1020', na=False)
        mask_1021 = df_final['Réf.WEB'].str.contains('1021', na=False)
        
        lines_1020 = df_final[mask_1020]
        lines_1021 = df_final[mask_1021]
        
        print(f"   - Lignes LCDI-1020: {len(lines_1020)}")
        print(f"   - Lignes LCDI-1021: {len(lines_1021)}")
        
        if len(lines_1020) > 0:
            row = lines_1020.iloc[0]
            print(f"   - LCDI-1020: TTC={row['TTC']}€, HT={row['HT']}€, Réf.LMB='{row['Réf. LMB']}'")
        
        if len(lines_1021) > 0:
            row = lines_1021.iloc[0]
            print(f"   - LCDI-1021: TTC={row['TTC']}€, HT={row['HT']}€, Réf.LMB='{row['Réf. LMB']}'")
        
        # Vérification finale
        if len(lines_1020) > 0 and len(lines_1021) > 0:
            ttc_1020 = lines_1020.iloc[0]['TTC']
            ttc_1021 = lines_1021.iloc[0]['TTC']
            
            if ttc_1020 != ttc_1021:
                print("   ✅ Correction réussie: les montants sont différents (pas de duplication)")
            else:
                print("   ❌ Problème: les montants sont identiques (duplication)")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    output_file = generer_tableau_final()
    
    if output_file:
        print(f"\n🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
        print(f"Fichier: {output_file}")
        print("\nLe fichier contient la correction pour les références multiples.")
        print("Vous pouvez maintenant l'ouvrir pour vérifier les résultats.")
    else:
        print("\n❌ Échec de la génération")
