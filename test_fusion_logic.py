#!/usr/bin/env python3
"""
Test simple pour vérifier la logique de fusion
"""

import sys
import os
import pandas as pd
sys.path.append('.')

def test_fusion_logic():
    """Test simple de la logique de fusion"""
    
    # Simuler les données
    df_merged_step1 = pd.DataFrame({
        'Name': ['#LCDI-1038', '#LCDI-1037', '#LCDI-1035', '#LCDI-1099'],
    })
    
    df_journal = pd.DataFrame({
        'Piece': ['LCDI-1038', 'LCDI-1037', 'LCDI-1035'],
        'Référence LMB': ['FAC-L-001', 'FAC-L-002', 'FAC-L-003']
    })
    
    print("=== TEST LOGIQUE DE FUSION ===")
    print(f"Commandes : {df_merged_step1['Name'].tolist()}")
    print(f"Journal : {df_journal['Piece'].tolist()}")
    
    # Test de correspondance directe
    commandes_dans_journal = df_merged_step1['Name'].isin(df_journal['Piece']).sum()
    print(f"Correspondances directes : {commandes_dans_journal}/{len(df_merged_step1)}")
    
    # Test de la condition
    condition = commandes_dans_journal < len(df_merged_step1)
    print(f"Condition (normalisation needed) : {condition}")
    
    if condition:
        print("NORMALISATION DEVRAIT ÊTRE APPLIQUÉE")
        # Test manual de la fonction
        try:
            from app import improve_journal_matching
            result = improve_journal_matching(df_merged_step1, df_journal)
            print(f"Résultat de improve_journal_matching : {len(result)} lignes")
            print(f"Colonnes : {list(result.columns)}")
            ref_lmb_trouvées = result['Référence LMB'].notna().sum()
            print(f"Réf. LMB trouvées : {ref_lmb_trouvées}")
        except Exception as e:
            print(f"ERREUR dans improve_journal_matching : {e}")
            import traceback
            traceback.print_exc()
    else:
        print("NORMALISATION NE SERA PAS APPLIQUÉE")

if __name__ == "__main__":
    test_fusion_logic()
