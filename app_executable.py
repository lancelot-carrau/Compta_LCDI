from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import os
from datetime import datetime
import tempfile
from werkzeug.utils import secure_filename
import io
import chardet
import re
import webbrowser
import threading
import time
import sys

# Configuration pour PyInstaller
if getattr(sys, 'frozen', False):
    # Application bundled with PyInstaller
    application_path = sys._MEIPASS
    template_dir = os.path.join(application_path, 'templates')
    static_dir = os.path.join(application_path, 'static') if os.path.exists(os.path.join(application_path, 'static')) else None
else:
    # Application running in development
    application_path = os.path.dirname(os.path.abspath(__file__))
    template_dir = 'templates'
    static_dir = 'static'

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration des dossiers
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'csv'}

# Créer les dossiers s'ils n'existent pas
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_encoding(file_path):
    """Détecte automatiquement l'encodage d'un fichier"""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            print(f"Encodage détecté: {encoding} (confiance: {confidence:.2f})")
            
            if confidence < 0.7:
                print("Confiance faible, utilisation de utf-8 par défaut")
                return 'utf-8'
            
            return encoding
    except Exception as e:
        print(f"Erreur lors de la détection d'encodage: {e}")
        return 'utf-8'

def read_csv_safe(file_path):
    """Lit un fichier CSV en gérant l'encodage automatiquement"""
    encoding = detect_encoding(file_path)
    encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            print(f"Tentative de lecture avec l'encodage: {enc}")
            df = pd.read_csv(file_path, encoding=enc)
            print(f"✅ Lecture réussie avec l'encodage: {enc}")
            return df
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"❌ Échec avec l'encodage {enc}: {e}")
            continue
        except Exception as e:
            print(f"❌ Erreur inattendue avec l'encodage {enc}: {e}")
            continue
    
    raise ValueError("Impossible de lire le fichier avec les encodages testés")

def harmonize_columns(df1, df2, priority_df_name="ancien"):
    """
    Harmonise les colonnes de deux DataFrames pour permettre la fusion
    """
    # Colonnes communes
    common_cols = set(df1.columns) & set(df2.columns)
    
    # Colonnes uniques à chaque DataFrame
    df1_only = set(df1.columns) - common_cols
    df2_only = set(df2.columns) - common_cols
    
    print(f"Colonnes communes: {len(common_cols)}")
    print(f"Colonnes uniques au {priority_df_name}: {len(df1_only)}")
    print(f"Colonnes uniques au nouveau: {len(df2_only)}")
    
    # Ajouter les colonnes manquantes avec des valeurs par défaut
    for col in df2_only:
        df1[col] = ''
        print(f"Ajout de la colonne '{col}' au {priority_df_name}")
    
    for col in df1_only:
        df2[col] = ''
        print(f"Ajout de la colonne '{col}' au nouveau")
    
    # Réorganiser les colonnes dans le même ordre
    all_columns = sorted(set(df1.columns) | set(df2.columns))
    df1 = df1.reindex(columns=all_columns, fill_value='')
    df2 = df2.reindex(columns=all_columns, fill_value='')
    
    return df1, df2

