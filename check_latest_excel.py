#!/usr/bin/env python3
"""
Script pour vérifier le contenu du dernier Excel généré
"""
import pandas as pd
import os

def check_latest_excel():
    """Vérifie le contenu du dernier Excel généré"""
    
    # Chercher le fichier le plus récent
    output_dir = "output"
    excel_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx') and 'DEBUG_Batch' in f]
    if not excel_files:
        print("❌ Aucun fichier DEBUG_Batch trouvé")
        return
    
    # Prendre le plus récent
    latest_file = max(excel_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    file_path = os.path.join(output_dir, latest_file)
    
    print(f"📁 Fichier analysé: {latest_file}")
    print("=" * 80)
    
    # Lire le fichier avec les en-têtes à la ligne 2 (index 1)
    try:
        df = pd.read_excel(file_path, header=1)
        print(f"✅ Fichier lu avec succès")
        print(f"📊 Colonnes: {df.columns.tolist()}")
        print(f"📋 Nombre de lignes de données: {len(df)}")
        print()
        
        # Vérifier si on a les bonnes colonnes
        expected_columns = ['ID AMAZON', 'Facture AMAZON', 'Date Facture', 'Pays', 'Nom contact', 'HT', 'TVA', 'Taux TVA', 'TOTAL']
        if all(col in df.columns for col in expected_columns):
            print("✅ Structure de colonnes correcte")
            print()
              # Afficher les données
            ligne_num = 1
            for idx, row in df.iterrows():
                if pd.notna(row['ID AMAZON']) and str(row['ID AMAZON']).strip():
                    print(f"Ligne {ligne_num}:")
                    ligne_num += 1
                    print(f"  📅 Date: {row['Date Facture']}")
                    print(f"  🌍 Pays: {row['Pays']}")
                    print(f"  🆔 ID Amazon: {row['ID AMAZON']}")
                    print(f"  📄 Facture: {row['Facture AMAZON']}")
                    print(f"  💰 Total: {row['TOTAL']}€")
                    print(f"  👤 Contact: {row['Nom contact']}")
                    print()
        else:
            print("❌ Structure de colonnes incorrecte")
            print(f"Colonnes attendues: {expected_columns}")
            print(f"Colonnes trouvées: {df.columns.tolist()}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {str(e)}")
        
        # Essayer de lire sans header
        try:
            df_raw = pd.read_excel(file_path, header=None)
            print(f"Contenu brut (5 premières lignes):")
            print(df_raw.head().to_string())
        except Exception as e2:
            print(f"❌ Erreur lors de la lecture brute: {str(e2)}")

if __name__ == "__main__":
    check_latest_excel()
