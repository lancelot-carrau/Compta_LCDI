                    # Traitement du match
                    for match in matches:
                        if len(match.groups()) > 1:
                            # Pattern avec groupes multiples
                            value = match.groups()[-1]  # Prendre le dernier groupe par défaut
                        else:
                            # Pattern simple
                            value = match.group(1) if match.groups() else match.group(0)
                        
                        if debug_mode:
                            debug_info.append(f"Pattern '{key}' trouvé: {value}")
                        
                        if key == 'order_id':
                            invoice_data['id_amazon'] = value
                        elif key == 'invoice_number':
                            invoice_data['facture_amazon'] = value
                        elif key == 'date':
                            parsed_date = parse_date_string(value)
                            if parsed_date:
                                dates_found.append(parsed_date)
                                if not invoice_data['date_facture']:  # Prendre la première date trouvée
                                    invoice_data['date_facture'] = parsed_date
                        elif key == 'country':
                            # Pour les patterns avec deux groupes (code postal + pays)
                            if len(match.groups()) == 2:
                                # Prendre le deuxième groupe (le code pays)
                                country_code = match.groups()[1].upper()
                                # Ce pattern est prioritaire car il inclut le contexte d'adresse
                                priority = 1
                                if debug_mode:
                                    debug_info.append(f"Pattern country avec 2 groupes (priorité {priority}): {match.groups()}, code pays: {country_code}")
                            else:
                                # Pattern simple - déterminer la priorité selon le pattern utilisé
                                country_code = value.upper()
                                # Vérifier si c'est un pattern avec contexte d'adresse
                                pattern_used = pattern
                                if any(addr_keyword in pattern_used for addr_keyword in ['Ship', 'Livraison', 'Spedire', 'Address', 'Indirizzo', 'Facturation', 'Bill']):
                                    priority = 1  # Pattern avec contexte d'adresse
                                elif r'\n\s*' in pattern_used or r'\s*$' in pattern_used:
                                    priority = 2  # Pattern en fin de ligne
                                else:
                                    priority = 3  # Pattern générique
                                
                                if debug_mode:
                                    debug_info.append(f"Pattern country simple (priorité {priority}): {value}, code pays: {country_code}")
                            
                            # Valider que c'est un vrai code pays (2 lettres majuscules)
                            if len(country_code) == 2 and country_code.isalpha():
                                # Logique de priorité : remplacer si on a un pattern plus prioritaire
                                current_priority = invoice_data.get('_country_priority', 99)
                                if not invoice_data['pays'] or priority < current_priority:
                                    invoice_data['pays'] = country_code
                                    invoice_data['_country_priority'] = priority
                                    if debug_mode:
                                        debug_info.append(f"Code pays défini avec priorité {priority}: {country_code}")
                                elif debug_mode:
                                    debug_info.append(f"Code pays ignoré (priorité {priority} >= {current_priority}): {country_code} (actuel: {invoice_data['pays']})")
                        elif key == 'customer_name':
                            name = re.sub(r'[0-9\n\r]+', ' ', value).strip()
                            if len(name) > 3:
                                invoice_data['nom_contact'] = name[:50]
                        elif key == 'total_amount':
                            try:
                                # Remplacer les virgules par des points et nettoyer
                                clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                invoice_data['total'] = float(clean_value)
                            except ValueError:
                                pass
                        elif key == 'tax_amount':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) == 3:
                                    # Pattern: (\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€
                                    # Groupe 3 = montant TVA
                                    clean_value = match.groups()[2].replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['tva'] = float(clean_value)
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['tva'] = float(clean_value)
                            except ValueError:
                                pass
                        elif key == 'tax_rate':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) >= 1:
                                    # Prendre le premier groupe (le taux)
                                    clean_value = match.groups()[0].replace(',', '.').replace(' ', '')
                                    rate_float = float(clean_value)
                                    invoice_data['taux_tva'] = f"{rate_float:.2f}%"
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '')
                                    rate_float = float(clean_value)
                                    invoice_data['taux_tva'] = f"{rate_float:.2f}%"
                            except ValueError:
                                pass
                        elif key == 'subtotal':
                            try:
                                # Pour les patterns avec plusieurs groupes (factures italiennes)
                                if len(match.groups()) == 3:
                                    # Pattern: (\d+)%\s+([\d,]+)\s*€\s+([\d,]+)\s*€
                                    # Groupe 2 = montant HT
                                    clean_value = match.groups()[1].replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['ht'] = float(clean_value)
                                else:
                                    # Pattern simple
                                    clean_value = value.replace(',', '.').replace(' ', '').replace('\u00a0', '')
                                    invoice_data['ht'] = float(clean_value)
                            except ValueError:
                                pass
