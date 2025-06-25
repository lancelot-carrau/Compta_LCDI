#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path

def analyze_excel_structure():
    """Analyse la structure du fichier Excel pour identifier le problème"""
    
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
        # Lit le fichier Excel sans header pour voir la structure brute
        df = pd.read_excel(latest_file, header=None)
        print(f"📄 Nombre total de lignes: {len(df)}")
        print(f"📄 Nombre total de colonnes: {len(df.columns)}")
        print()
        
        # Affiche toutes les lignes pour comprendre la structure
        print("🔍 Contenu complet du fichier:")
        for i, row in df.iterrows():
            print(f"Ligne {i}: {list(row)}")
        print()
        
        # Identifie quelle ligne contient les vrais headers
        for i, row in df.iterrows():
            if 'ID AMAZON' in str(row.values):
                print(f"✅ Headers trouvés à la ligne {i}")
                headers = row.values
                print(f"📋 Headers: {list(headers)}")
                  # Relit le fichier avec les bons headers
                df_correct = pd.read_excel(latest_file, header=int(i))
                print(f"\n📊 Structure avec headers corrects:")
                print(f"📄 Nombre de lignes de données: {len(df_correct)}")
                print(f"📋 Colonnes: {list(df_correct.columns)}")
                
                # Cherche la colonne client
                client_col = None
                for col in df_correct.columns:
                    if 'client' in str(col).lower() or 'nom' in str(col).lower():
                        client_col = col
                        break
                
                if client_col:
                    print(f"👤 Colonne client trouvée: '{client_col}'")
                    # Analyse les noms manquants
                    missing_names = df_correct[df_correct[client_col].isna() | (df_correct[client_col].str.strip() == '')]
                    print(f"❌ Lignes avec noms manquants: {len(missing_names)}")
                    
                    if len(missing_names) > 0:
                        print("\n📋 Lignes avec noms manquants:")
                        for idx, row in missing_names.iterrows():
                            print(f"  Ligne {idx}: {dict(row)}")
                else:
                    print("⚠️  Aucune colonne client trouvée")
                    print("📋 Colonnes disponibles:")
                    for col in df_correct.columns:
                        print(f"  - {col}")
                
                break
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_excel_structure()
