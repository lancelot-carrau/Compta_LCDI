import pandas as pd
import sys
import os

# Ajouter le répertoire de l'app au path
sys.path.insert(0, r'C:\Code\Apps\Compta LCDI V2')
from app import detect_encoding, normalize_column_names, clean_text_data, format_date_to_french

# Configuration des chemins
JOURNAL_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
COMMANDES_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
TRANSACTIONS_FILE = r"C:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"

def analyze_sersoub_dylan():
    """Analyser spécifiquement les données de Sersoub Dylan"""
    print("=== ANALYSE SERSOUB DYLAN ===\n")
    
    # 1. Charger les données
    print("1. Chargement des données...")
    
    # Commandes
    encoding_commandes = detect_encoding(COMMANDES_FILE)
    df_commandes = pd.read_csv(COMMANDES_FILE, encoding=encoding_commandes)
    print(f"   Commandes: {len(df_commandes)} lignes")
    
    # Transactions
    encoding_transactions = detect_encoding(TRANSACTIONS_FILE)
    df_transactions = pd.read_csv(TRANSACTIONS_FILE, encoding=encoding_transactions)
    print(f"   Transactions: {len(df_transactions)} lignes")
    
    # Journal
    encoding_journal = detect_encoding(JOURNAL_FILE)
    df_journal = pd.read_csv(JOURNAL_FILE, encoding=encoding_journal)
    print(f"   Journal: {len(df_journal)} lignes")
    
    # 2. Chercher les commandes de Sersoub Dylan
    print("\n2. Recherche des commandes de Sersoub Dylan...")
    
    # Chercher dans les commandes
    sersoub_commands = df_commandes[df_commandes['Billing Name'].str.contains('Sersoub Dylan', na=False, case=False)]
    if len(sersoub_commands) == 0:
        # Essayer d'autres variantes
        sersoub_commands = df_commandes[df_commandes['Billing Name'].str.contains('Dylan', na=False, case=False)]
    
    print(f"   Commandes trouvées: {len(sersoub_commands)}")
    
    if len(sersoub_commands) > 0:
        print("\n   Détails des commandes:")
        for idx, row in sersoub_commands.iterrows():
            name = row['Name']
            billing_name = row['Billing Name']
            total = row['Total']
            financial_status = row['Financial Status']
            payment_method = row['Payment Method']
            print(f"     - {name}: {billing_name}, Total={total}€, Status={financial_status}, Payment={payment_method}")
    
    # 3. Vérifier dans les transactions
    print("\n3. Recherche dans les transactions...")
    
    if len(sersoub_commands) > 0:
        sersoub_refs = sersoub_commands['Name'].tolist()
        print(f"   Références à chercher: {sersoub_refs}")
        
        for ref in sersoub_refs:
            # Chercher les transactions correspondantes
            transactions_ref = df_transactions[df_transactions['Order'] == ref]
            print(f"\n   Transactions pour {ref}:")
            if len(transactions_ref) > 0:
                for _, t_row in transactions_ref.iterrows():
                    amount = t_row['Presentment Amount']
                    fee = t_row['Fee']
                    net = t_row['Net']
                    print(f"     - Amount: {amount}€, Fee: {fee}€, Net: {net}€")
            else:
                print(f"     ❌ Aucune transaction trouvée")
      # 4. Vérifier dans le journal
    print("\n4. Recherche dans le journal...")
    print(f"   Colonnes du journal: {list(df_journal.columns)}")
    
    # Trouver la colonne de référence externe
    ref_col = None
    for col in df_journal.columns:
        if 'référence' in col.lower() and 'externe' in col.lower():
            ref_col = col
            break
    
    if ref_col is None:
        print("   ⚠️ Colonne 'Référence externe' non trouvée, utilisation de la première colonne")
        ref_col = df_journal.columns[0] if len(df_journal.columns) > 0 else None
    
    print(f"   Utilisation de la colonne: '{ref_col}'")
    
    if len(sersoub_commands) > 0 and ref_col:
        for ref in sersoub_refs:
            # Normaliser la référence (enlever #)
            ref_normalized = ref.replace('#', '')
            
            # Chercher dans le journal
            try:
                journal_entries = df_journal[df_journal[ref_col].astype(str).str.contains(ref_normalized, na=False, case=False)]
                print(f"\n   Entrées journal pour {ref} (cherché: {ref_normalized}):")
                if len(journal_entries) > 0:
                    for _, j_row in journal_entries.iterrows():
                        ref_lmb = j_row.get('Référence LMB', 'N/A')
                        ttc_col = None
                        ht_col = None
                        contact_col = None
                        
                        # Chercher les colonnes TTC, HT et contact
                        for col in df_journal.columns:
                            if 'ttc' in col.lower():
                                ttc_col = col
                            elif 'ht' in col.lower():
                                ht_col = col
                            elif 'contact' in col.lower():
                                contact_col = col
                        
                        ttc = j_row.get(ttc_col, 'N/A') if ttc_col else 'N/A'
                        ht = j_row.get(ht_col, 'N/A') if ht_col else 'N/A'
                        contact = j_row.get(contact_col, 'N/A') if contact_col else 'N/A'
                        
                        print(f"     - Réf LMB: {ref_lmb}, TTC: {ttc}€, HT: {ht}€, Contact: {contact}")
                else:
                    print(f"     ❌ Aucune entrée journal trouvée")
                    
                    # Essayer de chercher par nom de contact
                    if contact_col:
                        contact_entries = df_journal[df_journal[contact_col].astype(str).str.contains('Dylan', na=False, case=False)]
                        if len(contact_entries) > 0:
                            print(f"     🔍 Entrées trouvées par nom 'Dylan':")
                            for _, j_row in contact_entries.iterrows():
                                ref_ext = j_row.get(ref_col, 'N/A')
                                ref_lmb = j_row.get('Référence LMB', 'N/A')
                                ttc = j_row.get(ttc_col, 'N/A') if ttc_col else 'N/A'
                                ht = j_row.get(ht_col, 'N/A') if ht_col else 'N/A'
                                contact = j_row.get(contact_col, 'N/A')
                                print(f"       - Ref ext: {ref_ext}, Réf LMB: {ref_lmb}, TTC: {ttc}€, HT: {ht}€, Contact: {contact}")
            except Exception as e:
                print(f"   ❌ Erreur lors de la recherche: {e}")
    
    # 5. Diagnostiquer le problème
    print("\n5. DIAGNOSTIC:")
    
    if len(sersoub_commands) == 0:
        print("   ❌ Aucune commande trouvée pour Sersoub Dylan")
        print("   🔍 Vérifiez l'orthographe du nom ou cherchez manuellement")
        
        # Afficher quelques noms pour aider
        print("\n   Échantillon de noms dans les commandes:")
        for name in df_commandes['Billing Name'].dropna().unique()[:10]:
            print(f"     - {name}")
    else:
        print("   ✅ Commandes trouvées")
        
        # Vérifier si le problème est dans les transactions ou le journal
        for ref in sersoub_refs:
            ref_normalized = ref.replace('#', '')
            
            has_transaction = len(df_transactions[df_transactions['Order'] == ref]) > 0
            has_journal = len(df_journal[df_journal['Référence externe'].str.contains(ref_normalized, na=False, case=False)]) > 0
            
            print(f"   - {ref}: Transaction={'✅' if has_transaction else '❌'}, Journal={'✅' if has_journal else '❌'}")
            
            if not has_journal:
                print(f"     💡 Problème: {ref} n'est pas dans le journal")
                print(f"     📝 Solution: Vérifier que {ref_normalized} est bien dans le journal avec le bon format")

if __name__ == "__main__":
    analyze_sersoub_dylan()
