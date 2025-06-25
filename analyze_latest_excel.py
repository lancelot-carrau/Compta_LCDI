import pandas as pd
import os

# Lire le dernier fichier Excel généré
excel_path = r'c:\Code\Apps\Compta LCDI Rollback\output\Compta_LCDI_Amazon_23_06_2025_11_03_48.xlsx'

if os.path.exists(excel_path):
    try:
        # Lire le fichier avec header=1 pour ignorer la ligne de totaux
        df = pd.read_excel(excel_path, header=1)
        print(f'📊 Analyse du fichier: {os.path.basename(excel_path)}')
        print(f'🔢 Nombre total de factures: {len(df)}')
        print()
        
        # Analyser les noms vides ou problématiques
        empty_names = df[df['Nom contact'].isna() | (df['Nom contact'].astype(str).str.strip() == '')]
        
        if len(empty_names) > 0:
            print(f'❌ PROBLÈME: {len(empty_names)} factures sans nom:')
            for idx, row in empty_names.iterrows():
                facture = row.get('Facture AMAZON', 'N/A')
                pays = row.get('Pays', 'N/A')
                id_amazon = row.get('ID AMAZON', 'N/A')
                print(f'   • Facture: {facture} | Pays: {pays} | ID: {id_amazon}')
            print()
        else:
            print('✅ Tous les noms sont extraits correctement')
            
        # Analyser par pays
        print('📈 RÉPARTITION PAR PAYS:')
        pays_counts = df['Pays'].value_counts()
        for pays, count in pays_counts.items():
            print(f'   • {pays}: {count} factures')
            
        # Montrer quelques exemples de noms extraits
        print()
        print('📋 EXEMPLES DE NOMS EXTRAITS:')
        sample_names = df[df['Nom contact'].notna() & (df['Nom contact'].astype(str).str.strip() != '')]['Nom contact'].head(10)
        for i, name in enumerate(sample_names, 1):
            print(f'   {i}. {name}')
            
        # Vérifier spécifiquement les factures maltaises
        malta_rows = df[df['Pays'] == 'MT']
        if len(malta_rows) > 0:
            print()
            print('🇲🇹 ANALYSE SPÉCIFIQUE MALTE:')
            for idx, row in malta_rows.iterrows():
                facture = row.get('Facture AMAZON', 'N/A')
                nom = row.get('Nom contact', 'VIDE')
                print(f'   • Facture: {facture} | Nom: "{nom}"')
            
    except Exception as e:
        print(f'❌ Erreur lors de la lecture: {e}')
else:
    print('❌ Fichier non trouvé')
