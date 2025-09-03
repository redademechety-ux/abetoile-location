import os
import base64
from datetime import datetime, timezone
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.colors import HexColor
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv

load_dotenv()

class PDFInvoiceGenerator:
    def __init__(self):
        self.emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        
    async def generate_invoice_pdf(self, invoice_data, client_data, company_settings, items_details):
        """Generate a professional PDF invoice using AI for content and reportlab for formatting"""
        
        # Generate invoice content using AI
        invoice_content = await self._generate_invoice_content(
            invoice_data, client_data, company_settings, items_details
        )
        
        # Create PDF using reportlab
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Prepare content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=HexColor('#2563eb')
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor('#374151')
        )
        
        # Title
        story.append(Paragraph("FACTURE", title_style))
        story.append(Spacer(1, 20))
        
        # Company and client info
        company_info = f"""
        <b>{company_settings.get('company_name', 'AutoPro Rental')}</b><br/>
        {company_settings.get('company_address', '')}<br/>
        Tél: {company_settings.get('company_phone', '')}<br/>
        Email: {company_settings.get('company_email', '')}
        """
        
        client_info = f"""
        <b>FACTURÉ À:</b><br/>
        {client_data.get('company_name', '')}<br/>
        {client_data.get('contact_name', '')}<br/>
        {client_data.get('address', '')}<br/>
        {client_data.get('postal_code', '')} {client_data.get('city', '')}<br/>
        N° TVA: {client_data.get('vat_number', 'N/A')}
        """
        
        # Create table for company and client info
        info_table = Table([
            [Paragraph(company_info, styles['Normal']), 
             Paragraph(client_info, styles['Normal'])]
        ], colWidths=[8*cm, 8*cm])
        
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Invoice details
        invoice_details = f"""
        <b>Facture N°:</b> {invoice_data.get('invoice_number', '')}<br/>
        <b>Date de facture:</b> {datetime.fromisoformat(invoice_data.get('invoice_date', '')).strftime('%d/%m/%Y') if invoice_data.get('invoice_date') else ''}<br/>
        <b>Date d'échéance:</b> {datetime.fromisoformat(invoice_data.get('due_date', '')).strftime('%d/%m/%Y') if invoice_data.get('due_date') else ''}
        """
        
        story.append(Paragraph(invoice_details, header_style))
        story.append(Spacer(1, 20))
        
        # Items table
        table_data = [['Description', 'Quantité', 'Prix unitaire', 'Total HT']]
        
        for item in items_details:
            vehicle_name = f"{item.get('vehicle_brand', '')} {item.get('vehicle_model', '')} - {item.get('license_plate', '')}"
            if item.get('is_renewable'):
                vehicle_name += f" (Location reconductible - {item.get('rental_duration', '')} {item.get('rental_period', '')})"
            
            table_data.append([
                vehicle_name,
                str(item.get('quantity', 1)),
                f"{item.get('daily_rate', 0):.2f} €",
                f"{item.get('daily_rate', 0) * item.get('quantity', 1):.2f} €"
            ])
        
        # Add totals
        table_data.extend([
            ['', '', 'Total HT:', f"{invoice_data.get('total_ht', 0):.2f} €"],
            ['', '', f"TVA ({client_data.get('vat_rate', 20)}%):", f"{invoice_data.get('total_vat', 0):.2f} €"],
            ['', '', 'Total TTC:', f"{invoice_data.get('total_ttc', 0):.2f} €"]
        ])
        
        # Create items table
        items_table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right align numbers
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, HexColor('#f9fafb')]),
            
            # Total rows
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -3), (-1, -1), 10),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#dbeafe')),
            ('TEXTCOLOR', (0, -1), (-1, -1), HexColor('#1e40af')),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor('#374151')),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 30))
        
        # Payment terms using AI-generated content
        payment_terms = await self._generate_payment_terms(invoice_data, client_data)
        story.append(Paragraph("<b>Conditions de paiement:</b>", header_style))
        story.append(Paragraph(payment_terms, styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 40))
        footer_text = f"""
        <i>Merci pour votre confiance.</i><br/>
        {company_settings.get('company_name', 'AutoPro Rental')} - Spécialiste en location de véhicules
        """
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Return base64 encoded PDF
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(pdf_data).decode('utf-8')
    
    async def _generate_invoice_content(self, invoice_data, client_data, company_settings, items_details):
        """Use AI to generate personalized invoice content"""
        try:
            chat = LlmChat(
                api_key=self.emergent_key,
                session_id=f"invoice_{invoice_data.get('id', 'default')}",
                system_message="Vous êtes un expert comptable français spécialisé dans la location de véhicules. Générez du contenu professionnel pour les factures."
            ).with_model("openai", "gpt-4o-mini")
            
            prompt = f"""
            Générez un contenu professionnel pour une facture de location de véhicules avec ces informations:
            
            Client: {client_data.get('company_name', '')}
            Véhicules loués: {len(items_details)} véhicule(s)
            Montant total: {invoice_data.get('total_ttc', 0):.2f} €
            
            Générez uniquement un texte de remerciement professionnel en français (2-3 lignes maximum).
            """
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            return response.strip() if response else "Merci pour votre confiance."
            
        except Exception as e:
            print(f"Erreur génération contenu AI: {e}")
            return "Merci pour votre confiance."
    
    async def _generate_payment_terms(self, invoice_data, client_data):
        """Generate payment terms using AI"""
        try:
            chat = LlmChat(
                api_key=self.emergent_key,
                session_id=f"payment_terms_{invoice_data.get('id', 'default')}",
                system_message="Vous êtes un expert comptable français. Générez des conditions de paiement professionnelles."
            ).with_model("openai", "gpt-4o-mini")
            
            due_date = datetime.fromisoformat(invoice_data.get('due_date', ''))
            days_to_pay = (due_date - datetime.now(timezone.utc)).days
            
            prompt = f"""
            Générez des conditions de paiement professionnelles en français pour:
            - Échéance dans {days_to_pay} jours
            - Montant: {invoice_data.get('total_ttc', 0):.2f} €
            
            Incluez: délai de paiement, modalités, pénalités de retard selon la loi française.
            Maximum 4 lignes.
            """
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            return response.strip() if response else f"Paiement à {days_to_pay} jours. En cas de retard, pénalités selon la loi française."
            
        except Exception as e:
            print(f"Erreur génération conditions AI: {e}")
            return "Paiement à 30 jours. En cas de retard, pénalités de 3 fois le taux légal."