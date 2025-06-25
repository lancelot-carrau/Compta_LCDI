#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pdfplumber
import re
from pathlib import Path

def analyze_malta_invoice():
    """Analyse spécifiquement la facture maltaise problématique"""
    
    target_id = "406-7925504-5225948"
    target_invoice = "FR500063HCVZJU"
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ Dossier uploads non trouvé")
        return
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    print(f"🔍 Recherche de la facture maltaise {target_id} parmi {len(pdf_files)} PDF")
    print("=" * 70)
    
    found_malta_pdf = False
    
    for pdf_file in pdf_files:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                # Extrait le texte de toutes les pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\\n"
                
                # Cherche l'ID ou le numéro de facture maltaise
                if target_id in full_text or target_invoice in full_text:
                    found_malta_pdf = True
                    print(f"🎯 FACTURE MALTAISE TROUVÉE: {pdf_file.name}")
                    print("=" * 50)
                    
                    # Affiche le texte complet pour analyse
                    print("📄 TEXTE COMPLET EXTRAIT:")
                    print("-" * 40)
                    print(full_text)
                    print("-" * 40)
                    
                    # Test les patterns de nom existants
                    print("\\n🔍 TEST DES PATTERNS DE NOM:")
                    print("-" * 40)
                    
                    name_patterns = [
                        # Nouveaux patterns ajoutés
                        r'(?:\\d{2}\\s+(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\\s+\\d{4})\\s+([A-Z][A-Z\\s]+?)\\s+(?:Numero|numero|NUMERO)',
                        r'€\\s*\\d+[,.]?\\d*\\s+([A-Z][A-Z\\s]+?)\\s+(?:VIA|STRADA|CORSO|PIAZZA|RUE|AVENUE|STREET)',
                        r'pagare\\s+€\\s*\\d+[,.]?\\d*\\s+([A-Z][A-Z\\s]+?)\\s+(?:VIA|STRADA|CORSO|PIAZZA)',
                        r'(?<!Venduto da )(?<!Sold by )(?<!SAS )([A-Z][A-Z\\s]{8,}?)\\s+(?:VIA|STRADA|CORSO|PIAZZA|RUE|AVENUE|STREET)\\s+[A-Z]',
                        
                        # Patterns pour français/anglais (Malte)
                        r'(?:\\d{2}\\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\\s+\\d{4})\\s+([A-Z][a-z]+\\s+[A-Z][a-z]+)',
                        r'(?:\\d{2}\\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{4})\\s+([A-Z][a-z]+\\s+[A-Z][a-z]+)',
                        
                        # Patterns generiques
                        r'Ship\\s*to[:\\s]+([A-Za-z][A-Za-z\\s]{2,50}?)(?=\\s*(?:via|rue|street|avenue|\\d))',
                        r'Bill\\s*to[:\\s]+([A-Za-z][A-Za-z\\s]{2,50}?)(?=\\s*(?:via|rue|street|avenue|\\d))',
                        r'([A-Z][a-z]+\\s+[A-Z][a-z]+)\\s+(?:VIA|RUE|AVENUE|STREET)',
                        
                        # Pattern très large pour capturer tout nom avant adresse
                        r'([A-Z][A-Za-z\\s]+?)\\s+(?:[A-Z]{3}\\s?\\d{4})',  # Nom avant code postal maltais
                    ]
                    
                    found_name = None
                    for i, pattern in enumerate(name_patterns):
                        print(f"\\nPattern {i+1}: {pattern}")
                        try:
                            matches = re.findall(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                            if matches:
                                print(f"    ✅ Trouvé: {matches}")
                                # Prendre le premier match valide
                                for match in matches:
                                    clean_match = match.strip()
                                    # Vérifier que ce n'est pas un code ou autre
                                    if (len(clean_match) > 3 and 
                                        not re.match(r'^[A-Z0-9]+$', clean_match) and
                                        'COMPUTER' not in clean_match and
                                        'SAS' not in clean_match and
                                        'P. IVA' not in clean_match):
                                        found_name = clean_match
                                        print(f"    🎯 NOM CANDIDAT: '{found_name}'")
                                        break
                            else:
                                print(f"    ❌ Aucun match")
                        except re.error as e:
                            print(f"    ❌ Erreur regex: {e}")
                    
                    if not found_name:
                        print("\\n🔍 RECHERCHE MANUELLE DE NOMS:")
                        print("-" * 40)
                        
                        # Cherche des patterns de noms manuellement
                        lines = full_text.split('\\n')
                        for i, line in enumerate(lines):
                            line = line.strip()
                            # Cherche des lignes qui ressemblent à des noms
                            if (len(line) > 3 and 
                                re.match(r'^[A-Z][A-Za-z\\s]+$', line) and
                                not any(word in line.upper() for word in ['AMAZON', 'INVOICE', 'FACTURE', 'DATE', 'TOTAL', 'VIA', 'RUE', 'STREET', 'AVENUE'])):
                                print(f"  Ligne {i}: '{line}'")
                                if i < len(lines) - 1:
                                    print(f"    Ligne suivante: '{lines[i+1].strip()}'")
                                print()
                    
                    break
                    
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {pdf_file.name}: {e}")
    
    if not found_malta_pdf:
        print("⚠️  Facture maltaise non trouvée dans uploads/")
        print("   Les PDF ont peut-être été supprimés ou renommés")

if __name__ == "__main__":
    analyze_malta_invoice()
