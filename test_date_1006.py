#!/usr/bin/env python3
"""Script pour vérifier spécifiquement la date de la commande #LCDI-1006"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_consolidated_billing_table

def test_date_lcdi_1006():
    """Test spécifique pour vérifier la date de la commande #LCDI-1006"""
    print("🔍 TEST DE LA DATE DE LA COMMANDE #LCDI-1006")
    print("=" * 50)
    
    # Fichiers de test
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    transactions_file = r"c:\Users\Malo\Desktop\Compta LCDI\payment_transactions_export_1 (2).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    # Vérifier que les fichiers existent
    for file_path in [orders_file, transactions_file, journal_file]:
        if not os.path.exists(file_path):
            print(f"❌ Fichier introuvable: {file_path}")
            return False
    
    try:
        # Générer le tableau
        df_result = generate_consolidated_billing_table(orders_file, transactions_file, journal_file)
        
        # Rechercher la commande #LCDI-1006
        commande_1006 = df_result[df_result['Réf.WEB'] == '#LCDI-1006']
        
        if len(commande_1006) > 0:
            row = commande_1006.iloc[0]
            date_facture = row['Date Facture']
            ref_lmb = row['Réf. LMB']
            
            print(f"✅ Commande #LCDI-1006 trouvée dans le résultat:")
            print(f"   - Date Facture: {date_facture}")
            print(f"   - Réf. LMB: {ref_lmb}")
            print(f"   - Client: {row['Client']}")
            print(f"   - TTC: {row['TTC']}€")
            
            # Vérification de la date
            if date_facture == '19/05/2025':
                print("✅ SUCCÈS: La date est correcte (19/05/2025)")
                return True
            else:
                print(f"❌ ÉCHEC: Date incorrecte. Attendu: 19/05/2025, Obtenu: {date_facture}")
                return False
        else:
            print("❌ Commande #LCDI-1006 non trouvée dans le résultat")
            print("   Commandes disponibles:")
            for ref in df_result['Réf.WEB'].head(10):
                print(f"   - {ref}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_date_lcdi_1006()
    if success:
        print("\n🎉 TEST RÉUSSI: La date de #LCDI-1006 est correcte!")
    else:
        print("\n💥 TEST ÉCHOUÉ: La date de #LCDI-1006 est incorrecte!")
