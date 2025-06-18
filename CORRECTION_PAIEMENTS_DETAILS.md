# Correction des méthodes de paiement - Problèmes identifiés

## Problèmes détectés

1. **"Shopify Payments" incorrectement classés comme "Virement bancaire"**
   - Les paiements par carte ne doivent PAS être des virements bancaires
   - Les cellules doivent rester vides pour les paiements par carte

2. **PayPal non détecté**
   - L'information PayPal se trouve dans la colonne "Payment Method Name" du fichier transactions
   - Cette colonne n'est pas incluse dans les colonnes requises
   - La logique ne regarde que "Payment Method" du fichier commandes

3. **Logique de catégorisation incorrecte**
   - Tous les paiements par carte sont actuellement classés comme virements
   - Manque de distinction entre vraie carte bancaire et vrais virements

## Corrections à apporter

### 1. Mise à jour des colonnes requises
```python
# AVANT:
required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net']

# APRÈS:
required_transactions_cols = ['Order', 'Presentment Amount', 'Fee', 'Net', 'Payment Method Name']
```

### 2. Mise à jour du nettoyage des données
```python
# AVANT:
df_transactions = clean_text_data(df_transactions, ['Order'])

# APRÈS:
df_transactions = clean_text_data(df_transactions, ['Order', 'Payment Method Name'])
```

### 3. Nouvelle signature de fonction
```python
# AVANT:
def categorize_payment_method(payment_method, ttc_value, fallback_amount=None):

# APRÈS:
def categorize_payment_method(payment_method_orders, payment_method_transactions, ttc_value, fallback_amount=None):
```

### 4. Nouvelle logique de catégorisation
- **PRIORITÉ 1**: Vérifier PayPal dans `Payment Method Name` (transactions)
- **PRIORITÉ 2**: ALMA et Younited 
- **PRIORITÉ 3**: Vrais virements bancaires seulement (virement, wire, bank, custom)
- **IMPORTANT**: Paiements par carte (Shopify Payments, credit_card, carte) → cellules vides
- **DÉFAUT**: Méthodes non reconnues → cellules vides

### 5. Mise à jour de l'appel de fonction
```python
# AVANT:
lambda row: categorize_payment_method(
    row['Payment Method'], 
    corrected_amounts['TTC'].loc[row.name] if row.name in corrected_amounts['TTC'].index else None,
    fallback_amount=row.get('Total', 0)
)

# APRÈS:
lambda row: categorize_payment_method(
    row.get('Payment Method'),  # Méthode de paiement des commandes
    row.get('Payment Method Name'),  # Méthode de paiement des transactions (plus précise pour PayPal)
    corrected_amounts['TTC'].loc[row.name] if row.name in corrected_amounts['TTC'].index else None,
    fallback_amount=row.get('Total', 0)
)
```

## État actuel
- ✅ Colonnes requises mises à jour 
- ✅ Nettoyage des données mis à jour (première occurrence)
- ✅ Nouvelle fonction categorize_payment_method créée
- ❌ Appels de fonction pas encore mis à jour (problème de duplications dans le code)

## Prochaines étapes
1. Corriger les appels de fonction dans les 3 occurrences
2. Supprimer les duplications de code
3. Tester avec des fichiers réels

Date: 17 décembre 2024
