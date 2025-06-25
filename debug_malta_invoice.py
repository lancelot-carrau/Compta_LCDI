import sys
import os
import re
sys.path.append(os.getcwd())

# Importer les fonctions d'extraction de l'app
from app import extract_pdf_text, parse_amazon_invoice_data

# Analyser la facture maltaise problématique
pdf_path = r'1712 TVA 18,00% MT 2025-01-29 FR500063HCVZJU 126,72€.pdf'

print("=== ANALYSE DÉTAILLÉE FACTURE MALTAISE ===")
print(f"Fichier: {pdf_path}")

# Extraire le texte
text = extract_pdf_text(pdf_path)
print(f"Longueur du texte: {len(text)} caractères")
print()

# Afficher le début du texte
print("=== DÉBUT DU TEXTE EXTRAIT ===")
print(text[:1000])
print("=" * 50)

# Afficher des parties spécifiques
print()
print("=== RECHERCHE DE PATTERNS MALTAIS ===")

# Chercher les patterns spécifiques maltais/anglais
patterns_malta = [
    r'Ship\s*to[:\s]+([A-Za-z][A-Za-z\s]{2,50})',
    r'Bill\s*to[:\s]+([A-Za-z][A-Za-z\s]{2,50})',
    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+[A-Z]{3}\s?\d{4}\s+MT\b',
    r'(?:\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
]

for i, pattern in enumerate(patterns_malta, 1):
    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
    print(f"Pattern {i}: {pattern}")
    print(f"  Matches: {matches}")
    print()

# Chercher des mots-clés maltais/anglais
keywords_search = ['Ship to', 'Bill to', 'Invoice', 'Malta', 'MT ', 'MST', 'MLT']
print("=== MOTS-CLÉS TROUVÉS ===")
for keyword in keywords_search:
    if keyword.lower() in text.lower():
        print(f"✓ Trouvé: '{keyword}'")
        # Montrer le contexte
        start = text.lower().find(keyword.lower())
        if start != -1:
            context = text[max(0, start-50):start+100]
            print(f"  Contexte: ...{context}...")
    else:
        print(f"✗ Non trouvé: '{keyword}'")
    print()

# Essayer le parsing complet avec debug
print("=== PARSING AVEC DEBUG ===")
result = parse_amazon_invoice_data(text, debug_mode=True)
if result:
    print("✓ Parsing réussi:")
    for key, value in result.items():
        if key != 'debug_info':
            print(f"  {key}: {value}")
    
    if result.get('debug_info'):
        print("\nInformations de debug:")
        for info in result['debug_info']:
            print(f"  - {info}")
else:
    print("✗ Parsing échoué")