def combine_with_old_file(old_df, new_df):
    """
    Combine intelligemment l'ancien fichier avec le nouveau
    Priorité à l'ancien fichier, complément par le nouveau si champ vide
    """
    print("=== FUSION INTELLIGENTE ===")
    print(f"Ancien fichier: {len(old_df)} lignes")
    print(f"Nouveau fichier: {len(new_df)} lignes")
    
    # Harmoniser les colonnes
    old_df, new_df = harmonize_columns(old_df, new_df, "ancien")
    
    # Identifier la colonne de référence (Web) pour éviter les doublons
    ref_column = None
    for col in ['Réf.WEB', 'Ref.WEB', 'Reference Web', 'Web Reference', 'Name']:
        if col in old_df.columns:
            ref_column = col
            break
    
    if ref_column:
        print(f"Colonne de référence trouvée: {ref_column}")
        
        # Créer des sets pour identifier les références existantes
        old_refs = set(old_df[ref_column].dropna().astype(str))
        new_refs = set(new_df[ref_column].dropna().astype(str))
        
        # Références communes (doublons potentiels)
        common_refs = old_refs & new_refs
        print(f"Références communes détectées: {len(common_refs)}")
        
        # Nouvelles références uniquement
        new_only_refs = new_refs - old_refs
        print(f"Nouvelles références à ajouter: {len(new_only_refs)}")
        
        # Ajouter seulement les nouvelles lignes (sans doublons)
        new_rows_to_add = new_df[new_df[ref_column].astype(str).isin(new_only_refs)]
        
        # Pour les références communes, compléter les champs vides de l'ancien avec le nouveau
        for ref in common_refs:
            old_mask = old_df[ref_column].astype(str) == str(ref)
            new_mask = new_df[ref_column].astype(str) == str(ref)
            
            if old_mask.any() and new_mask.any():
                old_row_idx = old_df[old_mask].index[0]
                new_row = new_df[new_mask].iloc[0]
                
                # Compléter les champs vides ou nan de l'ancien fichier
                for col in old_df.columns:
                    old_value = old_df.loc[old_row_idx, col]
                    new_value = new_row[col]
                    
                    # Si l'ancien champ est vide/nan et le nouveau a une valeur
                    if (pd.isna(old_value) or str(old_value).strip() == '') and \
                       (not pd.isna(new_value) and str(new_value).strip() != ''):
                        old_df.loc[old_row_idx, col] = new_value
                        print(f"Complété {ref} - {col}: '{old_value}' -> '{new_value}'")
        
        # Combiner les DataFrames
        combined_df = pd.concat([old_df, new_rows_to_add], ignore_index=True)
        
    else:
        print("❌ Colonne de référence non trouvée, fusion simple")
        # Fusion simple sans détection de doublons
        combined_df = pd.concat([old_df, new_df], ignore_index=True)
    
    print(f"Fichier combiné final: {len(combined_df)} lignes")
    print("=== FIN FUSION ===")
    
    return combined_df

def clean_and_categorize_payments(df):
    """
    Nettoie et catégorise les méthodes de paiement
    """
    print("🧹 Nettoyage et catégorisation des paiements...")
    
    if 'Gateway' not in df.columns:
        print("⚠️ Colonne 'Gateway' non trouvée")
        return df
    
    # Nettoyer d'abord la colonne Gateway
    df['Gateway'] = df['Gateway'].fillna('').astype(str).str.strip()
    
    def categorize_payment(gateway_value):
        """Catégorise le type de paiement basé sur la valeur Gateway"""
        if pd.isna(gateway_value) or gateway_value == '' or gateway_value == 'nan':
            return 'Autre'
        
        gateway_lower = str(gateway_value).lower().strip()
        
        # Cartes de crédit
        if any(card in gateway_lower for card in ['card', 'carte', 'visa', 'mastercard', 'amex', 'credit']):
            return 'Carte bancaire'
        
        # PayPal et services similaires
        if any(paypal in gateway_lower for paypal in ['paypal', 'pay pal']):
            return 'PayPal'
        
        # Apple Pay
        if any(apple in gateway_lower for apple in ['apple pay', 'applepay']):
            return 'Apple Pay'
        
        # Google Pay
        if any(google in gateway_lower for google in ['google pay', 'googlepay', 'gpay']):
            return 'Google Pay'
        
        # Virement bancaire
        if any(bank in gateway_lower for bank in ['bank', 'virement', 'transfer', 'wire']):
            return 'Virement bancaire'
        
        # Stripe
        if 'stripe' in gateway_lower:
            return 'Carte bancaire'  # Stripe est généralement pour les cartes
        
        # Shopify Payments
        if any(shopify in gateway_lower for shopify in ['shopify payments', 'shopify_payments']):
            return 'Carte bancaire'  # Shopify Payments = cartes principalement
        
        # Défaut
        return 'Autre'
    
    # Appliquer la catégorisation
    df['Mode paiement'] = df['Gateway'].apply(categorize_payment)
    
    # Statistiques de catégorisation
    payment_stats = df['Mode paiement'].value_counts()
    print("📊 Répartition des modes de paiement:")
    for payment_type, count in payment_stats.items():
        print(f"  - {payment_type}: {count}")
    
    return df

