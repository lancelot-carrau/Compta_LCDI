#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path

def simple_excel_analysis():
    """Analyse simple du fichier Excel le plus récent"""
    
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
        # Lit le fichier Excel avec header à la ligne 1 (où sont les vrais headers)
        df = pd.read_excel(latest_file, header=1)
        print(f"📄 Nombre total de lignes: {len(df)}")
        print(f"📋 Colonnes: {list(df.columns)}")
        print()
        
        # Affiche quelques lignes d'exemple
        print("🔍 Exemples de données:")
        print(df.head())
        print()
        
        # Cherche la colonne client
        client_col = None
        for col in df.columns:
            if 'client' in str(col).lower() or 'nom' in str(col).lower():
                client_col = col
                break
        
        if client_col:
            print(f"👤 Colonne client trouvée: '{client_col}'")
            # Analyse les noms manquants
            missing_names = df[df[client_col].isna() | (df[client_col].astype(str).str.strip() == '') | (df[client_col].astype(str).str.strip() == 'nan')]
            print(f"❌ Lignes avec noms manquants: {len(missing_names)}")
            
            if len(missing_names) > 0:
                print("\n📋 Détail des lignes avec noms manquants:")
                for idx, row in missing_names.iterrows():
                    print(f"\n🔍 Ligne {idx}:")
                    for col in df.columns:
                        value = row[col]
                        print(f"  {col}: {value}")
                    print("-" * 40)
            
            # Affiche quelques noms extraits avec succès
            successful_names = df[~(df[client_col].isna() | (df[client_col].astype(str).str.strip() == '') | (df[client_col].astype(str).str.strip() == 'nan'))]
            if len(successful_names) > 0:
                print(f"\n✅ Exemples de noms extraits avec succès ({len(successful_names)} sur {len(df)}):")
                for name in successful_names[client_col].head(5):
                    print(f"  • {name}")
        else:
            print("⚠️  Aucune colonne client trouvée")
            print("📋 Colonnes disponibles:")
            for col in df.columns:
                print(f"  - {col}")
                  # Statistiques générales
        if client_col:
            missing_names = df[df[client_col].isna() | (df[client_col].astype(str).str.strip() == '') | (df[client_col].astype(str).str.strip() == 'nan')]
            total_rows = len(df)
            missing_count = len(missing_names)
            success_count = total_rows - missing_count
            success_rate = (success_count / total_rows * 100) if total_rows > 0 else 0
            
            print(f"\n📊 STATISTIQUES:")
            print(f"  • Total lignes: {total_rows}")
            print(f"  • Noms extraits: {success_count}")
            print(f"  • Noms manquants: {missing_count}")
            print(f"  • Taux de succès: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_excel_analysis()
