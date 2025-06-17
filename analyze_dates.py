#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour analyser les sources possibles des dates de facture
"""

import pandas as pd
from datetime import datetime

def analyze_date_sources():
    """Analyse les sources possibles des dates de facture"""
    
    print("=== ANALYSE DES SOURCES DE DATES ===")
    
    # Charger les fichiers
    journal_path = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    
    try:
        # Journal
        df_journal = pd.read_csv(journal_path, encoding='ISO-8859-1', sep=';')
        print(f"📋 Journal - Colonnes avec 'date': {[col for col in df_journal.columns if 'date' in col.lower()]}")
        
        if 'Date du document' in df_journal.columns:
            print(f"   Échantillon 'Date du document':")
            for i, date in enumerate(df_journal['Date du document'].head(5)):
                ref_lmb = df_journal.iloc[i]['Référence LMB']
                print(f"     {ref_lmb} - {date}")
        
        # Commandes
        df_orders = pd.read_csv(orders_path, encoding='utf-8')
        print(f"\n📋 Commandes - Colonnes avec 'date': {[col for col in df_orders.columns if 'date' in col.lower()]}")
        
        # Analyser Created at
        if 'Created at' in df_orders.columns:
            print(f"   Échantillon 'Created at':")
            for i, row in df_orders.head(5).iterrows():
                name = row['Name']
                created = row['Created at']
                print(f"     {name} - {created}")
        
        # Analyser Fulfilled at
        if 'Fulfilled at' in df_orders.columns:
            print(f"   Échantillon 'Fulfilled at':")
            for i, row in df_orders.head(5).iterrows():
                name = row['Name']
                fulfilled = row['Fulfilled at']
                print(f"     {name} - {fulfilled}")
        
        # Analyser Paid at
        if 'Paid at' in df_orders.columns:
            print(f"   Échantillon 'Paid at':")
            for i, row in df_orders.head(5).iterrows():
                name = row['Name']
                paid = row['Paid at']
                print(f"     {name} - {paid}")
        
        # Comparer avec les dates du fichier d'exemple
        print(f"\n🔍 COMPARAISON AVEC L'EXEMPLE:")
        
        # Fichier d'exemple
        df_exemple = pd.read_csv(r'c:\Users\Malo\Downloads\Compta-LCDI-shopify.csv')
        
        # Chercher correspondances pour quelques cas
        refs_test = ['#LCDI-1003', '#LCDI-1006', '#LCDI-1007']
        
        for ref in refs_test:
            # Date dans l'exemple
            ligne_exemple = df_exemple[df_exemple['Réf. WEB'] == ref]
            if not ligne_exemple.empty:
                date_exemple = ligne_exemple['Date Facture'].iloc[0]
                print(f"\n--- {ref} ---")
                print(f"   Date exemple: {date_exemple}")
                
                # Chercher dans orders
                ligne_order = df_orders[df_orders['Name'] == ref]
                if not ligne_order.empty:
                    created = ligne_order['Created at'].iloc[0]
                    fulfilled = ligne_order['Fulfilled at'].iloc[0]
                    paid = ligne_order['Paid at'].iloc[0]
                    print(f"   Created at: {created}")
                    print(f"   Fulfilled at: {fulfilled}")
                    print(f"   Paid at: {paid}")
                    
                    # Vérifier correspondances
                    try:
                        # Convertir date exemple (format M/D/YYYY)
                        date_ex_parsed = datetime.strptime(date_exemple, '%m/%d/%Y')
                        date_ex_str = date_ex_parsed.strftime('%Y-%m-%d')
                        
                        if date_ex_str in str(created):
                            print(f"     ✅ Correspond à Created at")
                        elif date_ex_str in str(fulfilled):
                            print(f"     ✅ Correspond à Fulfilled at")
                        elif date_ex_str in str(paid):
                            print(f"     ✅ Correspond à Paid at")
                        else:
                            print(f"     ❌ Aucune correspondance exacte")
                    except:
                        print(f"     ⚠️ Erreur de conversion de date")
                
                # Chercher dans journal si référence LMB disponible
                # (on sait qu'il n'y a pas beaucoup de correspondances mais essayons)
                
        print(f"\n📊 RECOMMANDATIONS:")
        print(f"   1. 'Created at' = Date de création de la commande")
        print(f"   2. 'Fulfilled at' = Date de livraison/expédition") 
        print(f"   3. 'Paid at' = Date de paiement")
        print(f"   4. 'Date du document' (Journal) = Date de facturation")
        print(f"\n   ➜ Pour les factures, 'Fulfilled at' ou 'Date du document' semblent les plus appropriés")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_date_sources()