def fallback_ttc_ht_tva(df):
    """
    Logique de fallback pour TTC/HT/TVA quand les données sont manquantes
    """
    print("🔄 Application de la logique de fallback TTC/HT/TVA...")
    
    # Colonnes nécessaires
    required_cols = ['Total TTC', 'Total HT', 'Total TVA']
    
    # Créer les colonnes si elles n'existent pas
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0
    
    # Convertir en numérique
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    fallback_count = 0
    
    for idx in df.index:
        ttc = df.loc[idx, 'Total TTC']
        ht = df.loc[idx, 'Total HT'] 
        tva = df.loc[idx, 'Total TVA']
        
        # Si toutes les valeurs sont à 0, essayer d'utiliser d'autres colonnes
        if ttc == 0 and ht == 0 and tva == 0:
            # Chercher dans d'autres colonnes possibles
            fallback_sources = ['Total', 'Amount', 'Net Amount', 'Gross Amount']
            
            for source_col in fallback_sources:
                if source_col in df.columns:
                    source_value = pd.to_numeric(df.loc[idx, source_col], errors='coerce')
                    if not pd.isna(source_value) and source_value != 0:
                        # Assumer que c'est du TTC et calculer HT/TVA avec 20% de TVA
                        df.loc[idx, 'Total TTC'] = source_value
                        df.loc[idx, 'Total HT'] = round(source_value / 1.20, 2)
                        df.loc[idx, 'Total TVA'] = round(source_value - df.loc[idx, 'Total HT'], 2)
                        fallback_count += 1
                        break
        
        # Si on a TTC mais pas HT/TVA
        elif ttc != 0 and (ht == 0 or tva == 0):
            df.loc[idx, 'Total HT'] = round(ttc / 1.20, 2)
            df.loc[idx, 'Total TVA'] = round(ttc - df.loc[idx, 'Total HT'], 2)
            fallback_count += 1
        
        # Si on a HT mais pas TTC/TVA
        elif ht != 0 and (ttc == 0 or tva == 0):
            df.loc[idx, 'Total TVA'] = round(ht * 0.20, 2)
            df.loc[idx, 'Total TTC'] = round(ht + df.loc[idx, 'Total TVA'], 2)
            fallback_count += 1
    
    print(f"✅ Fallback appliqué sur {fallback_count} lignes")
    return df

def process_orders_file(file_path):
    """Traite le fichier des commandes Shopify"""
    print("📋 Traitement du fichier des commandes...")
    
    try:
        df = read_csv_safe(file_path)
        print(f"✅ Fichier des commandes lu: {len(df)} lignes")
        
        # Colonnes essentielles pour les commandes
        required_columns = ['Name', 'Email', 'Financial Status', 'Total', 'Created at']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Colonnes manquantes dans le fichier des commandes: {missing_columns}")
        
        # Nettoyer et standardiser
        if 'Name' in df.columns:
            df['Réf.WEB'] = df['Name'].astype(str)
        
        # Traitement des montants
        for col in ['Total', 'Subtotal', 'Taxes']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Créer les colonnes finales
        if 'Total' in df.columns:
            df['Total TTC'] = df['Total']
            df['Total HT'] = df['Total'] / 1.20  # Approximation 20% TVA
            df['Total TVA'] = df['Total TTC'] - df['Total HT']
        
        print(f"✅ Fichier des commandes traité: {len(df)} lignes")
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement du fichier des commandes: {e}")
        raise

