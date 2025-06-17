#!/usr/bin/env python3
"""
Script pour corriger les erreurs dtype dans app.py
"""

def fix_dtype_errors():
    """Corriger les erreurs dtype dans app.py"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les occurrences problématiques
    old_pattern = "if df_orders[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df_orders[col]):"
    new_pattern = "try:\n                    if pd.api.types.is_numeric_dtype(df_orders[col]):"
    
    # Compter les occurrences
    count = content.count(old_pattern)
    print(f"Nombre d'occurrences trouvées: {count}")
    
    if count > 0:
        # Remplacer toutes les occurrences
        content = content.replace(old_pattern, new_pattern)
        
        # Ajouter les except manquants
        # Chercher les patterns qui suivent pour ajouter les except
        content = content.replace(
            "elif col not in first_cols:\n                    first_cols.append(col)",
            "elif col not in first_cols:\n                        first_cols.append(col)\n                except Exception as e:\n                    print(f\"   - Erreur lors de l'analyse de la colonne {col}: {e}\")\n                    if col not in first_cols:\n                        first_cols.append(col)"
        )
        
        content = content.replace(
            "elif col not in first_value_cols:\n                    first_value_cols.append(col)",
            "elif col not in first_value_cols:\n                        first_value_cols.append(col)\n                except Exception as e:\n                    print(f\"   - Erreur lors de l'analyse de la colonne {col}: {e}\")\n                    if col not in first_value_cols:\n                        first_value_cols.append(col)"
        )
        
        # Sauvegarder
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Corrections appliquées avec succès!")
    else:
        print("❌ Aucune occurrence trouvée")

if __name__ == "__main__":
    fix_dtype_errors()
