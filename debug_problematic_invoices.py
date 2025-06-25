#!/usr/bin/env python3
import os
from app import process_pdf_extraction, parse_amazon_invoice_data

def debug_specific_invoice(pdf_file):
    """Débugge une facture spécifique pour comprendre pourquoi le nom n'est pas extrait"""
    pdf_path = os.path.join('uploads', pdf_file)
    print(f"\n" + "="*80)
    print(f"DEBUG DE: {pdf_file}")
    print("="*80)
    
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return
    
    try:
        # Extraire le texte PDF
        extraction_result = process_pdf_extraction(pdf_path)
        if not extraction_result['success']:
            print(f"❌ Erreur extraction PDF: {extraction_result['errors']}")
            return
        
        print(f"📄 TEXTE EXTRAIT ({len(extraction_result['text'])} caractères):")
        print("-" * 60)
        print(extraction_result['text'])
        print("-" * 60)
        
        # Parser avec mode debug
        print(f"\n🔍 PARSING AVEC DEBUG:")
        print("-" * 60)
        extracted_data = parse_amazon_invoice_data(
            extraction_result['text'], 
            debug_mode=True,  # MODE DEBUG ACTIVÉ
            filename=pdf_file,
            pdf_path=pdf_path
        )
        
        print(f"\n📊 RÉSULTATS D'EXTRACTION:")
        print("-" * 60)
        for key, value in extracted_data.items():
            status = "✅" if value and str(value).strip() else "❌"
            print(f"{status} {key}: {repr(value)}")
        
        # Focus sur les noms dans le texte
        print(f"\n🔎 RECHERCHE DE NOMS DANS LE TEXTE:")
        print("-" * 60)
        text_lines = extraction_result['text'].split('\n')
        for i, line in enumerate(text_lines):
            line = line.strip()
            if line:
                # Chercher des patterns qui pourraient être des noms
                if any(char.isalpha() for char in line) and len(line) > 3:
                    print(f"Ligne {i+1:2d}: {repr(line)}")
        
    except Exception as e:
        print(f"❌ Erreur lors du debug: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Factures problématiques identifiées
    problematic_invoices = [
        "1761 TVA 20,00% FR 2025-05-03 FR5003P9HCVZJI 115,99€.pdf",
        "1763 TVA 21,00% ES 2025-05-08 FR5000JGHCVZJU 117,49€.pdf", 
        "batch_5_1714_TVA_2200_IT_2025-02-04_FR50006WHCVZJU_11525.pdf"
    ]
    
    print("ANALYSE DES FACTURES PROBLÉMATIQUES")
    print("="*80)
    print(f"Analyse de {len(problematic_invoices)} factures sans nom extrait...")
    
    for pdf_file in problematic_invoices:
        debug_specific_invoice(pdf_file)
    
    print(f"\n" + "="*80)
    print("FIN DE L'ANALYSE")
    print("="*80)

if __name__ == "__main__":
    main()
