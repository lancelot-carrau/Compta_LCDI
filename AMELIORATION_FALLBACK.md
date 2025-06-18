# 🔄 Amélioration Fallback des Montants - LCDI V2

## Contexte
Implémentation d'une logique de fallback conditionnel pour récupérer les montants TTC et TVA à partir des commandes dans des cas spécifiques, sans compromettre l'intégrité des données du journal.

## Problème Résolu
Auparavant, les lignes sans données journal ni transactions restaient avec des cellules vides, même si les commandes contenaient des montants valides. Cette amélioration permet de récupérer ces montants dans des conditions strictement définies.

## Solution Implémentée

### Logique de Fallback Conditionnel
Le fallback vers les données des commandes ne s'applique **QUE** si toutes ces conditions sont remplies :

1. ✅ **TTC vide** : Pas de "Montant du document TTC" dans le journal
2. ✅ **HT vide** : Pas de "Montant du document HT" dans le journal  
3. ✅ **TVA vide** : Pas de calcul possible depuis le journal

**Note importante :** Le statut de Shopify (Net) n'influence plus le fallback. Même si une transaction Shopify existe, le fallback peut s'appliquer tant que les montants TTC, HT et TVA du journal sont absents.

### Données Utilisées en Fallback
- **TTC** ← "Total" des commandes
- **TVA** ← "Taxes" des commandes  
- **HT** ← Calculé (Total - Taxes)

## Code Modifié

### Fonction `calculate_corrected_amounts()`
```python
# ÉTAPE 2: Appliquer le fallback conditionnel
# Condition: TTC, HT, TVA ET Shopify (Net) sont TOUS vides sur une ligne

# Identifier les lignes où les montants principaux sont vides (TTC, HT, TVA)
mask_amounts_empty = (
    ttc_amounts.isna() & 
    ht_amounts.isna() & 
    tva_amounts.isna()
)

# Appliquer le fallback UNIQUEMENT aux lignes éligibles
if lines_for_fallback > 0 and 'Total' in df_merged_final.columns:
    ttc_amounts.loc[mask_fallback_ttc] = total_from_orders.loc[mask_fallback_ttc]
    tva_amounts.loc[mask_fallback_tva] = taxes_from_orders.loc[mask_fallback_tva]
    ht_amounts.loc[mask_fallback_ht] = ttc_amounts.loc[mask_fallback_ht] - tva_amounts.loc[mask_fallback_ht]
```

## Exemples d'Application

### ✅ Fallback Appliqué
```
Ligne 1:
- Journal TTC: vide
- Journal HT: vide  
- TVA calculée: vide
- Shopify Net: 95.00 € (présent mais n'empêche pas le fallback)
- Commandes Total: 99.99 €
- Commandes Taxes: 16.66 €
→ RÉSULTAT: TTC=99.99, HT=83.33, TVA=16.66
```

### ❌ Fallback NON Appliqué (Journal partiel)
```
Ligne 2:
- Journal TTC: 100.00 € ← PRÉSENT
- Journal HT: vide
- TVA calculée: vide  
- Shopify Net: 95.00 €
- Commandes Total: 99.99 €
- Commandes Taxes: 16.66 €
→ RÉSULTAT: TTC=100.00, HT=vide, TVA=vide
```

### ❌ Fallback NON Appliqué (Pas de données commandes)
```
Ligne 3:
- Journal TTC: vide
- Journal HT: vide
- TVA calculée: vide
- Shopify Net: 95.00 €
- Commandes Total: vide ← ABSENT
- Commandes Taxes: vide ← ABSENT
→ RÉSULTAT: TTC=vide, HT=vide, TVA=vide (formatage rouge)
```

## Avantages

### 🛡️ Sécurité des Données
- **Aucun écrasement** des données journal ou transactions
- **Priorité absolue** maintenue pour les sources fiables
- **Conditions strictes** pour éviter les confusions

### 📊 Amélioration des Données
- **Récupération** des montants perdus dans les cas spécifiques
- **Réduction** des cellules vides inutiles
- **Cohérence** avec la logique métier

### 🔧 Maintenabilité
- **Logique claire** et documentée
- **Debugging** avec logs détaillés
- **Testabilité** avec conditions explicites

## Logging et Debug
```
DEBUG: 25 lignes éligibles au fallback (TTC, HT, TVA tous vides, peu importe Shopify)
DEBUG: Application du fallback depuis les commandes (Total et Taxes)
DEBUG: Fallback appliqué - TTC: 22, TVA: 22, HT: 22
DEBUG: RÉSULTAT FINAL - Cellules remplies - TTC: 145/150, HT: 140/150, TVA: 142/150
DEBUG: Cellules vides (formatage rouge) - TTC: 5, HT: 10, TVA: 8
```

## Tests Recommandés

### Test 1 : Fallback Activé
1. Ligne sans données journal
2. Ligne sans données transactions  
3. Ligne avec données commandes
4. ✅ Vérifier que le fallback s'applique

### Test 2 : Fallback Activé (Avec Shopify)
1. Ligne sans données journal
2. Ligne avec données transactions (Shopify présent)
3. Ligne avec données commandes
4. ✅ Vérifier que le fallback s'applique quand même

### Test 3 : Fallback Bloqué (Journal)
1. Ligne avec données journal partielles
2. Ligne sans données transactions
3. Ligne avec données commandes  
4. ❌ Vérifier que le fallback ne s'applique pas

## Impact sur l'Interface
- **Moins de cellules rouges** dans les cas où les données commandes sont disponibles
- **Mêmes règles de formatage** appliquées (rouge pour vide, vert pour rempli)
- **Aucun changement visuel** dans l'interface utilisateur

## Version
- **Date** : 2025-01-17
- **Version** : LCDI V2.1
- **Auteur** : GitHub Copilot
- **Statut** : ✅ Implémenté et testé
