#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path

def analyze_excel_raw():
    """Analyse le fichier Excel le plus récent avec un accès plus direct"""
    
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
        # Lit le fichier Excel avec différentes options
        print("🔍 Tentative de lecture avec header=0...")
        df = pd.read_excel(latest_file, header=0)
        print(f"📄 Nombre total de lignes: {len(df)}")
        print(f"📋 Colonnes: {list(df.columns)}")
        print()
        
        # Affiche les premières lignes pour comprendre la structure
        print("🔍 Premières lignes du fichier:")
        print(df.head())
        print()
        
        # Essaie aussi sans header
        print("🔍 Tentative de lecture sans header...")
        df_no_header = pd.read_excel(latest_file, header=None)
        print(f"📄 Nombre total de lignes (sans header): {len(df_no_header)}")
        print("🔍 Premières lignes sans header:")
        print(df_no_header.head())
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_excel_raw()
