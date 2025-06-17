#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic simple des correspondances manquantes
"""

import pandas as pd
import os
import re

def diagnostic_correspondances():
    """Diagnostic rapide des correspondances"""
    print("=== DIAGNOSTIC CORRESPONDANCES ===\n")
    
    # Fichiers
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    try:
        # Lecture
        print("Lecture des fichiers...")
        df_orders = pd.read_csv(orders_file, encoding='utf-8')
        df_journal = pd.read_csv(journal_file, encoding='latin-1', delimiter=';')
        
        print(f"Commandes: {len(df_orders)} lignes")
        print(f"Journal: {len(df_journal)} lignes")
        
        # Commandes uniques après agrégation (comme dans app.py)
        commandes_uniques = df_orders.drop_duplicates(subset=['Name'], keep='first')
        print(f"Commandes après déduplication: {len(commandes_uniques)}")
        
        # Références du journal
        ref_journal = df_journal['Référence externe'].dropna().unique()
        print(f"Références journal: {len(ref_journal)}")
        
        # Correspondances directes
        correspondances = 0
        multiples = 0
        
        # Normaliser les commandes
        commandes_set = set()
        for cmd in commandes_uniques['Name']:
            if pd.notna(cmd):
                cmd_str = str(cmd).strip()
                commandes_set.add(cmd_str)
                if cmd_str.startswith('#'):
                    commandes_set.add(cmd_str[1:])  # Sans #
                else:
                    commandes_set.add(f"#{cmd_str}")  # Avec #
        
        # Analyser chaque référence du journal
        for ref in ref_journal:
            if pd.isna(ref):
                continue
            ref_str = str(ref).strip()
            
            # Référence multiple ?
            if ' ' in ref_str and ref_str.count('LCDI-') > 1:
                # Extraire les numéros
                numbers = re.findall(r'LCDI-(\d+)', ref_str)
                for num in numbers:
                    cmd1 = f"#LCDI-{num}"
                    cmd2 = f"LCDI-{num}"
                    if cmd1 in commandes_set or cmd2 in commandes_set:
                        multiples += 1
            else:
                # Référence simple
                if ref_str in commandes_set:
                    correspondances += 1
        
        total_correspondances = correspondances + multiples
        
        print(f"\nRésultats:")
        print(f"- Correspondances directes: {correspondances}")
        print(f"- Correspondances multiples: {multiples}")
        print(f"- Total théorique: {total_correspondances}")
        print(f"- Obtenu dans le tableau: 22")
        print(f"- Différence: {total_correspondances - 22}")
        
        # Vérifier si l'agrégation cause des pertes
        print(f"\nVérification agrégation:")
        print(f"- Lignes originales: {len(df_orders)}")
        print(f"- Après déduplication: {len(commandes_uniques)}")
        print(f"- Lignes perdues: {len(df_orders) - len(commandes_uniques)}")
        
        if len(df_orders) - len(commandes_uniques) > 0:
            print("⚠️  Des lignes sont perdues lors de l'agrégation!")
            
            # Vérifier quelles commandes sont dupliquées
            duplicates = df_orders[df_orders.duplicated(subset=['Name'], keep=False)]
            if len(duplicates) > 0:
                print(f"Commandes dupliquées: {len(duplicates)} lignes")
                duplicate_names = duplicates['Name'].unique()
                print(f"Nombres de commandes avec doublons: {len(duplicate_names)}")
                print(f"Exemples: {list(duplicate_names[:5])}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_correspondances()
