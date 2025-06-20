#!/usr/bin/env python3
"""
Script d'analyse des factures Amazon multilingues pour identifier les patterns de dates et montants
"""

import os
import re
import PyPDF2
import pdfplumber
from datetime import datetime

def detect_language(text):
    """Détecte automatiquement la langue du PDF Amazon"""
    text_lower = text.lower()
    
    # Mots-clés spécifiques par langue
    language_patterns = {
        'french': ['facture', 'montant', 'tva', 'total', 'détails', 'adresse', 'expédition', 'commande', 'février', 'janvier', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
        'italian': ['fattura', 'importo', 'iva', 'totale', 'dettagli', 'indirizzo', 'spedizione', 'ordine', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
        'german': ['rechnung', 'betrag', 'mehrwertsteuer', 'gesamt', 'details', 'adresse', 'versand', 'bestellung', 'januar', 'februar', 'märz', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'dezember'],
        'english': ['invoice', 'amount', 'vat', 'total', 'details', 'address', 'shipping', 'order', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'],
        'spanish': ['factura', 'importe', 'iva', 'total', 'detalles', 'dirección', 'envío', 'pedido', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
        'chinese': ['发票', '金额', '税额', '总计', '详情', '地址', '运输', '订单', '一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    }
    
    # Comptage des mots-clés par langue
    scores = {}
    for lang, keywords in language_patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[lang] = score
    
    # Retourne la langue avec le score le plus élevé
    if scores:
        detected_lang = max(scores.items(), key=lambda x: x[1])
        if detected_lang[1] > 0:
            return detected_lang[0], scores
    
    return 'unknown', scores

def get_multilingual_patterns():
    """Retourne les patterns multilingues pour l'extraction de données Amazon"""
    patterns = {
        'amazon_id': [
            r'(?:Amazon|AMAZON)(?:\s+)?(?:ID|Id|id|ORDER|Order|order|COMMANDE|Commande|commande|BESTELLUNG|Bestellung|bestellung|ORDINE|Ordine|ordine|PEDIDO|Pedido|pedido|订单)(?:\s*[:\-\s]+\s*)?([A-Z0-9\-]{10,20})',
            r'(?:ID|Id|id|ORDER|Order|order)\s*[:\-\s]+\s*([A-Z0-9\-]{10,20})',
            r'([A-Z0-9]{3}\-[A-Z0-9]{7}\-[A-Z0-9]{7})',  # Format standard Amazon
            r'([0-9]{3}\-[0-9]{7}\-[0-9]{7})',
        ],
        
        'invoice_number': [
            # Formats spécifiques Amazon avec lettres
            r'(?:Facture|FACTURE|Invoice|INVOICE|Rechnung|RECHNUNG|Fattura|FATTURA|Factura|FACTURA|发票)\s*(?:n°|N°|no|NO|#)?\s*[:\-\s]*\s*(FR[0-9]{10,15}[A-Z]{1,3})',
            r'(?:Facture|FACTURE|Invoice|INVOICE|Rechnung|RECHNUNG|Fattura|FATTURA|Factura|FACTURA|发票)\s*(?:n°|N°|no|NO|#)?\s*[:\-\s]*\s*([A-Z]{2}[0-9]{10,15}[A-Z]{1,3})',
            r'(FR[0-9]{10,15}[A-Z]{1,3})',  # Format direct FR + chiffres + lettres
            r'([A-Z]{2}[0-9]{10,15}[A-Z]{1,3})',  # Format général pays + chiffres + lettres
        ],
        
        'date': {
            'french': [
                r'(?:Date|DATE|Facturée?|FACTUREE?|du)\s*(?:de|le)?\s*[:\-\s]*\s*([0-9]{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+([0-9]{4})',
                r'(?:Date|DATE|Facturée?|FACTUREE?|du)\s*(?:de|le)?\s*[:\-\s]*\s*([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
                r'(?:Date|DATE|Facturée?|FACTUREE?|du)\s*(?:de|le)?\s*[:\-\s]*\s*([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{4})',
                r'([0-9]{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+([0-9]{4})',
            ],
            'italian': [
                r'(?:Data|DATA|Fattura|FATTURA|del)\s*[:\-\s]*\s*([0-9]{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+([0-9]{4})',
                r'(?:Data|DATA|Fattura|FATTURA|del)\s*[:\-\s]*\s*([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
                r'([0-9]{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+([0-9]{4})',
            ],
            'german': [
                r'(?:Datum|DATUM|Rechnung|RECHNUNG|vom)\s*[:\-\s]*\s*([0-9]{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+([0-9]{4})',
                r'(?:Datum|DATUM|Rechnung|RECHNUNG|vom)\s*[:\-\s]*\s*([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{4})',
                r'([0-9]{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+([0-9]{4})',
            ],
            'english': [
                r'(?:Date|DATE|Invoice|INVOICE|on)\s*[:\-\s]*\s*([0-9]{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+([0-9]{4})',
                r'(?:Date|DATE|Invoice|INVOICE|on)\s*[:\-\s]*\s*([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
                r'([0-9]{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+([0-9]{4})',
            ],
            'spanish': [
                r'(?:Fecha|FECHA|Factura|FACTURA|del)\s*[:\-\s]*\s*([0-9]{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+([0-9]{4})',
                r'(?:Fecha|FECHA|Factura|FACTURA|del)\s*[:\-\s]*\s*([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
                r'([0-9]{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+([0-9]{4})',
            ],
            'chinese': [
                r'(?:日期|发票日期|开票日期)\s*[:\-\s]*\s*([0-9]{4})[年\-/]([0-9]{1,2})[月\-/]([0-9]{1,2})[日]?',
                r'([0-9]{4})[年\-/]([0-9]{1,2})[月\-/]([0-9]{1,2})[日]?',
            ]
        },
        
        'amounts': [
            # Montants avec contexte multilingue
            r'(?:Sous-total|SOUS-TOTAL|Subtotal|SUBTOTAL|Zwischensumme|ZWISCHENSUMME|Subtotale|SUBTOTALE|Subtotal|SUBTOTAL|小计)\s*[:\-\s]*\s*(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)?\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})',
            r'(?:Total|TOTAL|Gesamt|GESAMT|Totale|TOTALE|Total|TOTAL|总计|合计)\s*[:\-\s]*\s*(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)?\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})',
            r'(?:TVA|T\.V\.A\.|VAT|V\.A\.T\.|IVA|I\.V\.A\.|Mehrwertsteuer|MwSt|MwSt\.|增值税|税额)\s*[:\-\s]*\s*(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)?\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})',
            r'(?:HT|H\.T\.|Net|NET|Netto|NETTO|Netto|NETTO|净额)\s*[:\-\s]*\s*(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)?\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})',
            # Montants génériques avec devise
            r'(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)\s*([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})',
            r'([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})\s*(?:EUR|€|USD|\$|CHF|GBP|£|¥|元|人民币)',
        ],
        
        'country': [
            r'(?:Pays|PAYS|Country|COUNTRY|Land|LAND|Paese|PAESE|País|PAÍS|国家)\s*[:\-\s]*\s*([A-Z]{2,3}|France|FRANCE|Italia|ITALIA|Deutschland|DEUTSCHLAND|España|ESPAÑA|中国|China|CHINA)',
            r'(?:Livraison|LIVRAISON|Shipping|SHIPPING|Versand|VERSAND|Spedizione|SPEDIZIONE|Envío|ENVÍO|配送)\s*[:\-\s]*\s*([A-Z]{2,3}|France|FRANCE|Italia|ITALIA|Deutschland|DEUTSCHLAND|España|ESPAÑA|中国|China|CHINA)',
        ]
    }
    
    return patterns

def parse_multilingual_date(date_str, lang='french'):
    """Parse une date selon la langue détectée"""
    month_maps = {
        'french': {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
            'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        },
        'italian': {
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
            'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
        },
        'german': {
            'januar': 1, 'februar': 2, 'märz': 3, 'april': 4, 'mai': 5, 'juni': 6,
            'juli': 7, 'august': 8, 'september': 9, 'oktober': 10, 'november': 11, 'dezember': 12
        },
        'english': {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        },
        'spanish': {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
    }
    
    date_str = date_str.lower().strip()
    
    # Tenter de parser selon la langue
    if lang in month_maps:
        for month_name, month_num in month_maps[lang].items():
            if month_name in date_str:
                # Extraire jour et année
                parts = re.split(r'\s+', date_str)
                try:
                    day = int(parts[0]) if parts[0].isdigit() else int(parts[1])
                    year = int(parts[-1]) if parts[-1].isdigit() and len(parts[-1]) == 4 else datetime.now().year
                    return f"{day:02d}/{month_num:02d}/{year}"
                except:
                    continue
    
    # Fallback pour les formats numériques
    numeric_patterns = [
        r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})',
        r'([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{4})',
        r'([0-9]{1,2})-([0-9]{1,2})-([0-9]{4})',
        r'([0-9]{4})[年\-/]([0-9]{1,2})[月\-/]([0-9]{1,2})[日]?'  # Format chinois
    ]
    
    for pattern in numeric_patterns:
        match = re.search(pattern, date_str)
        if match:
            if lang == 'chinese':
                year, month, day = match.groups()
                return f"{int(day):02d}/{int(month):02d}/{year}"
            else:
                day, month, year = match.groups()
                return f"{int(day):02d}/{int(month):02d}/{year}"
    
    return date_str

def analyze_pdf_multilingual(pdf_path):
    """Analyse détaillée d'un PDF avec détection multilingue"""
    print(f"\n{'='*60}")
    print(f"ANALYSE MULTILINGUE DE: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    try:
        # Extraction avec pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        print(f"Texte extrait ({len(text)} caractères):")
        print("-" * 40)
        print(text[:1000])  # Premier 1000 caractères
        print("-" * 40)
        
        # Détection de la langue
        detected_lang, lang_scores = detect_language(text)
        print(f"\n🌍 LANGUE DÉTECTÉE: {detected_lang.upper()}")
        print(f"   Scores: {lang_scores}")
        
        # Obtenir les patterns multilingues
        patterns = get_multilingual_patterns()
        
        # Recherche de l'ID Amazon
        print("\n🏷️ RECHERCHE ID AMAZON:")
        amazon_ids = []
        for pattern in patterns['amazon_id']:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    amazon_ids.append(match)
                    print(f"   ✅ Trouvé ID Amazon: {match}")
        
        # Recherche du numéro de facture
        print("\n📄 RECHERCHE NUMÉRO DE FACTURE:")
        invoice_numbers = []
        for pattern in patterns['invoice_number']:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    invoice_numbers.append(match)
                    print(f"   ✅ Trouvé numéro facture: {match}")
        
        # Recherche de dates selon la langue détectée
        print("\n🗓️ RECHERCHE DE DATES:")
        if detected_lang in patterns['date']:
            date_patterns = patterns['date'][detected_lang]
        else:
            # Utiliser tous les patterns si langue inconnue
            date_patterns = []
            for lang_patterns in patterns['date'].values():
                date_patterns.extend(lang_patterns)
        
        # Ajout des patterns génériques
        date_patterns.extend([
            r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
            r'([0-9]{1,2}-[0-9]{1,2}-[0-9]{4})',
            r'([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4})',
            r'([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})',  # Format ISO
        ])
        
        found_dates = set()
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Pour les groupes multiples, joindre les parties
                        if len(match) == 3:
                            if detected_lang == 'chinese':
                                date_str = f"{match[2]}/{match[1]}/{match[0]}"  # jour/mois/année
                            else:
                                date_str = f"{match[0]}/{match[1]}/{match[2]}"  # jour/mois/année
                        else:
                            date_str = "/".join(match)
                    else:
                        date_str = match
                    
                    # Parser la date selon la langue
                    parsed_date = parse_multilingual_date(date_str, detected_lang)
                    found_dates.add(parsed_date)
        
        for date in sorted(found_dates):
            print(f"   ✅ Trouvé date: {date}")
        
        # Recherche de montants
        print("\n💰 RECHERCHE DE MONTANTS:")
        found_amounts = set()
        for pattern in patterns['amounts']:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    amount = match.replace(',', '.')  # Normaliser les décimales
                    try:
                        float_amount = float(amount)
                        if float_amount >= 10.00:  # Filtrer les montants trop petits
                            found_amounts.add(f"{float_amount:.2f}€")
                    except ValueError:
                        continue
        
        for amount in sorted(found_amounts, key=lambda x: float(x.replace('€', ''))):
            print(f"   ✅ Trouvé montant: {amount}")
        
        # Recherche du pays
        print("\n🌍 RECHERCHE DU PAYS:")
        countries = []
        for pattern in patterns['country']:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    countries.append(match)
                    print(f"   ✅ Trouvé pays: {match}")
        
        # Analyse des patterns spécifiques de ce fichier
        print("\n🔍 PATTERNS SPÉCIFIQUES DÉTECTÉS:")
        
        # Patterns de TVA
        tva_patterns = [
            r'(?:TVA|VAT|IVA|MwSt|增值税)\s*(?:taux|rate|tariff|率)?\s*[:\-\s]*\s*([0-9]{1,2}(?:[.,][0-9]{1,2})?)\s*%',
            r'([0-9]{1,2}(?:[.,][0-9]{1,2})?)\s*%\s*(?:TVA|VAT|IVA|MwSt|增值税)',
        ]
        
        tva_rates = []
        for pattern in tva_patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    tva_rates.append(f"{match}%")
                    print(f"   ✅ Taux TVA trouvé: {match}%")
        
        # Résumé de l'extraction
        print(f"\n📊 RÉSUMÉ DE L'EXTRACTION:")
        print(f"   Langue détectée: {detected_lang}")
        print(f"   IDs Amazon: {len(amazon_ids)}")
        print(f"   Numéros de facture: {len(invoice_numbers)}")
        print(f"   Dates trouvées: {len(found_dates)}")
        print(f"   Montants trouvés: {len(found_amounts)}")
        print(f"   Pays trouvés: {len(countries)}")
        print(f"   Taux TVA trouvés: {len(tva_rates)}")
        
        return {
            'language': detected_lang,
            'language_scores': lang_scores,
            'amazon_ids': amazon_ids,
            'invoice_numbers': invoice_numbers,
            'dates_found': list(found_dates),
            'amounts_found': list(found_amounts),
            'countries': countries,
            'tva_rates': tva_rates,
            'text_length': len(text),
            'analysis_complete': True
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return {'error': str(e), 'analysis_complete': False}

def main():
    """Fonction principale pour tester l'analyse multilingue"""
    # Répertoire des PDFs à analyser
    uploads_dir = "uploads"
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Répertoire {uploads_dir} introuvable")
        return
    
    # Lister tous les fichiers PDF
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ Aucun fichier PDF trouvé dans {uploads_dir}")
        return
    
    print(f"🔍 Analyse de {len(pdf_files)} fichiers PDF...")
    
    results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(uploads_dir, pdf_file)
        try:
            result = analyze_pdf_multilingual(pdf_path)
            result['filename'] = pdf_file
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur sur {pdf_file}: {e}")
            continue
    
    # Résumé global
    print(f"\n{'='*80}")
    print(f"📈 RÉSUMÉ GLOBAL - {len(results)} fichiers analysés")
    print(f"{'='*80}")
    
    language_counts = {}
    for result in results:
        if result.get('analysis_complete'):
            lang = result.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
            
            print(f"\n📄 {result['filename']}")
            print(f"   Langue: {lang}")
            print(f"   IDs Amazon: {len(result.get('amazon_ids', []))}")
            print(f"   Dates: {len(result.get('dates_found', []))}")
            print(f"   Montants: {len(result.get('amounts_found', []))}")
    
    print(f"\n🌍 Répartition par langue:")
    for lang, count in language_counts.items():
        print(f"   {lang}: {count} fichiers")

if __name__ == "__main__":
    main()
