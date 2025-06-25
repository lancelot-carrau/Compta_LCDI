#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner tous les PDFs pour identifier la facture de Zacharie Carpentier
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_text

def scan_all_pdfs():
    """Scanner tous les PDFs dans le dossier uploads"""
    uploads_dir = "uploads"
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Dossier {uploads_dir} non trouvé")
        return
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ Aucun fichier PDF trouvé dans {uploads_dir}")
        return
    
    print(f"📁 Analyse de {len(pdf_files)} fichiers PDF...")
    print("=" * 80)
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(uploads_dir, pdf_file)
        print(f"\n📄 FICHIER: {pdf_file}")
        print("-" * 50)
        
        try:
            text = extract_pdf_text(pdf_path)
            
            # Chercher des indices pour identifier Zacharie Carpentier
            if 'zacharie' in text.lower() or 'carpentier' in text.lower():
                print("🎯 ZACHARIE CARPENTIER DÉTECTÉ !")
            
            # Extraire les informations clés
            lines = text.split('\n')
            
            # Chercher le nom du client
            for line in lines:
                if any(keyword in line.lower() for keyword in ['facturation', 'livraison', 'billing', 'shipping']):
                    print(f"📍 Adresse: {line.strip()}")
                    break
            
            # Chercher les montants
            montants_found = []
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if any(keyword in line_clean.lower() for keyword in ['total', 'montant', 'ht', 'tva', '€']):
                    if any(char.isdigit() for char in line_clean):
                        # Chercher spécifiquement les montants de Zacharie (193,32 / 38,66 / 231,98)
                        if ('193' in line_clean and '32' in line_clean) or \
                           ('38' in line_clean and '66' in line_clean) or \
                           ('231' in line_clean and '98' in line_clean):
                            print(f"💰 MONTANT ZACHARIE: {line_clean}")
                            montants_found.append(line_clean)
                        elif any(amount in line_clean for amount in ['191,38', '38,28', '229,66']):
                            print(f"💰 Montant ADF: {line_clean}")
                        elif '€' in line_clean and any(char.isdigit() for char in line_clean):
                            print(f"💰 Autre montant: {line_clean}")
            
            if montants_found:
                print("🎯 FACTURE ZACHARIE CARPENTIER IDENTIFIÉE !")
            
            # Chercher le nom du contact/client
            contact_keywords = ['fatturazione', 'billing', 'livraison', 'shipping', 'client']
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in contact_keywords):
                    # Regarder les 3 lignes suivantes pour le nom
                    for j in range(1, 4):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            if next_line and not any(char.isdigit() for char in next_line[:5]):
                                if len(next_line) > 3 and not any(keyword in next_line.lower() for keyword in ['tva', 'vat', 'rue', 'via']):
                                    print(f"👤 Client potentiel: {next_line}")
                                    break
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {pdf_file}: {e}")
        
        print()

if __name__ == "__main__":
    scan_all_pdfs()
