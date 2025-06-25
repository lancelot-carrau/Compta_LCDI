#!/usr/bin/env python3
"""
Script pour vérifier le contenu du fichier Excel spécifique généré
"""
import pandas as pd
import os

# Fichier spécifique à analyser
excel_file = "output/Compta_LCDI_Amazon_23_06_2025_14_11_19.xlsx"

print(f"📄 Analyse du fichier: {excel_file}")
print("=" * 60)

try:
    # Lire le fichier Excel
    df = pd.read_excel(excel_file)
    
    # Afficher les colonnes
    print(f"📊 Colonnes disponibles: {list(df.columns)}")
    print()
    
    # Afficher les données importantes
    for index, row in df.iterrows():
        print(f"📋 Ligne {index + 1}:")
        print(f"   Nom: {row.get('Nom contact', 'N/A')}")
        print(f"   HT: {row.get('HT', 'N/A')}")
        print(f"   TVA: {row.get('TVA', 'N/A')}")
        print(f"   TOTAL: {row.get('TOTAL', 'N/A')}")
        print(f"   Date: {row.get('Date Facture', 'N/A')}")
        print(f"   Facture: {row.get('Facture AMAZON', 'N/A')}")
        print()
        
        # Vérifier la cohérence des montants
        try:
            ht_str = str(row.get('HT', '0')).replace('€', '').replace(',', '.').strip()
            tva_str = str(row.get('TVA', '0')).replace('€', '').replace(',', '.').strip()
            total_str = str(row.get('TOTAL', '0')).replace('€', '').replace(',', '.').strip()
            
            ht = float(ht_str) if ht_str else 0
            tva = float(tva_str) if tva_str else 0
            total = float(total_str) if total_str else 0
            
            calculated_total = ht + tva
            if abs(calculated_total - total) < 0.01:
                print(f"   ✅ Cohérence: HT ({ht:.2f}) + TVA ({tva:.2f}) = TOTAL ({total:.2f})")
            else:
                print(f"   ❌ Incohérence: HT ({ht:.2f}) + TVA ({tva:.2f}) = {calculated_total:.2f} ≠ TOTAL ({total:.2f})")
        except Exception as e:
            print(f"   ⚠️  Impossible de vérifier la cohérence des montants: {e}")
        
        print("-" * 40)

except Exception as e:
    print(f"❌ Erreur lors de la lecture du fichier Excel: {e}")
