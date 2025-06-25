#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrait le texte d'un PDF de manière robuste"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        logger.warning("PyPDF2 non disponible, utilisation de pdfplumber")
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            logger.error("Aucune bibliothèque PDF disponible (PyPDF2 ou pdfplumber)")
            return ""
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction PDF {pdf_path}: {e}")
        return ""

def detect_language(text: str) -> str:
    """Détecte la langue principale du document"""
    # Mots clés par langue pour détecter Amazon
    language_keywords = {
        'french': ['facture', 'montant', 'tva', 'total', 'adresse', 'livraison'],
        'italian': ['fattura', 'importo', 'iva', 'totale', 'indirizzo', 'consegna'],
        'german': ['rechnung', 'betrag', 'mwst', 'summe', 'adresse', 'lieferung'],
        'english': ['invoice', 'amount', 'vat', 'total', 'address', 'delivery'],
        'chinese': ['发票', '金额', '税', '总计', '地址', '配送']
    }
    
    text_lower = text.lower()
    
    scores = {}
    for lang, keywords in language_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[lang] = score
      # Retourne la langue avec le meilleur score
    if scores and max(scores.values()) > 0:
        best_lang = max(scores, key=lambda x: scores[x])
    else:
        best_lang = 'unknown'
    return best_lang

def analyze_dates_patterns(text: str) -> Set[str]:
    """Analyse tous les patterns de dates trouvés dans le texte"""
    found_dates = set()
      # Patterns de dates multilingues
    date_patterns = [
        # Formats numériques standard
        r'([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{4})',
        r'([0-9]{4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,2})',
        
        # Dates avec contexte français
        r'(?:Date|Facture|Émission)[:\s]*([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{4})',
        
        # Dates avec contexte italien
        r'(?:Data|Fattura|Emissione)[:\s]*([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{4})',
        
        # Dates avec contexte allemand
        r'(?:Datum|Rechnung|Rechnungsdatum)[:\s]*([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{4})',
        
        # Dates avec contexte anglais
        r'(?:Date|Invoice|Billing)[:\s]*([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{4})',
        
        # Formats avec mois en texte (français)
        r'([0-9]{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+[0-9]{4})',
        
        # Formats avec mois en texte (italien)
        r'([0-9]{1,2}\s+(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+[0-9]{4})',
        
        # Formats avec mois en texte (allemand)
        r'([0-9]{1,2}\s+(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+[0-9]{4})',
        
        # Formats avec mois en texte (anglais)
        r'([0-9]{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+[0-9]{4})'
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found_dates.add(match.group(1) if len(match.groups()) > 0 else match.group(0))
    
    return found_dates

def analyze_amounts_patterns(text: str) -> Set[str]: 
    """Analyse tous les patterns de montants trouvés dans le texte"""
    found_amounts = set()
    
    # Patterns de montants multilingues
    amount_patterns = [
        # Formats européens avec virgule
        r'([0-9]{1,3}(?:\s[0-9]{3})*,[0-9]{2})\s*€',
        r'€\s*([0-9]{1,3}(?:\s[0-9]{3})*,[0-9]{2})',
        
        # Formats avec point
        r'([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})\s*€',
        r'€\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})',
        
        # Formats USD/autres devises
        r'\$\s*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})',
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})\s*\$',
          # Patterns contextuels français
        r'(?:Total|Montant|HT|TVA)[:\s]*([0-9]{1,3}(?:[,\.]\s*[0-9]{3})*[,\.][0-9]{2})',
        
        # Patterns contextuels italiens
        r'(?:Totale|Importo|Imponibile|IVA)[:\s]*([0-9]{1,3}(?:[,\.]\s*[0-9]{3})*[,\.][0-9]{2})',
        
        # Patterns contextuels allemands
        r'(?:Summe|Betrag|Netto|MwSt)[:\s]*([0-9]{1,3}(?:[,\.]\s*[0-9]{3})*[,\.][0-9]{2})',
        
        # Patterns contextuels anglais
        r'(?:Total|Amount|Net|VAT)[:\s]*([0-9]{1,3}(?:[,\.]\s*[0-9]{3})*[,\.][0-9]{2})'
    ]
    
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found_amounts.add(match.group(1) if len(match.groups()) > 0 else match.group(0))
    
    return found_amounts

