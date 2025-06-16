#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic des informations manquantes dans le tableau final
"""

import pandas as pd
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def diagnostic_info_manquantes():
    """Diagnostic des informations manquantes ou partielles"""
    
    # Chemins vers les vrais fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_path = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    
    print("=== DIAGNOSTIC DES INFORMATIONS MANQUANTES ===")
    
    try:
        # Traiter les fichiers
        df_result = generate_consolidated_billing_table(orders_path, transactions_path, journal_path)
        
        if df_result is not None and not df_result.empty:
            print(f"\n✅ Traitement réussi ! {len(df_result)} lignes générées.")
            
            # Analyser les différents types d'informations manquantes
            print("\n📊 ANALYSE DES INFORMATIONS MANQUANTES:")
            
            # 1. Réf. LMB manquantes (pas de correspondance dans le journal)
            ref_lmb_manquantes = df_result['Réf. LMB'].fillna('').eq('').sum()
            print(f"\n🏷️ Réf. LMB:")
            print(f"  - Références trouvées: {len(df_result) - ref_lmb_manquantes}")
            print(f"  - Références manquantes: {ref_lmb_manquantes} ⚠️")
            
            # 2. TTC manquants (pas de transaction correspondante)
            ttc_manquants = (df_result['TTC'] == 0).sum()
            print(f"\n💰 TTC (Transactions):")
            print(f"  - TTC disponibles: {len(df_result) - ttc_manquants}")
            print(f"  - TTC manquants (=0): {ttc_manquants} ⚠️")
            
            # 3. Date de facture manquantes
            dates_manquantes = df_result['Date Facture'].fillna('').eq('').sum()
            print(f"\n📅 Date Facture:")
            print(f"  - Dates disponibles: {len(df_result) - dates_manquantes}")
            print(f"  - Dates manquantes: {dates_manquantes} ⚠️")
            
            # 4. États manquants
            etats_manquants = df_result['Etat'].fillna('').eq('').sum()
            print(f"\n📋 État:")
            print(f"  - États disponibles: {len(df_result) - etats_manquants}")
            print(f"  - États manquants: {etats_manquants} ⚠️")
            
            # 5. Cas complexes : commandes avec info partielle
            print(f"\n🔍 CAS D'INFORMATIONS PARTIELLES:")
            
            # Cas 1: Commande sans transaction (TTC=0 mais commande existe)
            commandes_sans_transaction = df_result[df_result['TTC'] == 0]
            if not commandes_sans_transaction.empty:
                print(f"\n❌ {len(commandes_sans_transaction)} commandes SANS transaction (TTC manquant):")
                for idx, row in commandes_sans_transaction.head(10).iterrows():
                    print(f"  Ligne {idx}: Réf={row['Réf.WEB']}, Client={row['Client'][:30]}, TTC={row['TTC']}, État={row['Etat']}")
            
            # Cas 2: Commande sans référence LMB (pas dans le journal)
            commandes_sans_lmb = df_result[df_result['Réf. LMB'].fillna('').eq('')]
            if not commandes_sans_lmb.empty:
                print(f"\n❌ {len(commandes_sans_lmb)} commandes SANS Réf. LMB (pas dans le journal):")
                for idx, row in commandes_sans_lmb.head(10).iterrows():
                    print(f"  Ligne {idx}: Réf={row['Réf.WEB']}, Client={row['Client'][:30]}, TTC={row['TTC']}, LMB='{row['Réf. LMB']}'")
            
            # Cas 3: Données complètes (référence croisée)
            donnees_completes = df_result[
                (df_result['TTC'] > 0) & 
                (df_result['Réf. LMB'].fillna('').ne('')) &
                (df_result['Date Facture'].fillna('').ne(''))
            ]
            print(f"\n✅ {len(donnees_completes)} lignes avec DONNÉES COMPLÈTES")
            
            return True
                
        else:
            print(f"\n❌ ERREUR: Aucun résultat généré!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = diagnostic_info_manquantes()
    if success:
        print(f"\n🔍 DIAGNOSTIC TERMINÉ")
    else:
        print(f"\n💥 DIAGNOSTIC ÉCHOUÉ")
