from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
import requests
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class MailgunService:
    def __init__(self):
        self.api_key = os.environ.get('MAILGUN_API_KEY')
        self.domain = os.environ.get('MAILGUN_DOMAIN', 'sandbox-123.mailgun.org')
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
        self.default_sender = os.environ.get('MAILGUN_DEFAULT_SENDER', f'noreply@{self.domain}')
        self.timeout = 30
        self.max_retries = 3
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            self.logger.warning("MAILGUN_API_KEY not configured - email functionality will be disabled")
    
    async def send_email(self, email_request: EmailRequest) -> Dict[str, Any]:
        """Send email through Mailgun API with comprehensive error handling"""
        if not self.api_key:
            self.logger.warning("Email not sent - Mailgun not configured")
            return {
                'success': False,
                'message': 'Email service not configured'
            }
        
        try:
            # Prepare email data
            email_data = self._prepare_email_data(email_request)
            
            # Send email with retry logic
            response = await self._send_with_retry(email_data)
            
            # Log successful send
            self.logger.info(f"Email sent successfully to {email_request.to}", extra={
                'recipient': email_request.to,
                'subject': email_request.subject,
                'mailgun_id': response.get('id')
            })
            
            return {
                'success': True,
                'message_id': response.get('id'),
                'message': response.get('message')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {email_request.to}: {str(e)}", extra={
                'recipient': email_request.to,
                'subject': email_request.subject,
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_email_data(self, email_request: EmailRequest) -> Dict[str, Any]:
        """Prepare email data for Mailgun API"""
        data = {
            'from': self.default_sender,
            'to': email_request.to,
            'subject': email_request.subject
        }
        
        if email_request.text_content:
            data['text'] = email_request.text_content
        
        if email_request.html_content:
            data['html'] = email_request.html_content
            
        if email_request.tags:
            data['o:tag'] = email_request.tags
            
        # Add tracking options for analytics
        data.update({
            'o:tracking': 'yes',
            'o:tracking-clicks': 'yes',
            'o:tracking-opens': 'yes'
        })
        
        return data
    
    async def _send_with_retry(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email with automatic retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/messages",
                    auth=("api", self.api_key),
                    data=email_data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise e
                
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.warning(f"Email send attempt {attempt + 1} failed, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                
        raise Exception("Max retries exceeded")

    async def send_invoice_email(self, client_email: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send invoice notification email"""
        subject = f"Facture {invoice_data.get('invoice_number', 'N/A')} - Abetoile Location"
        
        # HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px;">
                <h2 style="color: #2c3e50;">Abetoile Location</h2>
                <h3>Nouvelle facture disponible</h3>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p>Bonjour {invoice_data.get('client_name', '')},</p>
                    
                    <p>Une nouvelle facture est disponible pour votre compte :</p>
                    
                    <ul>
                        <li><strong>Numéro de facture :</strong> {invoice_data.get('invoice_number', 'N/A')}</li>
                        <li><strong>Date :</strong> {invoice_data.get('invoice_date', 'N/A')}</li>
                        <li><strong>Montant TTC :</strong> {invoice_data.get('total_ttc', 0):.2f} €</li>
                        <li><strong>Date d'échéance :</strong> {invoice_data.get('due_date', 'N/A')}</li>
                    </ul>
                    
                    <p>Vous pouvez télécharger votre facture depuis votre espace client.</p>
                    
                    <p>Cordialement,<br>L'équipe Abetoile Location</p>
                </div>
                
                <div style="font-size: 12px; color: #666; margin-top: 20px;">
                    <p>Cet email a été envoyé automatiquement. Merci de ne pas répondre directement à ce message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content
        text_content = f"""
        Abetoile Location - Nouvelle facture disponible
        
        Bonjour {invoice_data.get('client_name', '')},
        
        Une nouvelle facture est disponible pour votre compte :
        
        - Numéro de facture : {invoice_data.get('invoice_number', 'N/A')}
        - Date : {invoice_data.get('invoice_date', 'N/A')}
        - Montant TTC : {invoice_data.get('total_ttc', 0):.2f} €
        - Date d'échéance : {invoice_data.get('due_date', 'N/A')}
        
        Vous pouvez télécharger votre facture depuis votre espace client.
        
        Cordialement,
        L'équipe Abetoile Location
        
        ---
        Cet email a été envoyé automatiquement. Merci de ne pas répondre directement à ce message.
        """
        
        email_request = EmailRequest(
            to=client_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=['invoice', 'notification']
        )
        
        return await self.send_email(email_request)

    async def send_payment_reminder(self, client_email: str, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send payment reminder email"""
        urgency = reminder_data.get('urgency_level', 'standard')
        
        if urgency == 'urgent':
            subject = f"URGENT - Facture impayée {reminder_data.get('invoice_number', 'N/A')} - Abetoile Location"
        else:
            subject = f"Rappel de paiement - Facture {reminder_data.get('invoice_number', 'N/A')} - Abetoile Location"
        
        # HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #{'#fff3cd' if urgency == 'urgent' else '#f8f9fa'}; padding: 20px;">
                <h2 style="color: #2c3e50;">Abetoile Location</h2>
                <h3 style="color: #{'#856404' if urgency == 'urgent' else '#495057'};">
                    {'Rappel urgent de paiement' if urgency == 'urgent' else 'Rappel de paiement'}
                </h3>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #{'#ffc107' if urgency == 'urgent' else '#007bff'};">
                    <p>Bonjour {reminder_data.get('client_name', '')},</p>
                    
                    <p>Nous vous rappelons qu'une facture est en attente de paiement :</p>
                    
                    <ul>
                        <li><strong>Numéro de facture :</strong> {reminder_data.get('invoice_number', 'N/A')}</li>
                        <li><strong>Montant dû :</strong> {reminder_data.get('amount_due', 0):.2f} €</li>
                        <li><strong>Date d'échéance :</strong> {reminder_data.get('due_date', 'N/A')}</li>
                        <li><strong>Jours de retard :</strong> {reminder_data.get('days_overdue', 0)}</li>
                    </ul>
                    
                    <p>Merci de procéder au règlement dans les plus brefs délais pour éviter des frais supplémentaires.</p>
                    
                    <p>Cordialement,<br>L'équipe Abetoile Location</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        email_request = EmailRequest(
            to=client_email,
            subject=subject,
            html_content=html_content,
            tags=['payment-reminder', urgency]
        )
        
        return await self.send_email(email_request)


# Instance globale du service
mailgun_service = MailgunService()