#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
from datetime import datetime

# Ajouter le répertoire courant au path pour importer les modules
sys.path.append(os.getcwd())

from app import extract_pdf_text, parse_amazon_invoice_data, extract_date_from_paid_box

def analyze_refund_invoice():
    """Analyser les factures de remboursement pour identifier les numéros de note de crédit"""
    
    print("🚀 DÉMARRAGE DE L'ANALYSE DES FACTURES DE REMBOURSEMENT")
    
    # Fichiers de remboursement identifiés (montants négatifs)
    refund_files = [
        '1756 TVA 20,00% FR 2025-05-05 FR5000FSHCVZJC -2,33€.pdf',
        '1762 TVA 21,00% ES 2025-05-06 FR500025HCVZJQ -117,49€.pdf', 
        '1766 TVA 22,00% IT 2025-05-07 FR500023HCVZJQ -115,25€.pdf',
        '1770 TVA 21,00% NL 2025-05-06 FR500026HCVZJQ -115,78€.pdf',
        '1783 TVA 21,00% BE 2025-03-03 FR50001CHCVZJQ -902,94€.pdf'
    ]
    
    print(f"📋 Fichiers de remboursement à analyser: {len(refund_files)}")
    
    # Test avec un seul fichier d'abord
    test_file = '1783 TVA 21,00% BE 2025-03-03 FR50001CHCVZJQ -902,94€.pdf'
    pdf_path = os.path.join(os.getcwd(), 'uploads', test_file)
    
    print(f"\n🔍 TEST AVEC FICHIER: {test_file}")
    print(f"📂 Chemin complet: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        # Lister les fichiers disponibles
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        print(f"📂 Contenu du dossier uploads:")
        for f in os.listdir(uploads_dir):
            if f.endswith('.pdf'):
                print(f"   - {f}")
        return
    
    print("✅ Fichier trouvé, extraction en cours...")
    
    # Extraire le texte
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("❌ Impossible d'extraire le texte du PDF")
        return
    
    print(f"📄 Texte extrait: {len(text)} caractères")
    print(f"📄 Extrait du texte (premiers 200 chars): {text[:200]}...")    # Recherche des patterns de note de crédit / remboursement
    print("\n🔍 RECHERCHE DES NUMÉROS DE NOTE DE CRÉDIT:")
    print("-" * 50)
    
    # Patterns pour numéros de note de crédit (multilingue)
    credit_note_patterns = [
        # Français
        r'Numéro de l\'avoir[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Note de crédit[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Numéro de la note de crédit[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Avoir[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Anglais
        r'Credit note number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Refund number[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Italien
        r'Numero della nota di credito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Nota di credito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Espagnol
        r'Número de la nota de crédito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Nota de crédito[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Néerlandais
        r'Creditnota nummer[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Creditnota[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Allemand
        r'Gutschrift Nummer[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        r'Gutschrift[:\s]+([A-Z]{2}\d{3,8}[A-Z0-9]{2,8})',
        
        # Patterns génériques
        r'\b(FR\d{3,8}[A-Z0-9]{2,8})\b',  # FR + chiffres + lettres
        r'\b(IT\d{3,8}[A-Z0-9]{2,8})\b',  # IT + chiffres + lettres
        r'\b(ES\d{3,8}[A-Z0-9]{2,8})\b',  # ES + chiffres + lettres
        r'\b(NL\d{3,8}[A-Z0-9]{2,8})\b',  # NL + chiffres + lettres
        r'\b(BE\d{3,8}[A-Z0-9]{2,8})\b',  # BE + chiffres + lettres
        r'\b(DE\d{3,8}[A-Z0-9]{2,8})\b'   # DE + chiffres + lettres
    ]
    
    found_credit_numbers = []
    
    for pattern in credit_note_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match not in found_credit_numbers:
                found_credit_numbers.append(match)
                print(f"   ✅ Numéro trouvé: {match}")
    
    if not found_credit_numbers:
        print("   ❌ Aucun numéro de note de crédit trouvé")
    
    # Recherche des termes de remboursement dans le contexte
    print("\n🔍 RECHERCHE DES CONTEXTES DE REMBOURSEMENT:")
    print("-" * 50)
    
    refund_keywords = [
        'remboursé', 'remboursement', 'avoir',
        'refunded', 'refund', 'credit note',
        'rimborsato', 'rimborso', 'nota di credito',
        'reembolsado', 'reembolso', 'nota de crédito',
        'terugbetaald', 'terugbetaling', 'creditnota',
        'erstattet', 'erstattung', 'gutschrift'
    ]
    
    for keyword in refund_keywords:
        for match in re.finditer(keyword, text, re.IGNORECASE):
            # Récupérer 100 caractères autour du mot-clé
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            print(f"   📍 '{keyword}' à position {match.start()}: {repr(context)}")
    
    # Test de l'extraction complète
    print(f"\n🧪 TEST DE L'EXTRACTION COMPLÈTE:")
    print("-" * 50)
    
    result = parse_amazon_invoice_data(
        text=text, 
        debug_mode=True, 
        filename=test_file, 
        pdf_path=pdf_path
    )
    
    if result:
        print("✅ Extraction réussie:")
        for key, value in result.items():
            print(f"   {key}: {value}")
        
        # Vérifier si le numéro de facture correspond à un numéro de note de crédit
        current_invoice = result.get('facture_amazon', '')
        if current_invoice in found_credit_numbers:
            print(f"✅ CORRECT: Le numéro de facture '{current_invoice}' correspond à une note de crédit")
        else:
            print(f"⚠️ ATTENTION: Le numéro de facture '{current_invoice}' ne correspond pas aux notes de crédit trouvées")
            if found_credit_numbers:
                print(f"   Notes de crédit disponibles: {found_credit_numbers}")
    else:
        print("❌ Échec de l'extraction")
    
    # Test d'extraction de date spécifique
    print(f"\n📅 ANALYSE SPÉCIFIQUE DES DATES:")
    print("-" * 50)
    
    extracted_date = extract_date_from_paid_box(text)
    filename_date = test_file.split(' ')[4]  # Extraire la date du nom de fichier
    
    print(f"Date du nom de fichier: {filename_date}")
    print(f"Date extraite du PDF: {extracted_date}")
    
    if extracted_date != filename_date.replace('-', '/'):
        print("⚠️ DIVERGENCE DE DATE DÉTECTÉE!")
        print("   → Besoin d'analyser pourquoi les dates diffèrent")
    else:
        print("✅ Les dates correspondent")

if __name__ == "__main__":
    analyze_refund_invoice()
