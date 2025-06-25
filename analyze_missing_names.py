#!/usr/bin/env python3
import os
import sys
from app import process_pdf_extraction, parse_amazon_invoice_data

def analyze_missing_names():
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        print(f"Dossier {uploads_dir} non trouvé")
        return
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans {uploads_dir}")
        return
    
    print(f"Analyse de {len(pdf_files)} factures PDF...")
    print("=" * 80)
    
    missing_names = []
    total_fields = 0
    total_extracted = 0
    
    for pdf_file in sorted(pdf_files):
        pdf_path = os.path.join(uploads_dir, pdf_file)
        print(f"\nAnalyse: {pdf_file}")
        print("-" * 60)
        
        try:
            # Extraire le texte PDF
            extraction_result = process_pdf_extraction(pdf_path)
            if not extraction_result['success']:
                print(f"❌ Erreur extraction PDF: {extraction_result['errors']}")
                missing_names.append(pdf_file)
                continue
            
            # Parser les données Amazon
            extracted_data = parse_amazon_invoice_data(
                extraction_result['text'], 
                debug_mode=False, 
                filename=pdf_file,
                pdf_path=pdf_path
            )
            
            # Compter les champs
            non_empty_fields = {k: v for k, v in extracted_data.items() if v and str(v).strip()}
            total_fields += len(extracted_data)
            total_extracted += len(non_empty_fields)
            
            print(f"Champs extraits: {len(non_empty_fields)}/{len(extracted_data)}")
            
            # Vérifier si le nom manque
            contact_name = extracted_data.get('nom_contact', '').strip()
            if not contact_name:
                missing_names.append(pdf_file)
                print("❌ NOM MANQUANT")
                
                # Afficher tous les champs pour diagnostic
                for key, value in extracted_data.items():
                    status = "✅" if value and str(value).strip() else "❌"
                    print(f"  {status} {key}: {value}")
            else:
                print(f"✅ Nom trouvé: {contact_name}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction: {e}")
            missing_names.append(pdf_file)
    
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Total factures analysées: {len(pdf_files)}")
    print(f"Factures avec nom manquant: {len(missing_names)}")
    print(f"Taux de réussite noms: {((len(pdf_files) - len(missing_names)) / len(pdf_files) * 100):.1f}%")
    print(f"Total champs extraits: {total_extracted}/{total_fields} ({(total_extracted/total_fields*100):.1f}%)")
    
    if missing_names:
        print(f"\nFactures avec nom manquant ({len(missing_names)}):")
        for name in missing_names:
            print(f"  - {name}")
    
    return missing_names

if __name__ == "__main__":
    missing_names = analyze_missing_names()
