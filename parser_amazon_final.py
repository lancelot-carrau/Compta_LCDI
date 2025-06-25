#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version finale de l'extracteur Amazon avec logique spatiale intégrée
Cette version combine l'approche spatiale de pdfplumber avec les regex en fallback
"""

import re
import pdfplumber
from decimal import Decimal, InvalidOperation

def parse_amazon_invoice_data_enhanced(text, debug_mode=False, filename='', pdf_path=None):
    """
    Parse les données d'une facture Amazon en combinant analyse spatiale et regex
    
    Args:
        text: Texte brut extrait (pour compatibilité avec l'ancienne interface)
        debug_mode: Mode debug pour affichage détaillé
        filename: Nom du fichier pour les logs
        pdf_path: Chemin vers le fichier PDF pour analyse spatiale
    
    Returns:
        dict: Données extraites ou None si échec
    """
    
    # Initialisation du résultat
    result = {
        'id_amazon': '',
        'facture_amazon': '',
        'date_facture': '',
        'pays': '',
        'nom_contact': '',
        'ht': 0.0,
        'tva': 0.0,
        'taux_tva': '',
        'total': 0.0
    }
    
    try:
        # Vérification des mots-clés Amazon
        amazon_keywords = ['amazon', 'Amazon', 'AMAZON', 'fattura', 'facture', 'invoice']
        if not any(keyword in text for keyword in amazon_keywords):
            return None
        
        # === ANALYSE SPATIALE AVEC PDFPLUMBER (si PDF disponible) ===
        if pdf_path and pdf_path.lower().endswith('.pdf'):
            try:
                spatial_result = extract_with_spatial_analysis(pdf_path, debug_mode)
                if spatial_result:
                    # Fusionner les résultats spatiaux
                    for key, value in spatial_result.items():
                        if value and not result[key]:  # Ne pas écraser les valeurs existantes
                            result[key] = value
                            if debug_mode:
                                print(f"   📍 {key} (spatial): {value}")
            except Exception as e:
                if debug_mode:
                    print(f"   ⚠️  Analyse spatiale échouée: {e}")
        
        # === FALLBACK REGEX SUR TEXTE BRUT ===
        regex_patterns = {
            'id_amazon': [
                r'\b(\d{3}-\d{7}-\d{7})\b'
            ],
            'facture_amazon': [
                r'\b(FR\d{4,8}[A-Z0-9]{2,8})\b',
                r'\b(IT\d{4,8}[A-Z0-9]{2,8})\b',
                r'\b(MT\d{4,8}[A-Z0-9]{2,8})\b',
                r'Numero fattura\s+([A-Z]{2}\d{4,8}[A-Z0-9]{2,8})',
                r'Numéro de la facture\s+([A-Z]{2}\d{4,8}[A-Z0-9]{2,8})'
            ],
            'date_facture': [
                r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
                r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'Date de la facture[^0-9]*(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
            ],
            'pays': [
                r'(\d{5})\s*\n?\s*(FR|IT|MT)\b',
                r'\b(\d{5})\s+(?:FR|France|FRANCE)\b'
            ],
            'nom_contact': [
                r'(?:Bill to|Ship to|Livré à|Adresse de livraison)[:\s\n]+([A-Z][A-Za-z\s&\-\'\.]{5,80})',
                r'Commandé par\s+([A-Z][A-Za-z\s\-\'\.]{5,40})'
            ],
            'total': [
                r'Total à payer\s+(\d+[,.]?\d{0,2})\s*€',
                r'Montant dû\s+(\d+[,.]?\d{0,2})\s*€',
                r'Totale fattura\s+(\d+[,.]?\d{0,2})\s*€',
                r'Grand Total[:\s]+(\d+[,.]?\d{0,2})\s*[€$]'
            ]
        }
        
        # Application des patterns regex pour les champs manquants
        for field, patterns in regex_patterns.items():
            if not result[field]:  # Seulement si pas déjà rempli par l'analyse spatiale
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        if field == 'date_facture' and len(match.groups()) >= 3:
                            # Traitement des dates avec mois en texte
                            day = match.group(1).zfill(2)
                            month_text = match.group(2).lower()
                            year = match.group(3)
                            
                            # Mapping des mois
                            month_map = {
                                # Italien
                                'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
                                'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
                                'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
                                # Français
                                'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
                                'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
                                'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
                            }
                            
                            if month_text in month_map:
                                result[field] = f"{day}/{month_map[month_text]}/{year}"
                            else:
                                result[field] = f"{day}/{month_text}/{year}"
                        elif field == 'pays' and len(match.groups()) >= 1:
                            result[field] = match.group(1)
                        elif field in ['total'] and match.group(1):
                            try:
                                result[field] = float(match.group(1).replace(',', '.'))
                            except (ValueError, InvalidOperation):
                                continue
                        else:
                            result[field] = match.group(1).strip()
                        
                        if debug_mode:
                            print(f"   📝 {field} (regex): {result[field]}")
                        break
        
        # === VALIDATION ET COHÉRENCE ===
        # Si nous avons HT, TVA, Total, vérifier la cohérence
        if result['ht'] and result['tva'] and result['total']:
            calculated_total = result['ht'] + result['tva']
            if abs(calculated_total - result['total']) > 0.02:
                if debug_mode:
                    print(f"   ⚠️  Auto-correction des montants: {calculated_total:.2f} vs {result['total']}")
                # Prioriser le total et recalculer HT/TVA si on a le taux
                if result['taux_tva'] and '%' in str(result['taux_tva']):
                    try:
                        taux = float(result['taux_tva'].replace('%', ''))
                        result['ht'] = round(result['total'] / (1 + taux/100), 2)
                        result['tva'] = round(result['total'] - result['ht'], 2)
                    except:
                        pass
        
        # Calcul automatique du taux de TVA si manquant
        if not result['taux_tva'] and result['ht'] > 0 and result['tva'] > 0:
            taux = (result['tva'] / result['ht']) * 100
            result['taux_tva'] = f"{taux:.0f}%"
            if debug_mode:
                print(f"   🧮 Taux TVA calculé: {result['taux_tva']}")
        
        # Vérification des données minimales
        has_minimum_data = any([
            result['id_amazon'],
            result['facture_amazon'],
            result['total'] > 0
        ])
        
        if debug_mode:
            completeness = sum(1 for v in result.values() if v)
            print(f"   📊 Complétude: {completeness}/8 champs remplis")
        
        return result if has_minimum_data else None
        
    except Exception as e:
        if debug_mode:
            print(f"   ❌ Erreur parsing {filename}: {e}")
        return None

def extract_with_spatial_analysis(pdf_path, debug_mode=False):
    """
    Extraction spatiale avancée avec pdfplumber
    """
    result = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                if debug_mode:
                    print(f"   📄 Page {page_num + 1}")
                
                # === EXTRACTION DES TABLEAUX ===
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables):
                        if not table:
                            continue
                        
                        # Analyse du tableau de TVA (format: ['', '20 %', '191,38 €', '38,28 €'])
                        for row in table:
                            if len(row) >= 4 and any('€' in str(cell) for cell in row):
                                # Recherche d'une ligne avec pourcentage et montants
                                percent_cell = None
                                ht_cell = None
                                tva_cell = None
                                
                                for cell in row:
                                    cell_str = str(cell).strip()
                                    if '%' in cell_str:
                                        try:
                                            percent_cell = float(cell_str.replace('%', '').replace(',', '.').strip())
                                        except:
                                            pass
                                    elif '€' in cell_str:
                                        try:
                                            amount = float(cell_str.replace('€', '').replace(',', '.').strip())
                                            if ht_cell is None:
                                                ht_cell = amount
                                            elif tva_cell is None:
                                                tva_cell = amount
                                        except:
                                            pass
                                
                                if percent_cell and ht_cell and tva_cell:
                                    result['taux_tva'] = f"{percent_cell:.0f}%"
                                    result['ht'] = ht_cell
                                    result['tva'] = tva_cell
                                    if debug_mode:
                                        print(f"      ✅ Tableau TVA: {percent_cell}% | HT: {ht_cell}€ | TVA: {tva_cell}€")
                                    break
                
                # === EXTRACTION DU TEXTE POUR LES AUTRES CHAMPS ===
                text = page.extract_text() or ""
                
                # Total à payer (souvent en évidence)
                if not result.get('total'):
                    total_match = re.search(r'Total à payer\s+(\d+[,.]?\d{0,2})\s*€', text)
                    if not total_match:
                        total_match = re.search(r'Montant dû\s+(\d+[,.]?\d{0,2})\s*€', text)
                    
                    if total_match:
                        try:
                            result['total'] = float(total_match.group(1).replace(',', '.'))
                            if debug_mode:
                                print(f"      ✅ Total: {result['total']}€")
                        except:
                            pass
                
                # Numéro de facture
                if not result.get('facture_amazon'):
                    facture_match = re.search(r'Numéro de la facture\s+([A-Z]{2}\d{4,8}[A-Z0-9]{2,8})', text)
                    if facture_match:
                        result['facture_amazon'] = facture_match.group(1)
                        if debug_mode:
                            print(f"      ✅ Facture: {result['facture_amazon']}")
                
                # ID de commande Amazon
                if not result.get('id_amazon'):
                    id_match = re.search(r'Numéro de la commande\s+(\d{3}-\d{7}-\d{7})', text)
                    if id_match:
                        result['id_amazon'] = id_match.group(1)
                        if debug_mode:
                            print(f"      ✅ ID Amazon: {result['id_amazon']}")
    
    except Exception as e:
        if debug_mode:
            print(f"   ❌ Erreur analyse spatiale: {e}")
    
    return result

def test_enhanced_parser():
    """Test de l'extracteur amélioré"""
    
    pdf_path = 'uploads/batch_7_1716_TVA_2000_FR_2025-04-28_FR5003KOHCVZJI_22966.pdf'
    
    # Simulation de l'appel depuis app.py
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        print("❌ Impossible de lire le PDF")
        return
    
    print("=" * 80)
    print("🧪 TEST DE L'EXTRACTEUR AMAZON FINAL")
    print("=" * 80)
    
    result = parse_amazon_invoice_data_enhanced(
        text=text,
        debug_mode=True,
        filename='test.pdf',
        pdf_path=pdf_path
    )
    
    if result:
        print("\n✅ EXTRACTION RÉUSSIE!")
        print("-" * 50)
        for key, value in result.items():
            print(f"   {key.ljust(15)}: {value}")
        
        # Vérifications
        print("\n🔍 VÉRIFICATIONS:")
        print("-" * 50)
        
        checks = [
            ("ID Amazon présent", bool(result['id_amazon'])),
            ("Facture présente", bool(result['facture_amazon'])),
            ("Montants cohérents", abs((result['ht'] + result['tva']) - result['total']) < 0.02 if all([result['ht'], result['tva'], result['total']]) else False),
            ("TVA calculée correctement", abs(result['ht'] * (float(result['taux_tva'].replace('%', ''))/100) - result['tva']) < 0.02 if all([result['ht'], result['tva'], result['taux_tva']]) else False)
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
    
    else:
        print("❌ EXTRACTION ÉCHOUÉE")

if __name__ == "__main__":
    test_enhanced_parser()
