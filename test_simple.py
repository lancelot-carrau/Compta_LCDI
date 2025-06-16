import pandas as pd

# Test simple de création d'un DataFrame avec colonnes Shopify réalistes
print("=== TEST SIMPLE DE MAPPING DES COLONNES ===")

# Simuler un fichier commandes Shopify
df_orders = pd.DataFrame({
    'Id': ['#1001', '#1002'],
    'Billing Name': ['Client 1', 'Client 2'],
    'Financial Status': ['paid', 'pending'],
    'Tax 1 Value': [20.0, 15.5],
    'Outstanding Balance': [0.0, 50.0],
    'Payment Method': ['PayPal', 'Virement'],
    'Fulfilled at': ['2024-01-15', '2024-01-16']
})

print("Colonnes du DataFrame de test:")
print(list(df_orders.columns))

# Test du mapping
column_mappings = {
    'Name': ['Name', 'Id', 'Order'],
    'Billing name': ['Billing name', 'Billing Name', 'Client'],
}

# Simuler le mapping
for expected_col, variants in column_mappings.items():
    found = False
    for variant in variants:
        if variant in df_orders.columns:
            print(f"✓ Mapping trouvé: {variant} -> {expected_col}")
            found = True
            break
    if not found:
        print(f"❌ Aucun mapping trouvé pour: {expected_col}")

print("Test terminé avec succès!")
