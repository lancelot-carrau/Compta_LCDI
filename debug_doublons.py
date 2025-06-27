#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour analyser les doublons dans l'Excel généré
"""

import pandas as pd
import os

def analyze_excel_duplicates():
    """Analyse les doublons dans l'Excel le plus récent"""
    
    print("=== ANALYSE DES DOUBLONS EXCEL ===\n")
    
    try:
        # Trouver le fichier Excel le plus récent
        output_dir = 'output'
        excel_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx') and 'Amazon' in f]
        
        if not excel_files:
            print("❌ Aucun fichier Excel trouvé")
            return
        
        latest_excel = max([os.path.join(output_dir, f) for f in excel_files], 
                          key=os.path.getctime)
        
        print(f"📊 Analyse du fichier: {os.path.basename(latest_excel)}")
        
        # Lire la structure complète d'abord
        df_raw = pd.read_excel(latest_excel, engine='openpyxl', header=None)
        print(f"📋 Structure: {len(df_raw)} lignes, {len(df_raw.columns)} colonnes")
        
        # Afficher les premières lignes pour debug
        print(f"\n=== STRUCTURE DU FICHIER ===")
        for i in range(min(5, len(df_raw))):
            row_data = df_raw.iloc[i].tolist()
            print(f"Ligne {i+1}: {row_data[:3]}...")  # Afficher les 3 premières colonnes
        
        # Lire les données en sautant les 2 premières lignes (totaux + titres)
        df = pd.read_excel(latest_excel, engine='openpyxl', skiprows=2)
        print(f"\n📋 Données (après skip): {len(df)} lignes de factures")
        print(f"Colonnes: {list(df.columns)}")
        
        if len(df.columns) < 2:
            print("❌ Structure Excel incorrecte")
            return
        
        # Analyser les doublons de factures
        facture_col = df.iloc[:, 1]  # Colonne Facture AMAZON
        factures_counts = facture_col.value_counts()
        doublons = factures_counts[factures_counts > 1]
        
        print(f"\n=== ANALYSE DES DOUBLONS ===")
        
        if len(doublons) == 0:
            print("✅ Aucun doublon détecté")
            return
        
        print(f"⚠️ {len(doublons)} factures en doublon détectées:")
        
        for facture, count in doublons.items():
            print(f"\n🔍 Facture: {facture} ({count} occurrences)")
            
            # Trouver toutes les lignes avec cette facture
            lignes_doublons = df[df.iloc[:, 1] == facture]
            
            for idx, (original_idx, row) in enumerate(lignes_doublons.iterrows()):
                ligne_excel = original_idx + 3  # +3 car 2 lignes sautées + index 0-based
                
                id_amazon = row.iloc[0] if pd.notna(row.iloc[0]) else "N/A"
                date_facture = row.iloc[2] if pd.notna(row.iloc[2]) else "N/A"
                pays = row.iloc[3] if pd.notna(row.iloc[3]) else "N/A"
                nom_contact = row.iloc[4] if pd.notna(row.iloc[4]) else "N/A"
                total = row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else "N/A"
                
                print(f"   Ligne {ligne_excel}: ID={id_amazon}, Date={date_facture}, Pays={pays}, Contact={nom_contact}, Total={total}")
        
        # Analyser spécifiquement les lignes 17 et 19 mentionnées
        print(f"\n=== ANALYSE LIGNES 17 ET 19 ===")
        
        if len(df) >= 17:
            ligne_17_idx = 14  # Index 14 = ligne 17 (car skip 2 lignes)
            ligne_19_idx = 16  # Index 16 = ligne 19
            
            if ligne_17_idx < len(df):
                ligne_17 = df.iloc[ligne_17_idx]
                print(f"Ligne 17 (Excel): Facture='{ligne_17.iloc[1]}', Pays='{ligne_17.iloc[3]}', Date='{ligne_17.iloc[2]}'")
            
            if ligne_19_idx < len(df):
                ligne_19 = df.iloc[ligne_19_idx]
                print(f"Ligne 19 (Excel): Facture='{ligne_19.iloc[1]}', Pays='{ligne_19.iloc[3]}', Date='{ligne_19.iloc[2]}'")
                
                if ligne_17_idx < len(df):
                    meme_facture = ligne_17.iloc[1] == ligne_19.iloc[1]
                    print(f"Même numéro de facture: {meme_facture}")
                    
                    if meme_facture:
                        print("🚨 PROBLÈME CONFIRMÉ: Doublons avec infos différentes!")
        
        # Statistiques générales
        print(f"\n=== STATISTIQUES ===")
        factures_uniques = len(factures_counts)
        total_lignes = len(df)
        print(f"📊 Total lignes: {total_lignes}")
        print(f"📊 Factures uniques: {factures_uniques}")
        print(f"📊 Différence (doublons): {total_lignes - factures_uniques}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_excel_duplicates()
