#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour comparer le fichier d'exemple avec le fichier généré
"""

import pandas as pd
import sys
import os

def compare_files():
    """Compare les deux fichiers CSV"""
    
    # Chemins des fichiers
    fichier_exemple = r"c:\Users\Malo\Downloads\Compta-LCDI-shopify.csv"
    fichier_genere = r"c:\Users\Malo\Downloads\tableau_facturation_final_20250617_111742.csv"
    
    print("=== ANALYSE COMPARATIVE ===")
    
    try:
        # Charger les fichiers
        df_exemple = pd.read_csv(fichier_exemple)
        df_genere = pd.read_csv(fichier_genere)
        
        print(f"📋 Fichier d'exemple: {len(df_exemple)} lignes")
        print(f"   Colonnes: {list(df_exemple.columns)}")
        
        print(f"📋 Fichier généré: {len(df_genere)} lignes") 
        print(f"   Colonnes: {list(df_genere.columns)}")
        
        # Trouver les références communes
        refs_communes = []
        refs_exemple = df_exemple['Réf. WEB'].dropna().astype(str).str.strip()
        refs_genere = df_genere['Réf.WEB'].dropna().astype(str).str.strip()
        
        for ref in refs_exemple:
            if ref in refs_genere.values:
                refs_communes.append(ref)
        
        print(f"\n🔍 COMPARAISON DES DONNÉES:")
        print(f"   Références communes trouvées: {len(refs_communes)}")
        print(f"   Échantillon: {refs_communes[:5]}")
        
        # Comparaison détaillée
        print(f"\n📊 COMPARAISON DÉTAILLÉE (5 premiers cas):")
        
        for i, ref in enumerate(refs_communes[:5]):
            print(f"\n--- {ref} ---")
            
            # Lignes correspondantes
            ligne_exemple = df_exemple[df_exemple['Réf. WEB'].astype(str).str.strip() == ref].iloc[0]
            ligne_genere = df_genere[df_genere['Réf.WEB'].astype(str).str.strip() == ref].iloc[0]
            
            # Client
            client_exemple = ligne_exemple.get('Client', 'N/A')
            client_genere = ligne_genere.get('Client', 'N/A')
            print(f"   Client:")
            print(f"     Exemple: {client_exemple}")
            print(f"     Généré:  {client_genere}")
            if str(client_exemple).strip() == str(client_genere).strip():
                print(f"     ✅ Client correspond")
            else:
                print(f"     ❌ Client différent")
            
            # Référence LMB
            lmb_exemple = ligne_exemple.get('Réf. LMB', 'N/A')
            lmb_genere = ligne_genere.get('Réf. LMB', 'N/A')
            print(f"   Réf. LMB:")
            print(f"     Exemple: {lmb_exemple}")
            print(f"     Généré:  {lmb_genere}")
            if str(lmb_exemple).strip() == str(lmb_genere).strip():
                print(f"     ✅ Réf. LMB correspond")
            else:
                print(f"     ❌ Réf. LMB différent")
            
            # TTC
            ttc_exemple_brut = ligne_exemple.get('TTC', 'N/A')
            ttc_genere_brut = ligne_genere.get('TTC', 'N/A')
            
            # Nettoyer le TTC exemple (enlever $ et espaces)
            ttc_exemple = str(ttc_exemple_brut).replace('$', '').replace(',', '').replace(' ', '').strip()
            ttc_genere = str(ttc_genere_brut).strip()
            
            print(f"   TTC:")
            print(f"     Exemple: {ttc_exemple_brut} → {ttc_exemple}")
            print(f"     Généré:  {ttc_genere}")
            
            try:
                if abs(float(ttc_exemple) - float(ttc_genere)) < 0.01:
                    print(f"     ✅ TTC correspond")
                else:
                    print(f"     ❌ TTC différent (diff: {abs(float(ttc_exemple) - float(ttc_genere)):.2f})")
            except ValueError as e:
                print(f"     ⚠️ TTC non comparable: {e}")
        
        # Statistiques globales
        print(f"\n📈 STATISTIQUES GLOBALES:")
        
        # Nombre de lignes avec données complètes
        lignes_completes_exemple = len(df_exemple[df_exemple['TTC'].notna()])
        lignes_completes_genere = len(df_genere[df_genere['TTC'] != 0])
        
        print(f"   Lignes avec TTC dans exemple: {lignes_completes_exemple}/{len(df_exemple)}")
        print(f"   Lignes avec TTC dans généré: {lignes_completes_genere}/{len(df_genere)}")
        
        # Totaux TTC
        try:
            # Nettoyer les TTC de l'exemple
            ttc_exemple_clean = df_exemple['TTC'].astype(str).str.replace('$', '').str.replace(',', '').str.replace(' ', '')
            ttc_exemple_numeric = pd.to_numeric(ttc_exemple_clean, errors='coerce')
            total_exemple = ttc_exemple_numeric.sum()
            
            total_genere = df_genere['TTC'].sum()
            
            print(f"   Total TTC exemple: {total_exemple:.2f}€")
            print(f"   Total TTC généré: {total_genere:.2f}€")
            print(f"   Différence: {abs(total_exemple - total_genere):.2f}€")
            
            if abs(total_exemple - total_genere) < 1:
                print(f"   ✅ Totaux cohérents")
            else:
                print(f"   ❌ Totaux différents")
                
        except Exception as e:
            print(f"   ⚠️ Impossible de calculer les totaux: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Démarrage de la comparaison des fichiers...")
    success = compare_files()
    if success:
        print(f"\n🎉 COMPARAISON TERMINÉE !")
    else:
        print(f"\n💥 COMPARAISON ÉCHOUÉE !")