def process_transactions_file(file_path):
    """Traite le fichier des transactions de paiement"""
    print("💳 Traitement du fichier des transactions...")
    
    try:
        df = read_csv_safe(file_path)
        print(f"✅ Fichier des transactions lu: {len(df)} lignes")
        
        # Colonnes essentielles pour les transactions
        required_columns = ['Order', 'Type', 'Gateway', 'Amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Colonnes manquantes dans le fichier des transactions: {missing_columns}")
        
        # Filtrer seulement les transactions de type "sale" ou "charge"
        if 'Type' in df.columns:
            before_filter = len(df)
            df = df[df['Type'].isin(['sale', 'charge', 'Sale', 'Charge'])].copy()
            print(f"🔍 Filtrage par type: {before_filter} -> {len(df)} transactions")
        
        # Nettoyer et catégoriser les paiements
        df = clean_and_categorize_payments(df)
        
        # Standardiser les références
        if 'Order' in df.columns:
            df['Réf.WEB'] = df['Order'].astype(str)
        
        print(f"✅ Fichier des transactions traité: {len(df)} lignes")
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement du fichier des transactions: {e}")
        raise

def process_journal_file(file_path):
    """Traite le fichier journal comptable"""
    print("📊 Traitement du fichier journal...")
    
    try:
        df = read_csv_safe(file_path)
        print(f"✅ Fichier journal lu: {len(df)} lignes")
        
        # Colonnes essentielles pour le journal
        expected_columns = ['Piece', 'TTC', 'HT', 'TVA']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Colonnes manquantes dans le fichier journal: {missing_columns}")
        
        # Standardiser les colonnes
        column_mapping = {
            'Piece': 'Réf.WEB',
            'TTC': 'Total TTC',
            'HT': 'Total HT', 
            'TVA': 'Total TVA'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = pd.to_numeric(df[old_col], errors='coerce').fillna(0)
        
        # Appliquer la logique de fallback
        df = fallback_ttc_ht_tva(df)
        
        print(f"✅ Fichier journal traité: {len(df)} lignes")
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement du fichier journal: {e}")
        raise

def merge_dataframes(orders_df, transactions_df, journal_df):
    """Fusionne les trois DataFrames sur la référence web"""
    print("🔗 Fusion des données...")
    
    # Préparer la fusion sur la référence web
    merge_key = 'Réf.WEB'
    
    # S'assurer que la clé existe dans tous les DataFrames
    for df_name, df in [('commandes', orders_df), ('transactions', transactions_df), ('journal', journal_df)]:
        if merge_key not in df.columns:
            print(f"⚠️ Clé de fusion manquante dans {df_name}")
        else:
            print(f"✅ {df_name}: {len(df[merge_key].unique())} références uniques")
    
    # Fusion progressive
    # Étape 1: Fusionner commandes et transactions
    if merge_key in orders_df.columns and merge_key in transactions_df.columns:
        merged_df = pd.merge(orders_df, transactions_df, on=merge_key, how='outer', suffixes=('_orders', '_trans'))
        print(f"✅ Fusion commandes + transactions: {len(merged_df)} lignes")
    else:
        merged_df = orders_df.copy()
        print("⚠️ Fusion commandes + transactions impossible, utilisation des commandes uniquement")
    
    # Étape 2: Fusionner avec le journal
    if merge_key in journal_df.columns:
        final_df = pd.merge(merged_df, journal_df, on=merge_key, how='outer', suffixes=('', '_journal'))
        print(f"✅ Fusion finale avec journal: {len(final_df)} lignes")
    else:
        final_df = merged_df.copy()
        print("⚠️ Fusion avec journal impossible, données sans journal")
    
    # Nettoyage final: résoudre les colonnes dupliquées
    final_columns = []
    processed_base_names = set()
    
    for col in final_df.columns:
        # Extraire le nom de base (sans suffixe)
        base_name = col.replace('_orders', '').replace('_trans', '').replace('_journal', '')
        
        if base_name not in processed_base_names:
            # Colonnes prioritaires selon l'ordre: journal > transactions > commandes
            priority_cols = [
                base_name,
                f"{base_name}_journal", 
                f"{base_name}_trans",
                f"{base_name}_orders"
            ]
            
            # Trouver la première colonne qui existe
            for priority_col in priority_cols:
                if priority_col in final_df.columns:
                    # Renommer vers le nom de base si ce n'est pas déjà fait
                    if priority_col != base_name:
                        final_df[base_name] = final_df[priority_col]
                    final_columns.append(base_name)
                    processed_base_names.add(base_name)
                    break
    
    # Garder seulement les colonnes nettoyées
    final_df = final_df[final_columns]
    
    # Appliquer la logique de fallback finale
    final_df = fallback_ttc_ht_tva(final_df)
    
    print(f"✅ Fusion terminée: {len(final_df)} lignes, {len(final_df.columns)} colonnes")
    return final_df

def generate_filename():
    """Génère le nom de fichier standardisé"""
    today = datetime.now()
    day = today.strftime("%d")
    month = today.strftime("%m") 
    year = today.strftime("%Y")
    
    filename = f"Compta_LCDI_Shopify_{day}_{month}_{year}.xlsx"
    return filename

def save_to_excel(df, filename):
    """Sauvegarde le DataFrame au format Excel avec formatage"""
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        print(f"💾 Sauvegarde en cours: {filename}")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Données consolidées', index=False)
            
            # Récupérer la feuille pour le formatage
            worksheet = writer.sheets['Données consolidées']
            
            # Formatage des en-têtes
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
                cell.fill = cell.fill.copy(fgColor="366092")
            
            # Ajustement automatique des largeurs de colonnes
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✅ Fichier sauvegardé: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        raise

def open_browser():
    """Ouvre le navigateur après un délai"""
    time.sleep(2)  # Attendre que le serveur soit prêt
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Navigateur ouvert automatiquement")
    except:
        print("⚠️ Impossible d'ouvrir le navigateur automatiquement")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    try:
        # Vérifier le mode de traitement
        processing_mode = request.form.get('processing_mode', 'new')
        print(f"🔄 Mode de traitement: {processing_mode}")
        
        # Vérifier que tous les fichiers requis sont présents
        required_files = ['orders_file', 'transactions_file', 'journal_file']
        uploaded_files = {}
        
        for file_key in required_files:
            if file_key not in request.files:
                flash(f'Fichier manquant: {file_key}', 'error')
                return redirect(url_for('index'))
            
            file = request.files[file_key]
            if file.filename == '':
                flash(f'Aucun fichier sélectionné pour: {file_key}', 'error')
                return redirect(url_for('index'))
            
            if not allowed_file(file.filename):
                flash(f'Type de fichier non autorisé: {file.filename}', 'error')
                return redirect(url_for('index'))
            
            uploaded_files[file_key] = file
        
        # Traitement du fichier ancien pour le mode combine
        old_df = None
        if processing_mode == 'combine':
            if 'old_file' not in request.files:
                flash('Fichier ancien manquant pour le mode combinaison', 'error')
                return redirect(url_for('index'))
            
            old_file = request.files['old_file']
            if old_file.filename == '':
                flash('Aucun fichier ancien sélectionné', 'error')
                return redirect(url_for('index'))
            
            # Sauvegarder et lire l'ancien fichier
            old_filename = secure_filename(old_file.filename)
            old_path = os.path.join(UPLOAD_FOLDER, f"old_{old_filename}")
            old_file.save(old_path)
            
            try:
                if old_filename.endswith('.xlsx'):
                    old_df = pd.read_excel(old_path)
                else:
                    old_df = read_csv_safe(old_path)
                print(f"✅ Ancien fichier lu: {len(old_df)} lignes")
            except Exception as e:
                flash(f'Erreur lors de la lecture de l\'ancien fichier: {str(e)}', 'error')
                return redirect(url_for('index'))
            finally:
                if os.path.exists(old_path):
                    os.remove(old_path)
        
        # Sauvegarder les fichiers uploadés
        file_paths = {}
        for file_key, file in uploaded_files.items():
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            file_paths[file_key] = file_path
        
        # Traitement des fichiers
        print("🚀 Début du traitement des fichiers...")
        
        # Traiter chaque fichier
        orders_df = process_orders_file(file_paths['orders_file'])
        transactions_df = process_transactions_file(file_paths['transactions_file'])
        journal_df = process_journal_file(file_paths['journal_file'])
        
        # Fusionner les données
        merged_df = merge_dataframes(orders_df, transactions_df, journal_df)
        
        # Mode combinaison: fusionner avec l'ancien fichier
        if processing_mode == 'combine' and old_df is not None:
            print("🔄 Application du mode combinaison...")
            final_df = combine_with_old_file(old_df, merged_df)
            flash_message = f'Fichier combiné généré avec succès! {len(final_df)} lignes au total.'
        else:
            final_df = merged_df
            flash_message = f'Nouveau fichier généré avec succès! {len(final_df)} lignes traitées.'
        
        # Génération du fichier final
        filename = generate_filename()
        output_path = save_to_excel(final_df, filename)
        
        # Nettoyer les fichiers temporaires
        for file_path in file_paths.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print("✅ Traitement terminé avec succès!")
        
        # Message de succès et redirection
        flash(flash_message, 'success')
        return render_template('success.html', 
                             filename=filename, 
                             download_url=url_for('download_file', filename=filename),
                             processing_mode=processing_mode)
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {str(e)}")
        flash(f'Erreur lors du traitement des fichiers: {str(e)}', 'error')
        
        # Nettoyer les fichiers en cas d'erreur
        for file_path in file_paths.values() if 'file_paths' in locals() else []:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Télécharge le fichier généré"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            flash('Fichier non trouvé.', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {str(e)}")
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print("=== DÉMARRAGE DE L'APPLICATION LCDI ===")
    print("Application de génération de tableau de facturation LCDI")
    print(f"Port: {port}")
    print(f"Mode debug: {debug_mode}")
    print("=======================================")
    
    # Ouvrir le navigateur automatiquement (seulement si pas en mode debug)
    if not debug_mode:
        threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(debug=debug_mode, host='127.0.0.1', port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Application fermée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        input("Appuyez sur Entrée pour fermer...")
