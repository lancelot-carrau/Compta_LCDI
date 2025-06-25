#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation de l'extraction des données Amazon
Vérifie que toutes les dates et pays sont bien extraits dans les fichiers Excel générés
"""

import os
import pandas as pd
from datetime import datetime
import glob

def analyze_excel_file(file_path):
    """Analyse un fichier Excel généré pour vérifier la qualité de l'extraction"""
    print(f"\n{'='*80}")
    print(f"ANALYSE DU FICHIER: {os.path.basename(file_path)}")
    print('='*80)
    
    try:
        # Lire le fichier Excel
        df = pd.read_excel(file_path)
        
        # Afficher les colonnes disponibles
        print(f"Colonnes trouvées: {list(df.columns)}")
        print(f"Nombre de lignes: {len(df)}")
        
        # Analyser chaque ligne
        missing_dates = 0
        missing_countries = 0
        invalid_countries = 0
        
        for idx, (index, row) in enumerate(df.iterrows()):
            print(f"\nLigne {idx + 1}:")
            
            # Vérifier la date
            date_facture = row.get('Date Facture', '')
            if pd.isna(date_facture) or str(date_facture).strip() == '' or str(date_facture) == 'nan':
                print(f"  ❌ DATE MANQUANTE")
                missing_dates += 1
            else:
                print(f"  ✅ Date: {date_facture}")
            
            # Vérifier le pays
            pays = row.get('Pays', '')
            if pd.isna(pays) or str(pays).strip() == '' or str(pays) == 'nan':
                print(f"  ❌ PAYS MANQUANT")
                missing_countries += 1
            elif str(pays) == 'UE':
                print(f"  ⚠️  Pays générique: {pays}")
                invalid_countries += 1
            else:
                print(f"  ✅ Pays: {pays}")
            
            # Afficher les autres champs importants
            id_amazon = row.get('ID AMAZON', '')
            facture_amazon = row.get('FACTURE AMAZON', '')
            total = row.get('Total', '')
            
            print(f"  ID Amazon: {id_amazon}")
            print(f"  Facture Amazon: {facture_amazon}")
            print(f"  Total: {total}")
        
        # Résumé
        print(f"\n{'='*50}")
        print(f"RÉSUMÉ DE L'EXTRACTION:")
        print(f"{'='*50}")
        print(f"Total lignes: {len(df)}")
        print(f"Dates manquantes: {missing_dates}")
        print(f"Pays manquants: {missing_countries}")
        print(f"Pays génériques (UE): {invalid_countries}")
        
        success_rate_dates = ((len(df) - missing_dates) / len(df) * 100) if len(df) > 0 else 0
        success_rate_countries = ((len(df) - missing_countries - invalid_countries) / len(df) * 100) if len(df) > 0 else 0
        
        print(f"Taux de réussite dates: {success_rate_dates:.1f}%")
        print(f"Taux de réussite pays: {success_rate_countries:.1f}%")
        
        if missing_dates == 0 and missing_countries == 0 and invalid_countries == 0:
            print("✅ EXTRACTION PARFAITE!")
        else:
            print("⚠️  EXTRACTION À AMÉLIORER")
        
        return {
            'file': os.path.basename(file_path),
            'total_lines': len(df),
            'missing_dates': missing_dates,
            'missing_countries': missing_countries,
            'invalid_countries': invalid_countries,
            'success_rate_dates': success_rate_dates,
            'success_rate_countries': success_rate_countries
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return None

def main():
    """Fonction principale"""
    print("VALIDATION DE L'EXTRACTION DES DONNÉES AMAZON")
    print("=" * 80)
    
    # Chercher tous les fichiers Excel dans le dossier output
    output_dir = "output"
    excel_files = glob.glob(os.path.join(output_dir, "*.xlsx"))
    
    if not excel_files:
        print("❌ Aucun fichier Excel trouvé dans le dossier output")
        return
    
    print(f"Fichiers Excel trouvés: {len(excel_files)}")
    
    # Analyser chaque fichier
    results = []
    for file_path in excel_files:
        result = analyze_excel_file(file_path)
        if result:
            results.append(result)
    
    # Résumé global
    if results:
        print(f"\n{'='*80}")
        print("RÉSUMÉ GLOBAL DE TOUS LES FICHIERS")
        print('='*80)
        
        total_files = len(results)
        total_lines = sum(r['total_lines'] for r in results)
        total_missing_dates = sum(r['missing_dates'] for r in results)
        total_missing_countries = sum(r['missing_countries'] for r in results)
        total_invalid_countries = sum(r['invalid_countries'] for r in results)
        
        print(f"Fichiers analysés: {total_files}")
        print(f"Total lignes: {total_lines}")
        print(f"Total dates manquantes: {total_missing_dates}")
        print(f"Total pays manquants: {total_missing_countries}")
        print(f"Total pays génériques (UE): {total_invalid_countries}")
        
        if total_lines > 0:
            global_success_dates = ((total_lines - total_missing_dates) / total_lines * 100)
            global_success_countries = ((total_lines - total_missing_countries - total_invalid_countries) / total_lines * 100)
            
            print(f"Taux de réussite global dates: {global_success_dates:.1f}%")
            print(f"Taux de réussite global pays: {global_success_countries:.1f}%")
        
        # Fichiers avec problèmes
        problematic_files = [r for r in results if r['missing_dates'] > 0 or r['missing_countries'] > 0 or r['invalid_countries'] > 0]
        
        if problematic_files:
            print(f"\n⚠️  FICHIERS AVEC PROBLÈMES ({len(problematic_files)}):")
            for r in problematic_files:
                print(f"  - {r['file']}: {r['missing_dates']} dates manquantes, {r['missing_countries']} pays manquants, {r['invalid_countries']} pays génériques")
        else:
            print("\n✅ TOUS LES FICHIERS SONT PARFAITS!")

if __name__ == "__main__":
    main()
