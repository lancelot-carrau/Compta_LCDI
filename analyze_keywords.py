#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_amazon_keywords():
    """Analyser les mots-clés Amazon dans le texte de la facture italienne"""
    
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
Per domande relative al tuo ordine, ti preghiamo di visitare il sito www.amazon.it/contact-us"""
    
    amazon_keywords = [
        'amazon', 'Amazon', 'AMAZON',
        'invoice', 'Invoice', 'INVOICE',
        'facture', 'Facture', 'FACTURE', 
        'fattura', 'Fattura', 'FATTURA',
        'order', 'Order', 'ORDER',
        'commande', 'Commande', 'COMMANDE',
        'ordine', 'Ordine', 'ORDINE',
        # Ajout de patterns Amazon spécifiques
        'INV-', 'FR500', 'FR199', 'EU SARL', 'amazon.com',
        'Business EU', 'Marketplace'
    ]
    
    print("=== ANALYSE DES MOTS-CLÉS AMAZON ===")
    print(f"Texte longueur: {len(text)}")
    print(f"Début: {text[:200]}")
    
    found_keywords = []
    for keyword in amazon_keywords:
        if keyword in text:
            found_keywords.append(keyword)
            print(f"✅ Trouvé: '{keyword}'")
    
    if not found_keywords:
        print("❌ Aucun mot-clé Amazon trouvé!")
        print("Recherche de mots similaires...")
        # Chercher des patterns Amazon dans le texte
        amazon_patterns = [
            r'amazon\.it',
            r'FR\d{11}',
            r'Numero fattura',
            r'Data ordine',
            r'Venduto da',
            r'P\. IVA'
        ]
        
        for pattern in amazon_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"✅ Pattern trouvé '{pattern}': {matches}")
    else:
        print(f"✅ Mots-clés trouvés: {found_keywords}")

if __name__ == "__main__":
    analyze_amazon_keywords()
