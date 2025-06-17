#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour analyser pourquoi le fallback ne fonctionne pas
"""

import pandas as pd

def analyze_fallback_issue():
    """Analyse le problème de fallback"""
    
    # Charger le fichier des commandes
    orders_path = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    df_orders = pd.read_csv(orders_path, encoding='utf-8')
    
    print("=== ANALYSE DU PROBLÈME DE FALLBACK ===")
    
    # Chercher LCDI-1003
    ligne_1003 = df_orders[df_orders['Name'].str.contains('LCDI-1003', na=False)]
    
    if not ligne_1003.empty:
        print(f"\n📋 Commande LCDI-1003 trouvée:")
        print(f"   Name: {ligne_1003['Name'].iloc[0]}")
        print(f"   Total: {ligne_1003['Total'].iloc[0]}")
        print(f"   Taxes: {ligne_1003['Taxes'].iloc[0]}")
        print(f"   Subtotal: {ligne_1003['Subtotal'].iloc[0]}")
        print(f"   Client: {ligne_1003['Billing Name'].iloc[0]}")
    else:
        print(f"\n❌ Commande LCDI-1003 NON TROUVÉE dans orders_export")
        
        # Chercher toutes les commandes qui contiennent 1003
        matches = df_orders[df_orders['Name'].str.contains('1003', na=False)]
        print(f"\n🔍 Commandes contenant '1003':")
        for _, row in matches.iterrows():
            print(f"   {row['Name']} - {row['Billing Name']} - Total: {row['Total']}")
    
    # Chercher d'autres commandes problématiques
    refs_test = ['LCDI-1006', 'LCDI-1007', 'LCDI-1008', 'LCDI-1010']
    
    print(f"\n🔍 ANALYSE DES AUTRES COMMANDES PROBLÉMATIQUES :")
    
    for ref in refs_test:
        ligne = df_orders[df_orders['Name'].str.contains(ref, na=False)]
        if not ligne.empty:
            print(f"\n✅ {ref} trouvée:")
            print(f"   Name: {ligne['Name'].iloc[0]}")
            print(f"   Total: {ligne['Total'].iloc[0]}")
            print(f"   Client: {ligne['Billing Name'].iloc[0]}")
        else:
            print(f"\n❌ {ref} NON TROUVÉE")
            # Chercher des correspondances partielles
            matches = df_orders[df_orders['Name'].str.contains(ref.split('-')[1], na=False)]
            if not matches.empty:
                print(f"   Correspondances partielles:")
                for _, row in matches.head(3).iterrows():
                    print(f"     {row['Name']} - {row['Billing Name']}")
    
    # Statistiques générales
    print(f"\n📊 STATISTIQUES GÉNÉRALES:")
    print(f"   Total commandes: {len(df_orders)}")
    print(f"   Commandes uniques: {df_orders['Name'].nunique()}")
    print(f"   Échantillon des noms de commandes:")
    for name in df_orders['Name'].head(10):
        print(f"     {name}")

if __name__ == "__main__":
    analyze_fallback_issue()
