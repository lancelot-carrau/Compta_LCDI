#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pdfplumber
from pathlib import Path
import re

def analyze_problematic_pdfs():
    """Analyse les PDF problématiques identifiés dans l'Excel"""
    
    # Les IDs des factures problématiques
    problematic_ids = [
        "406-7925504-5225948",  # Malte
        "408-6932364-3574702"   # Italie  
    ]
    
    # Cherche les PDF correspondants
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ Dossier uploads non trouvé")
        return
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    print(f"📄 {len(pdf_files)} PDF trouvés dans uploads/")
    
    for pdf_file in pdf_files:
        print(f"\n📄 Analyse de: {pdf_file.name}")
        print("=" * 60)
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                # Extrait le texte de toutes les pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\\n"
                
                # Cherche les IDs problématiques
                found_problematic = False
                for prob_id in problematic_ids:
                    if prob_id in full_text:
                        found_problematic = True
                        print(f"🎯 PDF problématique trouvé ! ID: {prob_id}")
                        break
                
                if found_problematic:
                    print("📄 TEXTE EXTRAIT:")
                    print("-" * 40)
                    print(full_text[:2000])  # Premiers 2000 caractères
                    print("\\n[...texte tronqué...]")
                    print("-" * 40)
                    
                    # Test les patterns d'extraction de noms actuels
                    print("\\n🔍 TEST DES PATTERNS DE NOM:")
                    
                    # Patterns actuels de l'app
                    name_patterns = [
                        # Pattern principal avec € et montant
                        r'€\\s*(?:\\d+[,.]?\\d*)\\s*([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïñòóôõö÷øùúûüýþÿ][A-Za-zÀ-ÿ\\s\\-\']{1,50}?)(?=\\s|$|\\n)',
                        
                        # Pattern avec montant sans €
                        r'(?:\\d+[,.]\\d{2})\\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïñòóôõö÷øùúûüýþÿ][A-Za-zÀ-ÿ\\s\\-\']{1,50}?)(?=\\s|$|\\n)',
                        
                        # Pattern après numéro de commande
                        r'(?:order|ordine|commande|commanda)\\s*[#:]?\\s*\\d+[^\\n]*\\n\\s*([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïñòóôõö÷øùúûüýþÿ][A-Za-zÀ-ÿ\\s\\-\']{1,50}?)(?=\\s|$|\\n)',
                        
                        # Pattern générique nom + adresse
                        r'\\n\\s*([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïñòóôõö÷øùúûüýþÿ][A-Za-zÀ-ÿ\\s\\-\']{2,50}?)\\s*\\n\\s*(?:[A-Za-z0-9\\s,.-]+\\s*\\n|\\d{5})',
                    ]
                    
                    for i, pattern in enumerate(name_patterns):
                        print(f"\\n  Pattern {i+1}: {pattern}")
                        matches = re.findall(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                        if matches:
                            print(f"    ✅ Trouvé: {matches}")
                        else:
                            print(f"    ❌ Aucun match")
                    
                    # Cherche les sections potentielles avec des noms
                    print("\\n🔍 RECHERCHE DE SECTIONS AVEC NOMS:")
                    lines = full_text.split('\\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line and len(line) > 3:
                            # Cherche les lignes qui pourraient contenir des noms
                            if re.match(r'^[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïñòóôõö÷øùúûüýþÿ][A-Za-zÀ-ÿ\\s\\-\']{5,}', line):
                                print(f"    Ligne {i}: {line}")
                                if i < len(lines) - 1:
                                    print(f"    Ligne {i+1}: {lines[i+1].strip()}")
                                print()
                
                if not found_problematic:
                    # Affiche quand même les IDs trouvés pour référence
                    amazon_ids = re.findall(r'(\\d{3}-\\d{7}-\\d{7})', full_text)
                    if amazon_ids:
                        print(f"🔍 IDs Amazon trouvés: {amazon_ids}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {pdf_file.name}: {e}")

if __name__ == "__main__":
    analyze_problematic_pdfs()
