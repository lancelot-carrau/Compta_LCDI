#!/usr/bin/env python3
"""
Script pour vérifier que toutes les dépendances requises sont installées
"""

import sys
import importlib
import pkg_resources

# Liste des dépendances requises
REQUIRED_PACKAGES = [
    'flask',
    'pandas', 
    'werkzeug',
    'openpyxl',
    'chardet',
    'requests'  # Ajouté pour les tests
]

# Modules built-in Python qui ne nécessitent pas d'installation
BUILTIN_MODULES = [
    'os',
    'datetime', 
    'tempfile',
    'io',
    're',
    'webbrowser',
    'threading',
    'time',
    'sys'
]

def check_package(package_name):
    """Vérifie si un package est installé et retourne sa version"""
    try:
        module = importlib.import_module(package_name)
        try:
            version = pkg_resources.get_distribution(package_name).version
            return True, version
        except:
            # Pour les modules qui n'ont pas de version via pkg_resources
            return True, "Version inconnue"
    except ImportError:
        return False, None

def main():
    print("🔍 Vérification des dépendances Python...")
    print("=" * 50)
    
    all_ok = True
    
    print("\n📦 Packages requis:")
    for package in REQUIRED_PACKAGES:
        is_installed, version = check_package(package)
        if is_installed:
            print(f"✅ {package:<12} - v{version}")
        else:
            print(f"❌ {package:<12} - NON INSTALLÉ")
            all_ok = False
    
    print("\n🐍 Modules Python built-in:")
    for module in BUILTIN_MODULES:
        is_available, _ = check_package(module)
        if is_available:
            print(f"✅ {module}")
        else:
            print(f"❌ {module} - NON DISPONIBLE")
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ Toutes les dépendances sont installées !")
    else:
        print("❌ Certaines dépendances manquent.")
        print("Exécutez: pip install -r requirements.txt")
    
    print(f"\n🐍 Version Python: {sys.version}")
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
