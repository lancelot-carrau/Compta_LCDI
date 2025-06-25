#!/usr/bin/env python3
"""
Debug détaillé des patterns pour comprendre l'ordre d'exécution
"""
import re

# Texte du problème ADF INFORMATIQUE
text = """Total à payer 229,66 €ADF INFORMATIQUE
20 % 191,38 € 38,28 €
Total 191,38 € 38,28 €
Veuillez vous référer à la première page pour les informations de paiementMontant dû 229,66 €
ASIN: B0B4P5S94P2 95,69 € 20 % 114,83 € 229,66 €"""

print("🔍 DEBUG DÉTAILLÉ DES PATTERNS HT")
print("=" * 60)
print("Texte à analyser:")
print(text)
print("=" * 60)

# Patterns de subtotal (HT) dans l'ordre d'exécution
subtotal_patterns = [
    # PATTERNS PRIORITAIRES pour tableaux HT/TVA sur même ligne
    (r'Total\s+(\d+[,.]?\d{0,2})\s*€\s+\d+[,.]?\d{0,2}\s*€', "Pattern français Total HT TVA (priorité 1)"),
    (r'Sous-total\s+(\d+[,.]?\d{0,2})\s*€\s+\d+[,.]?\d{0,2}\s*€', "Pattern français Sous-total HT TVA (priorité 2)"),
    (r'(\d+)%\s+([\d,]+)\s*€\s+[\d,]+\s*€', "Pattern italien % HT TVA (priorité 3)"),
    
    # Patterns PRIORITAIRES pour montant HT 
    (r'Totale\s*prima\s*delle\s*tasse[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern italien Totale prima delle tasse"),
    (r'Subtotale\s*articoli[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern italien Subtotale articoli"),
    
    # NOUVEAUX PATTERNS pour factures françaises/anglaises
    (r'(?:Items|Articles)[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Items/Articles"),
    (r'Order\s*Subtotal[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Order Subtotal"),
    (r'Subtotal\s*before\s*tax[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Subtotal before tax"),
    (r'Total\s*before\s*VAT[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Total before VAT"),
    (r'Montant\s*avant\s*taxe[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Montant avant taxe"),
    (r'Total\s*avant\s*TVA[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Total avant TVA"),
    
    # Patterns génériques
    (r'Subtotale[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Subtotale générique"),
    (r'Subtotal[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Subtotal générique"),
    (r'Sous-total[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Sous-total générique"),
    (r'Sub-total[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Sub-total générique"),
    (r'Net\s*Amount[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Net Amount"),
    (r'Montant\s*HT[^€]*€\s*(\d+[,.]?\d{0,2})', "Pattern Montant HT"),
    
    # Patterns avec deux points
    (r'(?:Subtotale|Subtotal|Sous-total|Sub-total|Items|Articles)[:\s]+(\d+[,.]?\d{0,2})\s*€', "Pattern avec : variante 1"),
    (r'(?:Net\s*Amount|Montant\s*HT|Order\s*Subtotal)[:\s]+(\d+[,.]?\d{0,2})\s*€', "Pattern avec : variante 2"),
    (r'(?:Total\s*before|Montant\s*avant|Subtotal\s*before)[^€]*[:\s]+(\d+[,.]?\d{0,2})\s*€', "Pattern avec : variante 3"),
    
    # PATTERNS DE FALLBACK
    (r'(\d+[,.]?\d{0,2})\s*€[^€]*(?:before|avant)\s*(?:tax|VAT|TVA|IVA)', "Fallback before tax"),
    (r'(\d+[,.]?\d{0,2})\s*€[^€]*(?:excluding|hors|excl\.?)\s*(?:VAT|TVA|IVA)', "Fallback excluding VAT"),
    (r'(\d+[,.]?\d{0,2})\s*€[^€\n]{0,20}?(?:\d+[,.]?\d*)\s*%', "Fallback montant + %"),
]

print("Testis de chaque pattern:")
print()

for i, (pattern, description) in enumerate(subtotal_patterns, 1):
    matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
    if matches:
        print(f"{i:2d}. ✅ {description}")
        for match in matches:
            if len(match.groups()) == 1:
                print(f"     🎯 Match: '{match.group(1)}' (dans: '{match.group(0)}')")
            elif len(match.groups()) == 2:
                print(f"     🎯 Match: Groupe 1='{match.groups()[0]}', Groupe 2='{match.groups()[1]}' (dans: '{match.group(0)}')")
                # Pour les patterns à 2 groupes, indiquer lequel est utilisé selon la logique
                if 'Total\\s+' in pattern and '€\\s+\\d+' in pattern:
                    print(f"     ➡️  HT utilisé: {match.groups()[0]} (pattern français, groupe 1)")
                else:
                    print(f"     ➡️  HT utilisé: {match.groups()[1]} (pattern italien, groupe 2)")
        print()
    else:
        print(f"{i:2d}. ❌ {description}")

print("\n🎯 CONCLUSION:")
print("Le premier pattern qui match dans l'ordre ci-dessus sera utilisé pour extraire le HT.")
