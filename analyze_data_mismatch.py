#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'analyse pour comprendre pourquoi seulement 22 Réf. LMB sont trouvées
au lieu des 32 attendues du fichier orders_export.
"""

import pandas as pd
import os

def analyser_correspondances():
    """Analyse les correspondances entre commandes et journal"""
    print("=== ANALYSE DES CORRESPONDANCES MANQUANTES ===\n")
    
    # Chemins des fichiers
    orders_file = r"c:\Users\Malo\Desktop\Compta LCDI\orders_export_1 (1).csv"
    journal_file = r"c:\Users\Malo\Desktop\Compta LCDI\20250604-Journal.csv"
    
    # Vérifier que les fichiers existent
    if not os.path.exists(orders_file):
        print(f"❌ Fichier commandes non trouvé: {orders_file}")
        return
    if not os.path.exists(journal_file):
        print(f"❌ Fichier journal non trouvé: {journal_file}")
        return
    
    print("1. Lecture des fichiers...")
    
    # Lire les fichiers
    df_orders = pd.read_csv(orders_file, encoding='utf-8')
    
    # Essayer différents encodages pour le journal
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df_journal = None
    
    for encoding in encodings:
        try:
            df_journal = pd.read_csv(journal_file, encoding=encoding, delimiter=';')
            print(f"   - Journal lu avec succès (encodage: {encoding})")
            break
        except UnicodeDecodeError:
            continue
    
    if df_journal is None:
        print("❌ Impossible de lire le fichier journal")
        return
    
    print(f"   - Commandes: {len(df_orders)} lignes")
    print(f"   - Journal: {len(df_journal)} lignes")
    
    # Analyser les colonnes
    print("\n2. Analyse des colonnes...")
    
    # Colonnes des commandes
    if 'Name' in df_orders.columns:
        print("   ✓ Colonne 'Name' trouvée dans les commandes")
        commandes_uniques = df_orders['Name'].dropna().unique()
        print(f"   - Commandes uniques: {len(commandes_uniques)}")
        print(f"   - Échantillon: {list(commandes_uniques[:10])}")
    else:
        print("   ❌ Colonne 'Name' non trouvée dans les commandes")
        print(f"   Colonnes disponibles: {list(df_orders.columns)}")
        return
    
    # Colonnes du journal
    journal_ref_cols = [col for col in df_journal.columns if 'référence' in col.lower() or 'externe' in col.lower() or 'piece' in col.lower()]
    print(f"   - Colonnes de référence possibles dans le journal: {journal_ref_cols}")
    
    if 'Référence externe' in df_journal.columns:
        ref_col = 'Référence externe'
    elif 'Piece' in df_journal.columns:
        ref_col = 'Piece'
    else:
        print("   ❌ Aucune colonne de référence trouvée dans le journal")
        return
    
    print(f"   ✓ Colonne de référence du journal: '{ref_col}'")
    
    references_journal = df_journal[ref_col].dropna().unique()
    print(f"   - Références du journal: {len(references_journal)}")
    print(f"   - Échantillon: {list(references_journal[:10])}")
    
    # Analyse des correspondances directes
    print("\n3. Analyse des correspondances directes...")
    
    # Normaliser les références des commandes
    commandes_norm = set()
    for cmd in commandes_uniques:
        if pd.notna(cmd):
            cmd_str = str(cmd).strip()
            # Ajouter les deux formats
            if cmd_str.startswith('#'):
                commandes_norm.add(cmd_str)
                commandes_norm.add(cmd_str[1:])  # Sans le #
            else:
                commandes_norm.add(cmd_str)
                commandes_norm.add(f"#{cmd_str}")  # Avec le #
    
    print(f"   - Commandes normalisées: {len(commandes_norm)}")
    
    # Correspondances directes
    correspondances_directes = []
    for ref in references_journal:
        if pd.notna(ref):
            ref_str = str(ref).strip()
            if ref_str in commandes_norm:
                correspondances_directes.append(ref_str)
    
    print(f"   ✓ Correspondances directes: {len(correspondances_directes)}")
    if correspondances_directes:
        print(f"   - Échantillon: {correspondances_directes[:10]}")
    
    # Analyse des références multiples
    print("\n4. Analyse des références multiples...")
    
    import re
    references_multiples = []
    commandes_dans_multiples = set()
    
    for ref in references_journal:
        if pd.notna(ref):
            ref_str = str(ref).strip()
            # Détecter les références multiples (contient des espaces et plusieurs LCDI)
            if ' ' in ref_str and ref_str.count('LCDI-') > 1:
                references_multiples.append(ref_str)
                # Extraire les numéros de commandes
                numbers = re.findall(r'LCDI-(\d+)', ref_str)
                for num in numbers:
                    commandes_dans_multiples.add(f"#LCDI-{num}")
                    commandes_dans_multiples.add(f"LCDI-{num}")
    
    print(f"   ✓ Références multiples: {len(references_multiples)}")
    if references_multiples:
        print(f"   - Détail: {references_multiples}")
        print(f"   - Commandes concernées: {len(commandes_dans_multiples)}")
    
    # Total des correspondances
    total_correspondances = len(correspondances_directes) + len(commandes_dans_multiples)
    print(f"\n   📊 TOTAL CORRESPONDANCES ATTENDUES: {total_correspondances}")
    print(f"   - Directes: {len(correspondances_directes)}")
    print(f"   - Via références multiples: {len(commandes_dans_multiples)}")
    
    # Analyser les commandes sans correspondance
    print("\n5. Analyse des commandes sans correspondance...")
    
    toutes_correspondances = set(correspondances_directes) | commandes_dans_multiples
    commandes_sans_correspondance = []
    
    for cmd in commandes_uniques:
        if pd.notna(cmd):
            cmd_str = str(cmd).strip()
            cmd_norm1 = cmd_str if cmd_str.startswith('#') else f"#{cmd_str}"
            cmd_norm2 = cmd_str[1:] if cmd_str.startswith('#') else cmd_str
            
            if cmd_norm1 not in toutes_correspondances and cmd_norm2 not in toutes_correspondances:
                commandes_sans_correspondance.append(cmd_str)
    
    print(f"   ❌ Commandes sans correspondance: {len(commandes_sans_correspondance)}")
    if commandes_sans_correspondance:
        print(f"   - Échantillon: {commandes_sans_correspondance[:10]}")
    
    # Comparaison avec le résultat obtenu
    print("\n6. Comparaison avec le résultat obtenu...")
    print(f"   - Correspondances théoriques: {total_correspondances}")
    print(f"   - Correspondances obtenues: 22")
    print(f"   - Différence: {total_correspondances - 22}")
    
    if total_correspondances != 22:
        print("\n⚠️  PROBLÈME DÉTECTÉ:")
        print("   Il y a une différence entre les correspondances théoriques et obtenues.")
        print("   Causes possibles:")
        print("   1. Problème dans la logique de fusion")
        print("   2. Filtrage ou agrégation supprimant des lignes")
        print("   3. Normalisation des colonnes échouant")
        print("   4. Doublons dans les commandes")
    else:
        print("\n✅ COHÉRENCE CONFIRMÉE:")
        print("   Le nombre de correspondances obtenues correspond à la théorie.")
    
    return {
        'commandes_total': len(commandes_uniques),
        'journal_total': len(references_journal),
        'correspondances_directes': len(correspondances_directes),
        'correspondances_multiples': len(commandes_dans_multiples),
        'total_theorique': total_correspondances,
        'sans_correspondance': len(commandes_sans_correspondance)
    }

if __name__ == "__main__":
    analyser_correspondances()
        if 'LCDI-' in ref_str:
            try:
                return int(ref_str.split('LCDI-')[1])
            except:
                return None
        return None
    
    # Références des commandes
    orders_refs = df_orders['Name'].dropna().tolist()
    orders_numbers = [extract_order_number(ref) for ref in orders_refs]
    orders_numbers = [n for n in orders_numbers if n is not None]
    
    print(f"   Commandes:")
    print(f"     - Références uniques: {len(set(orders_refs))}")
    print(f"     - Numéros extraits: {len(orders_numbers)}")
    print(f"     - Plage: {min(orders_numbers) if orders_numbers else 'N/A'} à {max(orders_numbers) if orders_numbers else 'N/A'}")
    print(f"     - Dernières références: {sorted(set(orders_refs))[-5:]}")
    
    # Références du journal
    journal_refs = df_journal['Piece'].dropna().tolist()
    journal_numbers = [extract_order_number(ref) for ref in journal_refs]
    journal_numbers = [n for n in journal_numbers if n is not None]
    
    print(f"   Journal:")
    print(f"     - Références uniques: {len(set(journal_refs))}")
    print(f"     - Numéros extraits: {len(journal_numbers)}")
    print(f"     - Plage: {min(journal_numbers) if journal_numbers else 'N/A'} à {max(journal_numbers) if journal_numbers else 'N/A'}")
    print(f"     - Dernières références: {sorted(set(journal_refs))[-5:]}")
    
    # 4. Analyser les correspondances
    print("\n3. Analyse des correspondances...")
    
    # Normaliser les références
    def normalize_ref(ref):
        if pd.isna(ref):
            return None
        ref_str = str(ref).strip()
        return ref_str if ref_str.startswith('#') else f"#{ref_str}"
    
    orders_normalized = {normalize_ref(ref) for ref in orders_refs}
    journal_normalized = {normalize_ref(ref) for ref in journal_refs}
    
    # Correspondances
    correspondances = orders_normalized & journal_normalized
    orders_only = orders_normalized - journal_normalized
    journal_only = journal_normalized - orders_normalized
    
    print(f"   Correspondances trouvées: {len(correspondances)}")
    print(f"   Références dans commandes seulement: {len(orders_only)}")
    print(f"   Références dans journal seulement: {len(journal_only)}")
    
    # 5. Analyser les lignes multiples (une commande peut avoir plusieurs lignes)
    print("\n4. Analyse des lignes multiples...")
    
    orders_count = df_orders['Name'].value_counts()
    journal_count = df_journal['Piece'].value_counts()
    
    print(f"   Commandes avec plusieurs lignes: {(orders_count > 1).sum()}")
    print(f"   Journal avec plusieurs lignes: {(journal_count > 1).sum()}")
    
    # Montrer les exemples
    multi_orders = orders_count[orders_count > 1].head(3)
    if not multi_orders.empty:
        print(f"   Exemples commandes multi-lignes:")
        for ref, count in multi_orders.items():
            print(f"     {ref}: {count} lignes")
    
    multi_journal = journal_count[journal_count > 1].head(3)
    if not multi_journal.empty:
        print(f"   Exemples journal multi-lignes:")
        for ref, count in multi_journal.items():
            print(f"     {ref}: {count} lignes")
    
    # 6. Recommandations
    print(f"\n=== RECOMMANDATIONS ===")
    
    overlap_percentage = len(correspondances) / len(orders_normalized) * 100
    print(f"Taux de chevauchement: {overlap_percentage:.1f}%")
    
    if overlap_percentage < 50:
        print("❌ PROBLÈME MAJEUR: Décalage temporel important")
        print("Solutions possibles:")
        print("- Utiliser des fichiers de la même période")
        print("- Mettre à jour le fichier journal")
        print("- Étendre la plage temporelle des commandes")
    elif overlap_percentage < 80:
        print("⚠️ PROBLÈME MODÉRÉ: Décalage temporel partiel")
        print("Solutions possibles:")
        print("- Vérifier la synchronisation des exports")
        print("- Considérer les commandes en cours de traitement")
    else:
        print("✅ BON CHEVAUCHEMENT: Données cohérentes")
    
    # 7. Analyse des dates si disponibles
    print(f"\n5. Analyse des dates...")
    
    if 'Fulfilled at' in df_orders.columns:
        orders_dates = pd.to_datetime(df_orders['Fulfilled at'], errors='coerce')
        orders_dates_valid = orders_dates.dropna()
        if not orders_dates_valid.empty:
            print(f"   Commandes - Période: {orders_dates_valid.min().strftime('%Y-%m-%d')} à {orders_dates_valid.max().strftime('%Y-%m-%d')}")
    
    if 'Date du document' in df_journal.columns:
        # Essayer plusieurs formats de date
        journal_dates = pd.to_datetime(df_journal['Date du document'], errors='coerce', format='%d/%m/%Y')
        if journal_dates.isna().all():
            journal_dates = pd.to_datetime(df_journal['Date du document'], errors='coerce')
        
        journal_dates_valid = journal_dates.dropna()
        if not journal_dates_valid.empty:
            print(f"   Journal - Période: {journal_dates_valid.min().strftime('%Y-%m-%d')} à {journal_dates_valid.max().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    analyze_data_mismatch()
