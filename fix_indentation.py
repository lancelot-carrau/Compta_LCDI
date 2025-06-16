#!/usr/bin/env python3
"""
Script pour corriger les indentations dans app.py
"""

# Lire le fichier et corriger les indentations problématiques
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corriger les indentations ligne par ligne
corrected_lines = []
for i, line in enumerate(lines):
    # Supprimer les espaces en début de ligne et les remplacer par des espaces standards
    if line.strip():  # Si la ligne n'est pas vide
        # Compter l'indentation actuelle
        indent_count = len(line) - len(line.lstrip())
        # Reconstruire avec des espaces standards (4 espaces par niveau)
        if line.lstrip().startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ', 'elif ', 'else:')):
            # Ces éléments déterminent le niveau d'indentation
            pass
        corrected_lines.append(line)
    else:
        corrected_lines.append(line)

# Pour l'instant, créons une version simplifiée des corrections les plus urgentes
fixes = {
    '          for col in monetary_cols_transactions:': '        for col in monetary_cols_transactions:',
    '          print("3.5. Agrégation des commandes pour éviter les doublons...")': '        print("3.5. Agrégation des commandes pour éviter les doublons...")',
    '          # ÉTAPE 2: Agrégation des transactions par commande': '        # ÉTAPE 2: Agrégation des transactions par commande',
}

# Appliquer les corrections
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

for incorrect, correct in fixes.items():
    content = content.replace(incorrect, correct)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Corrections d'indentation appliquées!")