def analyze_invoice_numbers(text: str) -> Set[str]:
    """Analyse les numéros de facture Amazon"""
    found_numbers = set()
    
    # Patterns pour les numéros de facture Amazon
    invoice_patterns = [
        # Format principal Amazon (FR + chiffres + lettres)
        r'(?:FR|IT|DE|ES|UK|US)([0-9]{4}[A-Z]{2,8})',
        
        # Numéros avec préfixes
        r'(?:Invoice|Facture|Fattura|Rechnung)[:\s#]*([A-Z0-9-]{8,15})',
        
        # Formats courts
        r'([0-9]{3}-[0-9]{7}-[0-9]{7})',
        r'([A-Z]{2}[0-9]{4}[A-Z]{2,8})'
    ]
    
    for pattern in invoice_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            number = match.group(1) if len(match.groups()) > 0 else match.group(0)
            # Éviter les numéros de TVA
            if not re.match(r'^FR[0-9]{11}$', number):
                found_numbers.add(number)
    
    return found_numbers

def analyze_pdf_content(pdf_path: str) -> Dict:
    """Analyse complète d'un PDF Amazon"""
    try:
        print(f"📄 Analyse de: {os.path.basename(pdf_path)}")
        
        # Extraction du texte
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return {'error': 'Impossible d\'extraire le texte', 'analysis_complete': False}
        
        # Détection de langue
        detected_lang = detect_language(text)
        print(f"🌐 Langue détectée: {detected_lang}")
        
        # Analyse des patterns
        found_dates = analyze_dates_patterns(text)
        found_amounts = analyze_amounts_patterns(text)
        found_invoices = analyze_invoice_numbers(text)
        
        print(f"📅 Dates trouvées ({len(found_dates)}): {list(found_dates)[:5]}")
        print(f"💰 Montants trouvés ({len(found_amounts)}): {list(found_amounts)[:5]}")
        print(f"📋 Numéros facture ({len(found_invoices)}): {list(found_invoices)[:3]}")
        print("-" * 60)
        
        return {
            'language': detected_lang,
            'text_length': len(text),
            'dates_found': list(found_dates),
            'amounts_found': list(found_amounts),
            'invoice_numbers': list(found_invoices),
            'analysis_complete': True
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return {'error': str(e), 'analysis_complete': False}

def main():
    """Fonction principale d'analyse des factures"""
    
    # Dossier des uploads
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ Dossier uploads introuvable")
        return
    
    # Recherche des fichiers PDF
    pdf_files = list(uploads_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Aucun fichier PDF trouvé dans le dossier uploads")
        return
    
    print(f"🔍 Analyse de {len(pdf_files)} fichiers PDF...")
    print("=" * 60)
    
    # Statistiques globales
    total_results = []
    languages_found = {}
    
    # Analyse de chaque PDF
    for pdf_file in pdf_files:
        result = analyze_pdf_content(str(pdf_file))
        if result.get('analysis_complete'):
            total_results.append(result)
            lang = result.get('language', 'unknown')
            languages_found[lang] = languages_found.get(lang, 0) + 1
    
    # Résumé global
    print("=" * 60)
    print("📊 RÉSUMÉ GLOBAL")
    print("=" * 60)
    print(f"✅ Fichiers analysés avec succès: {len(total_results)}/{len(pdf_files)}")
    print(f"🌐 Langues détectées: {languages_found}")
    
    if total_results:
        total_dates = sum(len(r.get('dates_found', [])) for r in total_results)
        total_amounts = sum(len(r.get('amounts_found', [])) for r in total_results)
        total_invoices = sum(len(r.get('invoice_numbers', [])) for r in total_results)
        
        print(f"📅 Total dates extraites: {total_dates}")
        print(f"💰 Total montants extraits: {total_amounts}")
        print(f"📋 Total numéros facture: {total_invoices}")

if __name__ == "__main__":
    main()
