#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import sys

def analyze_excel_output():
    """Analyser le fichier Excel de sortie pour comprendre les noms manquants"""
    
    output_dir = r"c:\Code\Apps\Compta LCDI Rollback\output"
    
    # Trouver le fichier Excel le plus récent
    excel_files = [f for f in os.listdir(output_dir) if f.startswith('Compta_LCDI_Amazon_23_06_2025')]
    if not excel_files:
        print("Aucun fichier Excel Amazon trouvé pour aujourd'hui")
        return
    
    # Prendre le plus récent
    latest_file = sorted(excel_files)[-1]
    file_path = os.path.join(output_dir, latest_file)
    
    print(f"Analyse du fichier: {latest_file}")
    print("="*60)
    
    try:
        # Lire le fichier Excel (structure avec totaux en première ligne)
        df = pd.read_excel(file_path, header=None)
        
        print("Contenu complet du fichier:")
        print(df.to_string())
        
        # Analyser les en-têtes (ligne 1)
        if len(df) >= 2:
            headers = df.iloc[1].tolist()
            print(f"\nEn-têtes détectés: {headers}")
            
            # Analyser les données (à partir de la ligne 2)
            if len(df) >= 3:
                print(f"\nNombre total de lignes de données: {len(df) - 2}")
                
                # Identifier la colonne des noms
                nom_col_index = None
                for i, header in enumerate(headers):
                    if header and 'nom' in str(header).lower():
                        nom_col_index = i
                        break
                
                if nom_col_index is not None:
                    print(f"Colonne des noms trouvée à l'index: {nom_col_index}")
                    
                    # Analyser les noms
                    noms_vides = 0
                    noms_remplis = 0
                    
                    for row_idx in range(2, len(df)):
                        nom_value = df.iloc[row_idx, nom_col_index]
                        if pd.isna(nom_value) or str(nom_value).strip() == '':
                            noms_vides += 1
                            print(f"  Ligne {row_idx + 1}: NOM VIDE - Autres données: {df.iloc[row_idx].tolist()}")
                        else:
                            noms_remplis += 1
                            print(f"  Ligne {row_idx + 1}: '{nom_value}'")
                    
                    print(f"\nRésumé:")
                    print(f"  Noms remplis: {noms_remplis}")
                    print(f"  Noms vides: {noms_vides}")
                    print(f"  Pourcentage de noms manquants: {(noms_vides / (noms_vides + noms_remplis)) * 100:.1f}%")
                else:
                    print("❌ Colonne des noms non trouvée!")
            else:
                print("❌ Aucune donnée dans le fichier")
        else:
            print("❌ Fichier mal formaté")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

def analyze_recent_pdf_extraction():
    """Analyser les derniers PDF traités pour comprendre le problème"""
    
    uploads_dir = r"c:\Code\Apps\Compta LCDI Rollback\uploads"
    
    if not os.path.exists(uploads_dir):
        print("Dossier uploads non trouvé")
        return
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("Aucun fichier PDF trouvé")
        return
    
    print(f"\nPDF disponibles pour test: {len(pdf_files)}")
    for i, pdf_file in enumerate(pdf_files[:5]):
        print(f"  {i+1}. {pdf_file}")

if __name__ == "__main__":
    analyze_excel_output()
    analyze_recent_pdf_extraction()
