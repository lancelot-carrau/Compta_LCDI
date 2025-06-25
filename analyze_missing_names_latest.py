#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path
import glob

def analyze_latest_excel():
    """Analyse le fichier Excel le plus récent pour identifier les lignes avec des noms manquants"""
    
    # Cherche le fichier Excel le plus récent dans output/
    output_dir = Path("output")
    excel_files = list(output_dir.glob("*.xlsx"))
    excel_files.sort(key=os.path.getmtime, reverse=True)
    
    if not excel_files:
        print("❌ Aucun fichier Excel trouvé dans output/")
        return
    
    latest_file = excel_files[0]
    print(f"📊 Analyse du fichier: {latest_file}")
    print("=" * 80)
    
    try:
        # Lit le fichier Excel
        df = pd.read_excel(latest_file)
        print(f"📄 Nombre total de lignes: {len(df)}")
        
        # Affiche les colonnes
        print(f"📋 Colonnes: {list(df.columns)}")
        print()
        
        # Cherche la colonne client (peut avoir différents noms)
        client_col = None
        for col in df.columns:
            if 'client' in col.lower() or 'nom' in col.lower() or 'customer' in col.lower():
                client_col = col
                break
        
        if not client_col:
            print("⚠️  Colonne client non trouvée. Colonnes disponibles:")
            for i, col in enumerate(df.columns):
                print(f"  {i}: {col}")
            return
        
        print(f"👤 Colonne client identifiée: '{client_col}'")
        print()
        
        # Identifie les lignes avec des noms manquants ou vides
        missing_names = df[df[client_col].isna() | (df[client_col].str.strip() == '')]
        
        print(f"❌ Lignes avec noms manquants: {len(missing_names)}")
        
        if len(missing_names) > 0:
            print("\n📋 Détail des lignes avec noms manquants:")
            print("=" * 60)            
            for i, (idx, row) in enumerate(missing_names.iterrows()):
                print(f"\n🔍 Ligne {i + 1}:")  # Numérotation simple
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        value = "[VIDE]"
                    print(f"  {col}: {value}")
                print("-" * 40)
        
        # Statistiques générales
        print(f"\n📊 STATISTIQUES:")
        print(f"  • Total lignes: {len(df)}")
        print(f"  • Noms présents: {len(df) - len(missing_names)}")
        print(f"  • Noms manquants: {len(missing_names)}")
        print(f"  • Taux de succès: {((len(df) - len(missing_names)) / len(df) * 100):.1f}%")
        
        # Affiche quelques exemples de noms extraits avec succès
        successful_names = df[~(df[client_col].isna() | (df[client_col].str.strip() == ''))]
        if len(successful_names) > 0:
            print(f"\n✅ Exemples de noms extraits avec succès:")
            for i, name in enumerate(successful_names[client_col].head(10)):
                print(f"  • {name}")
                if i >= 9:  # Limite à 10 exemples
                    break
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_latest_excel()
