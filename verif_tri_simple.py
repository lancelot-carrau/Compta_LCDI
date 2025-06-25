#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification simple du tri par date dans le fichier Excel
"""
import pandas as pd
import os
from datetime import datetime

# Chemin vers le fichier Excel le plus récent
output_dir = "output"
excel_file = "Compta_LCDI_Amazon_23_06_2025_15_45_18.xlsx"
excel_path = os.path.join(output_dir, excel_file)

print(f"📊 Vérification du tri par date dans : {excel_file}")
print("=" * 70)

try:
    # Lire le fichier Excel
    df = pd.read_excel(excel_path, header=1)  # Les vraies données commencent à la ligne 2
    print(f"✅ Fichier Excel lu avec succès")
    print(f"📋 Nombre de lignes de données : {len(df)}")
    print()
    
    # Afficher les données complètes
    print("🔍 Données du fichier Excel :")
    print("-" * 80)
    for i, row in df.iterrows():
        print(f"Ligne {i + 1}:")
        for j, value in enumerate(row):
            if pd.notna(value):
                print(f"  Col{j}: {value}")
        print()
    
    # Chercher la colonne de date (généralement colonne 2, index 2)
    if len(df.columns) >= 3:
        print("📅 Dates extraites (colonne 2 - DATE FACTURE) :")
        print("-" * 50)
        
        dates_found = []
        for i in range(len(df)):
            try:
                date_val = df.iloc[i, 2]  # Colonne 2 = DATE FACTURE
                if pd.notna(date_val) and str(date_val).strip() != '':
                    dates_found.append(str(date_val).strip())
                    print(f"Ligne {i + 1}: {date_val}")
            except Exception as e:
                print(f"Erreur ligne {i + 1}: {e}")
        
        if dates_found:
            print(f"\n📊 Total de {len(dates_found)} dates trouvées")
            print("✅ Vérification du tri : les dates devraient être dans l'ordre croissant")
            print("-" * 50)
            
            # Convertir et afficher les dates avec leur ordre chronologique
            parsed_dates = []
            for i, date_str in enumerate(dates_found):
                try:
                    parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                    parsed_dates.append((i + 1, date_str, parsed_date))
                    print(f"Ligne {i + 1}: {date_str} → {parsed_date.strftime('%Y-%m-%d')}")
                except ValueError as e:
                    print(f"⚠️  Erreur de format ligne {i + 1} ({date_str}): {e}")
            
            # Vérifier si les dates sont triées
            if len(parsed_dates) > 1:
                sorted_check = True
                print("\n🔍 Vérification du tri chronologique:")
                for i in range(1, len(parsed_dates)):
                    prev_date = parsed_dates[i-1][2]
                    curr_date = parsed_dates[i][2]
                    if prev_date > curr_date:
                        sorted_check = False
                        print(f"❌ Erreur de tri : {parsed_dates[i-1][1]} ({prev_date.strftime('%Y-%m-%d')}) > {parsed_dates[i][1]} ({curr_date.strftime('%Y-%m-%d')})")
                    else:
                        print(f"✅ OK : {parsed_dates[i-1][1]} ({prev_date.strftime('%Y-%m-%d')}) ≤ {parsed_dates[i][1]} ({curr_date.strftime('%Y-%m-%d')})")
                
                print()
                if sorted_check:
                    print("🎉 LE TRI PAR DATE EST CORRECT (plus ancienne en haut, plus récente en bas)")
                else:
                    print("❌ LE TRI PAR DATE N'EST PAS CORRECT")
            else:
                print("⚠️  Une seule date trouvée, pas de tri à vérifier")
        else:
            print("⚠️  Aucune date valide trouvée")
    else:
        print("⚠️  Pas assez de colonnes dans le fichier")
        
except Exception as e:
    print(f"❌ Erreur lors de la lecture du fichier Excel : {e}")
    print(f"Fichier : {excel_path}")
    print(f"Existe : {os.path.exists(excel_path)}")
