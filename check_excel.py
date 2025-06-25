#!/usr/bin/env python3
"""
Vérification du contenu du fichier Excel généré
"""

import pandas as pd
import os

def check_excel_content():
    """Vérifie le contenu du fichier Excel téléchargé"""
    
    excel_file = "test_download.xlsx"
    
    if not os.path.exists(excel_file):
        print("❌ Fichier Excel non trouvé")
        return
    
    try:
        # Lire le fichier Excel
        print(f"📊 Analyse du fichier Excel: {excel_file}")
        print("=" * 60)
        
        # Lire sans en-têtes pour voir la structure brute
        df_raw = pd.read_excel(excel_file, header=None)
        print("📋 Structure brute du fichier:")
        print(df_raw.head(10))
        print()
        
        # Lire avec en-têtes (ligne 2 = index 1)
        df = pd.read_excel(excel_file, header=1)
        print("📋 Données avec en-têtes:")
        print(df.head())
        print()
        
        print("📊 Informations sur le fichier:")
        print(f"  - Nombre de lignes: {len(df)}")
        print(f"  - Nombre de colonnes: {len(df.columns)}")
        print(f"  - Colonnes: {list(df.columns)}")
        print()
        
        # Vérifier les totaux (première ligne)
        print("💰 Totaux calculés (première ligne):")
        totals_row = df_raw.iloc[0]
        print(f"  - HT: {totals_row[6] if pd.notna(totals_row[6]) else 'N/A'}")
        print(f"  - TVA: {totals_row[7] if pd.notna(totals_row[7]) else 'N/A'}")
        print(f"  - Total: {totals_row[9] if pd.notna(totals_row[9]) else 'N/A'}")
        print()
        
        # Afficher les factures
        print("📋 Factures extraites:")
        for idx, row in df.iterrows():
            if pd.notna(row['N°']) and str(row['N°']).isdigit():
                print(f"  {row['N°']:>3}. {row['ID AMAZON']} | {row['Pays']} | {row['TOTAL']}€")
        
        # Statistiques sur les pays
        countries = df[df['Pays'].notna()]['Pays'].value_counts()
        if not countries.empty:
            print()
            print("🌍 Répartition par pays:")
            for country, count in countries.items():
                print(f"  - {country}: {count} facture(s)")
        
        print("=" * 60)
        print("✅ Fichier Excel analysé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    check_excel_content()
