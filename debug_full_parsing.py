#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer les fonctions de app.py
from app import parse_amazon_invoice_data

def debug_parsing():
    """Debug complet du parsing d'une facture italienne"""
    
    # Texte réel de la facture italienne
    text = """Fattura
Pagina 1 di 1L'IVA del paese di destinazione è stata addebitata e sara' dichiarata nella registrazione IVA del regime UE One Stop Shop (OSS), menzionata in questa fatturaIVA %  Prezzo Totale
(IVA esclusa)Subtotale IVA
22% 696,71 € 153,28 €
Totale 696,71 € 153,28 €Totale fattura 849,99 €Dettagli fatturaData ordine 29 gennaio 2025   Contratto 402-7933303-9707500Pagato
 Numero di riferimento del pagamento H8hkbFJpd9BM4fTLttEI
Venduto da SAS 3W COMPUTER
P. IVA FR19797666666
Data di fatturazione / Data di consegna 03 febbraio 2025
Numero fattura FR50006SHCVZJU
Totale da pagare 849,99 €CRISTINA MORARU
VIA CIVITA CASTELLANA 24, SECONDO PIANO
CASTEL SANT'ELIA, VITERBO, 01030
IT
Per domande relative al tuo ordine, ti preghiamo di visitare il sito www.amazon.it/contact-us
Indirizzo di fatturazione
Cristina Moraru
Via Civita Castellana 24, Secondo piano
Castel Sant'Elia, Viterbo, 01030
IT Indirizzo di spedizione
Cristina Moraru
Via Civita Castellana 24, Secondo piano
Castel Sant'Elia, Viterbo, 01030
IT Venduto da
SAS 3W COMPUTER
24 RUE MONTGALLET
PARIS, 75012
FR
P. IVA FR19797666666
Informazioni sull'ordine
Descrizione Quant. P. Unitario
(IVA esclusa)IVA % P. Unitario
(IVA inclusa) Prezzo Totale
(IVA inclusa)
INFOMAX | PC Gamer, Desktop, PC Gaming - Processore AMD Ryzen 5
4500 • NVIDIA RTX 4060 8 GB • RAM 16 GB • SSD 500 GB • SCATOLA
ARGB Aquarius • FREEDOS
ASIN: B0CKN7N3HQ1 696,71 € 22% 849,99 € 849,99 €
Costi di spedizione 0,00 € 0,00 € 0,00 €"""
    
    print("=== DEBUG COMPLET DU PARSING ===")
    print(f"Longueur du texte: {len(text)}")
    
    # Appel avec debug activé
    result = parse_amazon_invoice_data(text, debug_mode=True, filename="batch_4_1713_TVA_2200_IT_2025-02-03_FR50006SHCVZJU_84999.pdf")
    
    print(f"\n=== RÉSULTAT FINAL ===")
    if result:
        print("✅ Parsing réussi!")
        for key, value in result.items():
            if key != 'debug_info':
                print(f"  {key}: {value}")
        
        if 'debug_info' in result:
            print(f"\n=== DEBUG INFO ===")
            for info in result['debug_info']:
                print(f"  {info}")
    else:
        print("❌ Parsing échoué - résultat None")

if __name__ == "__main__":
    debug_parsing()
