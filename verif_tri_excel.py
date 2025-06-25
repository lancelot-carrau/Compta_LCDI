#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification du tri par date dans le fichier Excel généré
"""
import pandas as pd
import os
from datetime import datetime

# Chemin vers le fichier Excel le plus récent
output_dir = "output"
excel_file = "Compta_LCDI_Amazon_23_06_2025_15_29_47.xlsx"  # Le dernier généré
excel_path = os.path.join(output_dir, excel_file)

print(f"📊 Vérification du tri par date dans : {excel_file}")
print("=" * 70)

try:
    # Lire le fichier Excel
    df = pd.read_excel(excel_path)
    print(f"✅ Fichier Excel lu avec succès")
    print(f"📋 Nombre de lignes : {len(df)}")
    print(f"📋 Colonnes : {list(df.columns)}")
    print()
    
    # Afficher les premières lignes pour voir la structure
    print("🔍 Premières lignes du fichier Excel :")
    print("-" * 50)
    print(df.head(10).to_string(index=False))
    print()
    
    # Chercher les colonnes contenant des dates
    date_columns = []
    for col in df.columns:
        if 'date' in col.lower() or 'facture' in col.lower():
            date_columns.append(col)
    
    print(f"📅 Colonnes potentielles de date trouvées : {date_columns}")
    
    # Afficher les dates dans l'ordre d'apparition
    if date_columns:
        date_col = date_columns[0]  # Prendre la première colonne de date
        print(f"\n📅 Dates dans l'ordre d'apparition (colonne '{date_col}') :")
        print("-" * 50)
          dates_found = []
        for idx, row in df.iterrows():
            date_val = row[date_col]
            if pd.notna(date_val) and str(date_val).strip() != '':
                dates_found.append((int(idx), str(date_val)))
                print(f"Ligne {int(idx) + 1}: {date_val}")
        
        if dates_found:
            print(f"\n📊 Total de {len(dates_found)} dates trouvées")
            print("✅ Vérification du tri : les dates devraient être dans l'ordre croissant")
            
            # Vérifier si les dates sont triées
            sorted_check = True
            for i in range(1, len(dates_found)):
                try:
                    date1 = datetime.strptime(dates_found[i-1][1], '%d/%m/%Y')
                    date2 = datetime.strptime(dates_found[i][1], '%d/%m/%Y')
                    if date1 > date2:
                        sorted_check = False
                        print(f"❌ Erreur de tri : {dates_found[i-1][1]} > {dates_found[i][1]}")
                        break
                except ValueError as e:
                    print(f"⚠️  Erreur de format de date : {e}")
            
            if sorted_check:
                print("✅ LE TRI PAR DATE EST CORRECT (plus ancienne en haut)")
            else:
                print("❌ LE TRI PAR DATE N'EST PAS CORRECT")
        else:
            print("⚠️  Aucune date valide trouvée")
    else:
        print("⚠️  Aucune colonne de date trouvée")
        
except Exception as e:
    print(f"❌ Erreur lors de la lecture du fichier Excel : {e}")
    print(f"Fichier : {excel_path}")
    print(f"Existe : {os.path.exists(excel_path)}")
