#!/usr/bin/env python3
"""Script pour analyser les dates de la commande #LCDI-1006"""

import pandas as pd
import chardet

def safe_read_csv(file_path, separator=','):
    """Lit un fichier CSV avec détection automatique de l'encodage"""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
    
    print(f"Encodage détecté pour {file_path}: {encoding} (confiance: {confidence:.2f})")
    
    try:
        df = pd.read_csv(file_path, encoding=encoding, sep=separator)
        print(f"Fichier lu avec succès avec l'encodage {encoding}")
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture avec {encoding}: {e}")
        # Essayer avec d'autres encodages
        for fallback_encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=fallback_encoding, sep=separator)
                print(f"Fichier lu avec succès avec l'encodage de fallback {fallback_encoding}")
                return df
            except:
                continue
        raise Exception(f"Impossible de lire le fichier {file_path}")

# Charger les fichiers
orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"

print("=== ANALYSE DE LA COMMANDE #LCDI-1006 ===")

# Charger les commandes
df_orders = safe_read_csv(orders_file, separator=',')
print(f"Commandes chargées: {len(df_orders)} lignes")

# Charger le journal
df_journal = safe_read_csv(journal_file, separator=';')
print(f"Journal chargé: {len(df_journal)} lignes")

# Rechercher la commande #LCDI-1006
print("\n1. RECHERCHE DANS LES COMMANDES:")
commande_1006 = df_orders[df_orders['Name'] == '#LCDI-1006']
if len(commande_1006) > 0:
    print(f"   ✅ Commande trouvée dans orders_export")
    row = commande_1006.iloc[0]
    print(f"   - Name: {row['Name']}")
    if 'Fulfilled at' in df_orders.columns:
        print(f"   - Fulfilled at: {row['Fulfilled at']}")
    if 'Created at' in df_orders.columns:
        print(f"   - Created at: {row['Created at']}")
    if 'Paid at' in df_orders.columns:
        print(f"   - Paid at: {row['Paid at']}")
else:
    print("   ❌ Commande non trouvée dans orders_export")

print("\n2. RECHERCHE DANS LE JOURNAL:")
# Rechercher par référence externe
journal_1006_externe = df_journal[df_journal['Référence externe'] == '#LCDI-1006']
journal_1006_sans_diese = df_journal[df_journal['Référence externe'] == 'LCDI-1006']

if len(journal_1006_externe) > 0:
    print(f"   ✅ Commande trouvée dans Journal (avec #)")
    row = journal_1006_externe.iloc[0]
    print(f"   - Référence externe: {row['Référence externe']}")
    if 'Date du document' in df_journal.columns:
        print(f"   - Date du document: {row['Date du document']}")
    if 'Référence LMB' in df_journal.columns:
        print(f"   - Référence LMB: {row['Référence LMB']}")
elif len(journal_1006_sans_diese) > 0:
    print(f"   ✅ Commande trouvée dans Journal (sans #)")
    row = journal_1006_sans_diese.iloc[0]
    print(f"   - Référence externe: {row['Référence externe']}")
    if 'Date du document' in df_journal.columns:
        print(f"   - Date du document: {row['Date du document']}")
    if 'Référence LMB' in df_journal.columns:
        print(f"   - Référence LMB: {row['Référence LMB']}")
else:
    print("   ❌ Commande non trouvée dans Journal")
    print("   Références disponibles dans le journal:")
    print(f"   {df_journal['Référence externe'].head(10).tolist()}")

print("\n3. TEST DE CONVERSION DE DATE:")
# Tester la conversion des dates
if len(commande_1006) > 0 and 'Fulfilled at' in df_orders.columns:
    fulfilled_date = commande_1006.iloc[0]['Fulfilled at']
    print(f"   Date originale Fulfilled at: {fulfilled_date}")
    
    # Tester la conversion comme dans le code
    if fulfilled_date and str(fulfilled_date) != 'nan':
        date_str = str(fulfilled_date)
        print(f"   Date en string: {date_str}")
        
        if 'T' in date_str or '+' in date_str:
            try:
                # Enlever timezone et heure
                if '+' in date_str:
                    date_str = date_str.split('+')[0]
                if 'T' in date_str:
                    date_str = date_str.split('T')[0]
                elif ' ' in date_str:
                    date_str = date_str.split(' ')[0]
                
                print(f"   Date nettoyée: {date_str}")
                
                # Convertir YYYY-MM-DD vers MM/DD/YYYY (PROBLÈME ICI!)
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                wrong_format = date_obj.strftime('%m/%d/%Y')  # Format américain
                correct_format = date_obj.strftime('%d/%m/%Y')  # Format français
                
                print(f"   Conversion actuelle (MM/DD/YYYY): {wrong_format}")
                print(f"   Conversion correcte (DD/MM/YYYY): {correct_format}")
            except Exception as e:
                print(f"   Erreur de conversion: {e}")
