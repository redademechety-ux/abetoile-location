from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
import uuid
import csv
import io
import json

class AccountingEntryType(str, Enum):
    SALE = "sale"
    VAT_COLLECTED = "vat_collected"
    CLIENT_RECEIVABLE = "client_receivable"

class AccountingEntry(BaseModel):
    id: str = None
    entry_date: datetime
    invoice_id: str
    client_id: str
    account_code: str
    account_name: str
    debit: float = 0.0
    credit: float = 0.0
    description: str
    reference: str  # Invoice number
    entry_type: AccountingEntryType
    
    def __init__(self, **data):
        if data.get('id') is None:
            data['id'] = str(uuid.uuid4())
        super().__init__(**data)

class FrenchAccounting:
    """Système comptable français conforme au Plan Comptable Général (PCG)"""
    
    # Comptes du Plan Comptable Général français
    ACCOUNT_CODES = {
        'client_receivables': '411000',  # Clients
        'sales_services': '706000',      # Prestations de services
        'vat_collected_standard': '445571',  # TVA collectée 20%
        'vat_collected_reduced': '445572',   # TVA collectée 10%
        'vat_collected_super_reduced': '445573',  # TVA collectée 5.5%
        'bank': '512000',                # Banque
        'cash': '530000',               # Caisse
        'discount_granted': '709000',   # Remises accordées
    }
    
    def __init__(self):
        self.entries: List[AccountingEntry] = []
    
    def generate_invoice_entries(
        self, 
        invoice_data: Dict[str, Any], 
        client_data: Dict[str, Any],
        items_data: List[Dict[str, Any]],
        settings: Dict[str, Any]
    ) -> List[AccountingEntry]:
        """Génère les écritures comptables pour une facture selon les normes françaises"""
        
        entries = []
        invoice_date = datetime.fromisoformat(invoice_data['invoice_date'])
        invoice_number = invoice_data['invoice_number']
        client_name = client_data['company_name']
        
        # 1. Écriture de débit client (411000 - Clients)
        client_entry = AccountingEntry(
            entry_date=invoice_date,
            invoice_id=invoice_data['id'],
            client_id=invoice_data['client_id'],
            account_code=self.ACCOUNT_CODES['client_receivables'],
            account_name=f"Client - {client_name}",
            debit=invoice_data['total_ttc'],
            credit=0.0,
            description=f"Facture {invoice_number} - Location véhicules",
            reference=invoice_number,
            entry_type=AccountingEntryType.CLIENT_RECEIVABLE
        )
        entries.append(client_entry)
        
        # 2. Écriture de crédit ventes (706000 - Prestations de services)
        sales_entry = AccountingEntry(
            entry_date=invoice_date,
            invoice_id=invoice_data['id'],
            client_id=invoice_data['client_id'],
            account_code=settings.get('accounting_accounts', {}).get('sales', self.ACCOUNT_CODES['sales_services']),
            account_name="Prestations de services - Location véhicules",
            debit=0.0,
            credit=invoice_data['total_ht'],
            description=f"Facture {invoice_number} - Vente HT",
            reference=invoice_number,
            entry_type=AccountingEntryType.SALE
        )
        entries.append(sales_entry)
        
        # 3. Écriture de crédit TVA collectée
        if invoice_data['total_vat'] > 0:
            vat_rate = client_data.get('vat_rate', 20.0)
            vat_account_code = self._get_vat_account_code(vat_rate, settings)
            
            vat_entry = AccountingEntry(
                entry_date=invoice_date,
                invoice_id=invoice_data['id'],
                client_id=invoice_data['client_id'],
                account_code=vat_account_code,
                account_name=f"TVA collectée {vat_rate}%",
                debit=0.0,
                credit=invoice_data['total_vat'],
                description=f"Facture {invoice_number} - TVA {vat_rate}%",
                reference=invoice_number,
                entry_type=AccountingEntryType.VAT_COLLECTED
            )
            entries.append(vat_entry)
        
        self.entries.extend(entries)
        return entries
    
    def generate_payment_entries(
        self,
        invoice_data: Dict[str, Any],
        client_data: Dict[str, Any],
        payment_date: datetime,
        payment_method: str = "bank"
    ) -> List[AccountingEntry]:
        """Génère les écritures de règlement d'une facture"""
        
        entries = []
        invoice_number = invoice_data['invoice_number']
        client_name = client_data['company_name']
        
        # Débit du compte de trésorerie (banque ou caisse)
        treasury_account = self.ACCOUNT_CODES['bank'] if payment_method == 'bank' else self.ACCOUNT_CODES['cash']
        treasury_name = "Banque" if payment_method == 'bank' else "Caisse"
        
        treasury_entry = AccountingEntry(
            entry_date=payment_date,
            invoice_id=invoice_data['id'],
            client_id=invoice_data['client_id'],
            account_code=treasury_account,
            account_name=treasury_name,
            debit=invoice_data['total_ttc'],
            credit=0.0,
            description=f"Règlement facture {invoice_number} - {client_name}",
            reference=invoice_number,
            entry_type=AccountingEntryType.CLIENT_RECEIVABLE
        )
        entries.append(treasury_entry)
        
        # Crédit du compte client
        client_entry = AccountingEntry(
            entry_date=payment_date,
            invoice_id=invoice_data['id'],
            client_id=invoice_data['client_id'],
            account_code=self.ACCOUNT_CODES['client_receivables'],
            account_name=f"Client - {client_name}",
            debit=0.0,
            credit=invoice_data['total_ttc'],
            description=f"Règlement facture {invoice_number}",
            reference=invoice_number,
            entry_type=AccountingEntryType.CLIENT_RECEIVABLE
        )
        entries.append(client_entry)
        
        self.entries.extend(entries)
        return entries
    
    def _get_vat_account_code(self, vat_rate: float, settings: Dict[str, Any]) -> str:
        """Retourne le code comptable TVA approprié selon le taux"""
        if vat_rate == 20.0:
            return settings.get('accounting_accounts', {}).get('vat_standard', self.ACCOUNT_CODES['vat_collected_standard'])
        elif vat_rate == 10.0:
            return settings.get('accounting_accounts', {}).get('vat_reduced', self.ACCOUNT_CODES['vat_collected_reduced'])
        elif vat_rate == 5.5:
            return self.ACCOUNT_CODES['vat_collected_super_reduced']
        else:
            return self.ACCOUNT_CODES['vat_collected_standard']
    
    def export_to_csv(self, entries: Optional[List[AccountingEntry]] = None) -> str:
        """Exporte les écritures au format CSV pour logiciels comptables"""
        if entries is None:
            entries = self.entries
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # En-têtes CSV standards pour logiciels comptables français
        headers = [
            'Date',
            'Compte',
            'Libellé compte',
            'Référence',
            'Libellé écriture',
            'Débit',
            'Crédit',
            'Montant',
            'Sens'
        ]
        writer.writerow(headers)
        
        for entry in entries:
            amount = entry.debit if entry.debit > 0 else entry.credit
            sens = 'D' if entry.debit > 0 else 'C'
            
            row = [
                entry.entry_date.strftime('%d/%m/%Y'),
                entry.account_code,
                entry.account_name,
                entry.reference,
                entry.description,
                f"{entry.debit:.2f}".replace('.', ',') if entry.debit > 0 else "0,00",
                f"{entry.credit:.2f}".replace('.', ',') if entry.credit > 0 else "0,00",
                f"{amount:.2f}".replace('.', ','),
                sens
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_ciel(self, entries: Optional[List[AccountingEntry]] = None) -> str:
        """Export spécifique pour CIEL Compta"""
        if entries is None:
            entries = self.entries
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')
        
        # Format CIEL
        headers = ['Date', 'Journal', 'Compte', 'Libellé', 'Débit', 'Crédit', 'Numéro pièce']
        writer.writerow(headers)
        
        for entry in entries:
            row = [
                entry.entry_date.strftime('%d%m%Y'),
                'VTE',  # Journal des ventes
                entry.account_code,
                entry.description[:30],  # CIEL limite à 30 caractères
                f"{entry.debit:.2f}".replace('.', ',') if entry.debit > 0 else "",
                f"{entry.credit:.2f}".replace('.', ',') if entry.credit > 0 else "",
                entry.reference
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_sage(self, entries: Optional[List[AccountingEntry]] = None) -> str:
        """Export spécifique pour SAGE"""
        if entries is None:
            entries = self.entries
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Format SAGE
        headers = [
            'Date_comptable', 'Compte_general', 'Compte_tiers', 'Libelle', 
            'Sens', 'Montant', 'Reference', 'Date_echeance'
        ]
        writer.writerow(headers)
        
        for entry in entries:
            sens = '1' if entry.debit > 0 else '2'  # SAGE utilise 1 pour débit, 2 pour crédit
            amount = entry.debit if entry.debit > 0 else entry.credit
            
            row = [
                entry.entry_date.strftime('%d/%m/%Y'),
                entry.account_code,
                entry.client_id if entry.account_code.startswith('411') else "",
                entry.description,
                sens,
                f"{amount:.2f}".replace('.', ','),
                entry.reference,
                entry.entry_date.strftime('%d/%m/%Y')  # Même date par défaut
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_cegid(self, entries: Optional[List[AccountingEntry]] = None) -> str:
        """Export spécifique pour CEGID"""
        if entries is None:
            entries = self.entries
        
        # CEGID utilise souvent du XML ou du format spécifique
        # Ici on fait un CSV adapté
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        headers = [
            'Date', 'Code_journal', 'Numero_compte', 'Libelle_compte',
            'Libelle_ecriture', 'Montant_debit', 'Montant_credit', 'Numero_piece'
        ]
        writer.writerow(headers)
        
        for entry in entries:
            row = [
                entry.entry_date.strftime('%d/%m/%Y'),
                'VEN',  # Code journal ventes
                entry.account_code,
                entry.account_name,
                entry.description,
                f"{entry.debit:.2f}".replace('.', ',') if entry.debit > 0 else "0,00",
                f"{entry.credit:.2f}".replace('.', ',') if entry.credit > 0 else "0,00",
                entry.reference
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def get_journal_entries_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Génère un résumé des écritures pour une période"""
        period_entries = [
            entry for entry in self.entries 
            if start_date <= entry.entry_date <= end_date
        ]
        
        total_debit = sum(entry.debit for entry in period_entries)
        total_credit = sum(entry.credit for entry in period_entries)
        
        # Groupement par compte
        accounts_summary = {}
        for entry in period_entries:
            if entry.account_code not in accounts_summary:
                accounts_summary[entry.account_code] = {
                    'account_name': entry.account_name,
                    'total_debit': 0,
                    'total_credit': 0,
                    'balance': 0,
                    'entries_count': 0
                }
            
            accounts_summary[entry.account_code]['total_debit'] += entry.debit
            accounts_summary[entry.account_code]['total_credit'] += entry.credit
            accounts_summary[entry.account_code]['balance'] = (
                accounts_summary[entry.account_code]['total_debit'] - 
                accounts_summary[entry.account_code]['total_credit']
            )
            accounts_summary[entry.account_code]['entries_count'] += 1
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_entries': len(period_entries),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'is_balanced': abs(total_debit - total_credit) < 0.01
            },
            'accounts': accounts_summary
        }