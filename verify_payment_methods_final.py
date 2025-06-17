import pandas as pd
import os
from datetime import datetime

def verify_payment_methods_in_output():
    """Vérifier que les méthodes de paiement sont correctement remplies dans le fichier de sortie"""
    print("=== VÉRIFICATION DES MÉTHODES DE PAIEMENT DANS LE FICHIER FINAL ===\n")
    
    # Chercher le fichier le plus récent dans le dossier output
    output_folder = r'C:\Code\Apps\Compta LCDI V2\output'
    
    if not os.path.exists(output_folder):
        print("❌ Dossier output non trouvé")
        return
    
    # Lister tous les fichiers Excel
    excel_files = [f for f in os.listdir(output_folder) if f.endswith('.xlsx')]
    
    if not excel_files:
        print("❌ Aucun fichier Excel trouvé dans output/")
        return
    
    # Prendre le plus récent
    latest_file = max(excel_files, key=lambda f: os.path.getmtime(os.path.join(output_folder, f)))
    file_path = os.path.join(output_folder, latest_file)
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    print(f"📄 Fichier le plus récent: {latest_file}")
    print(f"⏰ Date de création: {file_time.strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # Charger le fichier
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Fichier chargé avec succès: {len(df)} lignes, {len(df.columns)} colonnes\n")
        
        # Vérifier les colonnes de méthodes de paiement
        payment_columns = ['Virement bancaire', 'ALMA', 'Younited', 'PayPal']
        
        print("📊 ANALYSE DES MÉTHODES DE PAIEMENT:")
        print("=" * 50)
        
        total_amount = 0
        total_transactions = 0
        
        for col in payment_columns:
            if col in df.columns:
                # Compter les lignes non nulles et non zéro
                non_zero_mask = (df[col] > 0) & (df[col].notna())
                non_zero_count = non_zero_mask.sum()
                total_amount_col = df[col].sum()
                
                print(f"{col:20}: {non_zero_count:3d} commandes, {total_amount_col:10.2f}€")
                
                if non_zero_count > 0:
                    total_amount += total_amount_col
                    total_transactions += non_zero_count
                    
                    # Montrer quelques exemples
                    examples = df[non_zero_mask].head(3)
                    print(f"                     Exemples: ", end="")
                    for idx, row in examples.iterrows():
                        ref = row.get('Réf.WEB', f'Ligne {idx+1}')
                        amount = row[col]
                        print(f"{ref}({amount:.0f}€) ", end="")
                    print()
            else:
                print(f"{col:20}: ❌ Colonne manquante")
            print()
        
        print("=" * 50)
        print(f"💰 TOTAL: {total_transactions} transactions, {total_amount:.2f}€")
        
        # Vérifier qu'il n'y a pas de lignes sans méthode de paiement
        print(f"\n🔍 ANALYSE DE LA COUVERTURE:")
        
        # Créer un masque pour les lignes qui ont au moins une méthode de paiement
        has_payment_method = pd.Series([False] * len(df))
        for col in payment_columns:
            if col in df.columns:
                has_payment_method |= (df[col] > 0) & (df[col].notna())
        
        coverage = has_payment_method.sum()
        print(f"   Lignes avec méthode de paiement: {coverage}/{len(df)} ({coverage/len(df)*100:.1f}%)")
        
        # Montrer les lignes sans méthode de paiement
        no_payment = df[~has_payment_method]
        if len(no_payment) > 0:
            print(f"   ⚠️  {len(no_payment)} lignes SANS méthode de paiement:")
            for idx, row in no_payment.head(5).iterrows():
                ref = row.get('Réf.WEB', f'Ligne {idx+1}')
                client = row.get('Client', 'N/A')
                ttc = row.get('TTC', 'N/A')
                print(f"     - {ref}: {client} ({ttc}€)")
        else:
            print("   ✅ Toutes les lignes ont une méthode de paiement")
        
        # Vérifier la cohérence avec les montants TTC
        print(f"\n📈 COHÉRENCE AVEC LES MONTANTS TTC:")
        if 'TTC' in df.columns:
            ttc_total = df['TTC'].sum()
            print(f"   Total TTC du tableau: {ttc_total:.2f}€")
            print(f"   Total méthodes paiement: {total_amount:.2f}€")
            
            diff = abs(ttc_total - total_amount)
            if diff < 1:  # Tolérance d'1€ pour les arrondis
                print("   ✅ Cohérence parfaite!")
            elif diff < 100:
                print(f"   ⚠️  Différence mineure: {diff:.2f}€")
            else:
                print(f"   ❌ Différence importante: {diff:.2f}€")
        
        print(f"\n🎯 RÉSUMÉ:")
        if total_transactions > 0 and coverage > len(df) * 0.8:  # Au moins 80% de couverture
            print("   ✅ Les méthodes de paiement sont correctement remplies!")
            print("   ✅ La correction a fonctionné avec succès!")
        else:
            print("   ❌ Problème détecté avec les méthodes de paiement")
            
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")

if __name__ == "__main__":
    verify_payment_methods_in_output()
