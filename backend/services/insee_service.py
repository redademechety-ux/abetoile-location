import requests
import os
import re
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum

class BusinessStatus(str, Enum):
    ACTIVE = "A"
    CEASED = "C"

class CompanyInfo(BaseModel):
    siren: str = Field(..., regex=r"^\d{9}$")
    siret: Optional[str] = Field(None, regex=r"^\d{14}$")
    denomination: Optional[str] = None
    legal_form: Optional[str] = None
    legal_form_code: Optional[str] = None
    activity_code: Optional[str] = None
    activity_label: Optional[str] = None
    status: Optional[BusinessStatus] = None
    creation_date: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    vat_number: Optional[str] = None
    
    @validator('vat_number', pre=True, always=True)
    def generate_vat_number(cls, v, values):
        if v is None and 'siren' in values:
            siren = values['siren']
            # Calculate VAT number check digits
            remainder = int(siren) % 97
            check_digits = f"{remainder:02d}"
            return f"FR{check_digits}{siren}"
        return v

class INSEEService:
    def __init__(self):
        self.consumer_key = os.environ.get('INSEE_CONSUMER_KEY')
        self.consumer_secret = os.environ.get('INSEE_CONSUMER_SECRET')
        self.base_url = "https://api.insee.fr/entreprises/sirene/V3.11"
        self.auth_url = "https://api.insee.fr/token"
        self.access_token = None
        self.token_expires_at = None
        self.cache = {}
        self.logger = logging.getLogger(__name__)
        
        if not self.consumer_key or not self.consumer_secret:
            self.logger.warning("INSEE API credentials not configured")
    
    async def get_access_token(self) -> Optional[str]:
        """Get or refresh access token"""
        if not self.consumer_key or not self.consumer_secret:
            return None
            
        if self.access_token and self.token_expires_at > datetime.now():
            return self.access_token
        
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials"
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"INSEE authentication failed: {str(e)}")
            return None
    
    async def validate_siren(self, siren: str) -> bool:
        """Validate SIREN number format and existence"""
        if not re.match(r"^\d{9}$", siren):
            return False
        
        if not self._validate_siren_checksum(siren):
            return False
        
        # Check cache first
        cache_key = f"siren_valid_{siren}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            token = await self.get_access_token()
            if not token:
                # Fallback to format validation only
                return True
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/siren/{siren}",
                headers=headers,
                timeout=30
            )
            
            is_valid = response.status_code == 200
            self.cache[cache_key] = is_valid
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error validating SIREN {siren}: {e}")
            # Fallback to format validation
            return True
    
    async def validate_siret(self, siret: str) -> bool:
        """Validate SIRET number format and existence"""
        if not re.match(r"^\d{14}$", siret):
            return False
        
        # Extract SIREN from SIRET
        siren = siret[:9]
        if not self._validate_siren_checksum(siren):
            return False
        
        if not self._validate_siret_checksum(siret):
            return False
        
        # Check cache first
        cache_key = f"siret_valid_{siret}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            token = await self.get_access_token()
            if not token:
                # Fallback to format validation only
                return True
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/siret/{siret}",
                headers=headers,
                timeout=30
            )
            
            is_valid = response.status_code == 200
            self.cache[cache_key] = is_valid
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error validating SIRET {siret}: {e}")
            # Fallback to format validation
            return True
    
    async def get_company_info(self, identifier: str) -> Optional[CompanyInfo]:
        """Retrieve comprehensive company information by SIREN or SIRET"""
        if len(identifier) == 9:
            return await self._get_siren_info(identifier)
        elif len(identifier) == 14:
            return await self._get_siret_info(identifier)
        else:
            return None
    
    async def _get_siren_info(self, siren: str) -> Optional[CompanyInfo]:
        """Get company information by SIREN number"""
        # Check cache first
        cache_key = f"siren_info_{siren}"
        if cache_key in self.cache:
            return CompanyInfo(**self.cache[cache_key])
        
        try:
            token = await self.get_access_token()
            if not token:
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/siren/{siren}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            unite_legale = data.get('uniteLegale', {})
            periodes = unite_legale.get('periodesUniteLegale', [])
            
            if not periodes:
                return None
            
            current_period = periodes[0]  # Most recent period
            
            company_info = CompanyInfo(
                siren=siren,
                denomination=unite_legale.get('denominationUniteLegale'),
                legal_form_code=current_period.get('categorieJuridiqueUniteLegale'),
                activity_code=current_period.get('activitePrincipaleUniteLegale'),
                status=BusinessStatus(current_period.get('etatAdministratifUniteLegale', 'A')),
                creation_date=current_period.get('dateDebut')
            )
            
            # Cache the result
            self.cache[cache_key] = company_info.dict()
            
            return company_info
            
        except Exception as e:
            self.logger.error(f"Error retrieving SIREN info for {siren}: {e}")
            return None
    
    async def _get_siret_info(self, siret: str) -> Optional[CompanyInfo]:
        """Get establishment information by SIRET number"""
        # Check cache first
        cache_key = f"siret_info_{siret}"
        if cache_key in self.cache:
            return CompanyInfo(**self.cache[cache_key])
        
        try:
            token = await self.get_access_token()
            if not token:
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/siret/{siret}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()  
            etablissement = data.get('etablissement', {})
            unite_legale = etablissement.get('uniteLegale', {})
            adresse = etablissement.get('adresseEtablissement', {})
            periodes_unite = unite_legale.get('periodesUniteLegale', [])
            periodes_etab = etablissement.get('periodesEtablissement', [])
            
            current_unite_period = periodes_unite[0] if periodes_unite else {}
            current_etab_period = periodes_etab[0] if periodes_etab else {}
            
            company_info = CompanyInfo(
                siren=etablissement.get('siren'),
                siret=siret,
                denomination=unite_legale.get('denominationUniteLegale'),
                legal_form_code=current_unite_period.get('categorieJuridiqueUniteLegale'),
                activity_code=current_etab_period.get('activitePrincipaleEtablissement'),
                status=BusinessStatus(current_etab_period.get('etatAdministratifEtablissement', 'A')),
                creation_date=current_etab_period.get('dateDebut'),
                address=self._format_address(adresse),
                postal_code=adresse.get('codePostalEtablissement'),
                city=adresse.get('libelleCommuneEtablissement')
            )
            
            # Cache the result
            self.cache[cache_key] = company_info.dict()
            
            return company_info
            
        except Exception as e:
            self.logger.error(f"Error retrieving SIRET info for {siret}: {e}")
            return None
    
    def _format_address(self, adresse: Dict) -> Optional[str]:
        """Format address components into readable string"""
        components = []
        
        if adresse.get('numeroVoieEtablissement'):
            components.append(adresse['numeroVoieEtablissement'])
        
        if adresse.get('typeVoieEtablissement'):
            components.append(adresse['typeVoieEtablissement'])
        
        if adresse.get('libelleVoieEtablissement'):
            components.append(adresse['libelleVoieEtablissement'])
        
        return ' '.join(components) if components else None
    
    @staticmethod
    def _validate_siren_checksum(siren: str) -> bool:
        """Validate SIREN using Luhn algorithm variant"""
        try:
            total = 0
            for i, digit in enumerate(siren):
                n = int(digit)
                if i % 2 == 1:  # Even position (0-indexed)
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                total += n
            return total % 10 == 0
        except:
            return False
    
    @staticmethod
    def _validate_siret_checksum(siret: str) -> bool:
        """Validate SIRET checksum"""
        try:
            # SIRET uses a different algorithm than SIREN
            weights = [3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]
            total = sum(int(digit) * weight for digit, weight in zip(siret[:14], weights))
            return total % 10 == 0
        except:
            return False

# Instance globale du service
insee_service = INSEEService()