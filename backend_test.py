import requests
import sys
from datetime import datetime, timezone, timedelta
import json

class AutoProAPITester:
    def __init__(self, base_url="https://abetoile-rental.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_auth_register(self):
        """Test user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "test123",
            "full_name": "Test User"
        }
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success:
            self.test_data['user_id'] = response.get('id')
        return success

    def test_auth_login(self):
        """Test user login"""
        login_data = {
            "username": "testuser",
            "password": "test123"
        }
        success, response = self.run_test(
            "User Login",
            "POST", 
            "auth/login",
            200,
            data=login_data
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
        return success

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me", 
            200
        )
        return success

    def test_create_client(self):
        """Test client creation"""
        client_data = {
            "company_name": "Test Company Ltd",
            "contact_name": "John Doe",
            "email": "john@testcompany.com",
            "phone": "+33123456789",
            "address": "123 Test Street",
            "city": "Paris",
            "postal_code": "75001",
            "country": "France",
            "vat_rate": 20.0,
            "vat_number": "FR12345678901",
            "rcs_number": "123456789"
        }
        success, response = self.run_test(
            "Create Client",
            "POST",
            "clients",
            200,
            data=client_data
        )
        if success:
            self.test_data['client_id'] = response.get('id')
        return success

    def test_get_clients(self):
        """Test get all clients"""
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "clients",
            200
        )
        return success

    def test_get_client(self):
        """Test get specific client"""
        if 'client_id' not in self.test_data:
            print("❌ Skipping - No client ID available")
            return False
            
        success, response = self.run_test(
            "Get Specific Client",
            "GET",
            f"clients/{self.test_data['client_id']}",
            200
        )
        return success

    def test_create_vehicle(self):
        """Test vehicle creation"""
        vehicle_data = {
            "type": "car",
            "brand": "Renault",
            "model": "Clio",
            "license_plate": "AB-123-CD",
            "first_registration": "2020-01-15T00:00:00Z",
            "technical_control_expiry": "2025-01-15T00:00:00Z",
            "insurance_company": "AXA Insurance",
            "insurance_contract": "POL123456",
            "insurance_amount": 5000.0,
            "insurance_expiry": "2025-12-31T00:00:00Z",
            "daily_rate": 45.0,
            "accounting_account": "706000"
        }
        success, response = self.run_test(
            "Create Vehicle",
            "POST",
            "vehicles",
            200,
            data=vehicle_data
        )
        if success:
            self.test_data['vehicle_id'] = response.get('id')
        return success

    def test_get_vehicles(self):
        """Test get all vehicles"""
        success, response = self.run_test(
            "Get All Vehicles",
            "GET",
            "vehicles",
            200
        )
        return success

    def test_create_order(self):
        """Test order creation"""
        if 'client_id' not in self.test_data or 'vehicle_id' not in self.test_data:
            print("❌ Skipping - Missing client or vehicle ID")
            return False
            
        order_data = {
            "client_id": self.test_data['client_id'],
            "items": [
                {
                    "vehicle_id": self.test_data['vehicle_id'],
                    "quantity": 1,
                    "daily_rate": 45.0,
                    "is_renewable": True,
                    "rental_period": "days",
                    "rental_duration": 7
                }
            ],
            "start_date": "2024-12-01T00:00:00Z"
        }
        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data=order_data
        )
        if success:
            self.test_data['order_id'] = response.get('id')
        return success

    def test_get_orders(self):
        """Test get all orders"""
        success, response = self.run_test(
            "Get All Orders",
            "GET",
            "orders",
            200
        )
        return success

    def test_get_invoices(self):
        """Test get all invoices"""
        success, response = self.run_test(
            "Get All Invoices",
            "GET",
            "invoices",
            200
        )
        return success

    def test_get_overdue_invoices(self):
        """Test get overdue invoices"""
        success, response = self.run_test(
            "Get Overdue Invoices",
            "GET",
            "invoices/overdue",
            200
        )
        return success

    def test_dashboard(self):
        """Test dashboard endpoint"""
        success, response = self.run_test(
            "Get Dashboard Data",
            "GET",
            "dashboard",
            200
        )
        if success:
            print(f"   Dashboard data: {response}")
        return success

    def test_get_settings(self):
        """Test get settings"""
        success, response = self.run_test(
            "Get Settings",
            "GET",
            "settings",
            200
        )
        return success

    def test_update_settings(self):
        """Test update settings"""
        settings_data = {
            "id": "test-settings-id",
            "company_name": "AutoPro Rental Test",
            "company_address": "123 Test Avenue, Paris",
            "company_phone": "+33123456789",
            "company_email": "contact@autopro-test.com",
            "vat_rates": {"standard": 20.0, "reduced": 10.0, "super_reduced": 5.5},
            "payment_delays": {"days": 30, "weeks": 7, "months": 30, "years": 365},
            "reminder_periods": [7, 15, 30],
            "reminder_templates": {},
            "accounting_accounts": {
                "sales": "706000",
                "vat_standard": "445571", 
                "vat_reduced": "445572"
            },
            "mailgun_api_key": "test-key",
            "mailgun_domain": "test-domain.com"
        }
        success, response = self.run_test(
            "Update Settings",
            "PUT",
            "settings",
            200,
            data=settings_data
        )
        return success

    def test_generate_invoice_pdf(self):
        """Test PDF generation for invoice"""
        # First get an invoice ID
        success, invoices_response = self.run_test(
            "Get Invoices for PDF Test",
            "GET",
            "invoices",
            200
        )
        
        if not success or not invoices_response:
            print("❌ No invoices found for PDF generation test")
            return False
            
        invoices = invoices_response
        if not invoices:
            print("❌ No invoices available for PDF generation")
            return False
            
        invoice_id = invoices[0]['id']
        self.test_data['invoice_id'] = invoice_id
        
        success, response = self.run_test(
            "Generate Invoice PDF",
            "POST",
            f"invoices/{invoice_id}/generate-pdf",
            200
        )
        
        if success and response.get('pdf_data'):
            print(f"   PDF generated successfully (size: {len(response['pdf_data'])} chars)")
            
        return success

    def test_download_invoice_pdf(self):
        """Test PDF download for invoice"""
        if 'invoice_id' not in self.test_data:
            print("❌ Skipping - No invoice ID available for PDF download")
            return False
            
        invoice_id = self.test_data['invoice_id']
        
        success, response = self.run_test(
            "Download Invoice PDF",
            "GET",
            f"invoices/{invoice_id}/download-pdf",
            200
        )
        return success

    def test_mark_invoice_paid(self):
        """Test marking invoice as paid"""
        if 'invoice_id' not in self.test_data:
            print("❌ Skipping - No invoice ID available")
            return False
            
        invoice_id = self.test_data['invoice_id']
        
        success, response = self.run_test(
            "Mark Invoice as Paid",
            "PUT",
            f"invoices/{invoice_id}/mark-paid",
            200
        )
        return success

    def test_get_accounting_entries(self):
        """Test get accounting entries"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Get Accounting Entries",
            "GET",
            "accounting/entries",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        
        if success:
            print(f"   Found {len(response)} accounting entries")
            
        return success

    def test_get_accounting_summary(self):
        """Test get accounting summary"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Get Accounting Summary",
            "GET",
            "accounting/summary",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        
        if success:
            summary = response.get('summary', {})
            print(f"   Total entries: {summary.get('total_entries', 0)}")
            print(f"   Total debit: {summary.get('total_debit', 0):.2f} €")
            print(f"   Total credit: {summary.get('total_credit', 0):.2f} €")
            print(f"   Is balanced: {summary.get('is_balanced', False)}")
            
        return success

    def test_export_accounting_csv(self):
        """Test export accounting to CSV"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Export Accounting CSV",
            "GET",
            "accounting/export/csv",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        return success

    def test_export_accounting_ciel(self):
        """Test export accounting to CIEL format"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Export Accounting CIEL",
            "GET",
            "accounting/export/ciel",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        return success

    def test_export_accounting_sage(self):
        """Test export accounting to SAGE format"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Export Accounting SAGE",
            "GET",
            "accounting/export/sage",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        return success

    def test_export_accounting_cegid(self):
        """Test export accounting to CEGID format"""
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        success, response = self.run_test(
            "Export Accounting CEGID",
            "GET",
            "accounting/export/cegid",
            200,
            params={
                'start_date': start_date,
                'end_date': today
            }
        )
        return success

    def test_get_vehicle_documents(self):
        """Test get vehicle documents"""
        if 'vehicle_id' not in self.test_data:
            print("❌ Skipping - No vehicle ID available")
            return False
            
        vehicle_id = self.test_data['vehicle_id']
        success, response = self.run_test(
            "Get Vehicle Documents",
            "GET",
            f"vehicles/{vehicle_id}/documents",
            200
        )
        
        if success:
            print(f"   Found {len(response)} vehicle documents")
            
        return success

    def test_upload_vehicle_document(self):
        """Test upload vehicle document"""
        if 'vehicle_id' not in self.test_data:
            print("❌ Skipping - No vehicle ID available")
            return False
            
        vehicle_id = self.test_data['vehicle_id']
        
        # Create a simple test PDF content (base64 encoded)
        import base64
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        # For file upload, we need to use multipart/form-data
        url = f"{self.base_url}/vehicles/{vehicle_id}/documents/upload"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        files = {
            'file': ('test_document.pdf', test_pdf_content, 'application/pdf')
        }
        data = {
            'label': 'Test Vehicle Document',
            'document_type': 'registration_card'
        }

        self.tests_run += 1
        print(f"\n🔍 Testing Upload Vehicle Document...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, files=files, data=data, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    self.test_data['vehicle_document_id'] = response_data.get('id')
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_view_vehicle_document(self):
        """Test view vehicle document (PDF viewing functionality)"""
        if 'vehicle_id' not in self.test_data or 'vehicle_document_id' not in self.test_data:
            print("❌ Skipping - No vehicle or document ID available")
            return False
            
        vehicle_id = self.test_data['vehicle_id']
        document_id = self.test_data['vehicle_document_id']
        
        url = f"{self.base_url}/vehicles/{vehicle_id}/documents/{document_id}/view"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing View Vehicle Document (PDF Viewing)...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Check if it's a PDF response
                if response.headers.get('Content-Type') == 'application/pdf':
                    print(f"   ✅ PDF content served correctly")
                else:
                    print(f"   ⚠️  Expected PDF content-type, got: {response.headers.get('Content-Type')}")
                    
                return success, {}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_download_vehicle_document(self):
        """Test download vehicle document"""
        if 'vehicle_id' not in self.test_data or 'vehicle_document_id' not in self.test_data:
            print("❌ Skipping - No vehicle or document ID available")
            return False
            
        vehicle_id = self.test_data['vehicle_id']
        document_id = self.test_data['vehicle_document_id']
        
        success, response = self.run_test(
            "Download Vehicle Document",
            "GET",
            f"vehicles/{vehicle_id}/documents/{document_id}/download",
            200
        )
        return success

    def test_get_client_documents(self):
        """Test get client documents"""
        if 'client_id' not in self.test_data:
            print("❌ Skipping - No client ID available")
            return False
            
        client_id = self.test_data['client_id']
        success, response = self.run_test(
            "Get Client Documents",
            "GET",
            f"clients/{client_id}/documents",
            200
        )
        
        if success:
            print(f"   Found {len(response)} client documents")
            
        return success

    # NEW INTEGRATION TESTS FOR ENHANCED FEATURES
    
    def test_validate_business_siren(self):
        """Test business validation with valid SIREN"""
        validation_data = {
            "identifier": "732829320"  # Google France SIREN
        }
        success, response = self.run_test(
            "Validate Business - Valid SIREN",
            "POST",
            "validate/business",
            200,
            data=validation_data
        )
        
        if success:
            print(f"   Validation result: {response.get('is_valid', False)}")
            print(f"   Identifier type: {response.get('identifier_type', 'Unknown')}")
            if response.get('company_info'):
                print(f"   Company name: {response['company_info'].get('denomination', 'N/A')}")
        
        return success

    def test_validate_business_siret(self):
        """Test business validation with valid SIRET"""
        validation_data = {
            "identifier": "73282932000074"  # Google France SIRET
        }
        success, response = self.run_test(
            "Validate Business - Valid SIRET",
            "POST",
            "validate/business",
            200,
            data=validation_data
        )
        
        if success:
            print(f"   Validation result: {response.get('is_valid', False)}")
            print(f"   Identifier type: {response.get('identifier_type', 'Unknown')}")
            if response.get('company_info'):
                print(f"   Company name: {response['company_info'].get('denomination', 'N/A')}")
        
        return success

    def test_validate_business_invalid_format(self):
        """Test business validation with invalid format"""
        validation_data = {
            "identifier": "123456"  # Invalid format
        }
        success, response = self.run_test(
            "Validate Business - Invalid Format",
            "POST",
            "validate/business",
            200,
            data=validation_data
        )
        
        if success:
            print(f"   Validation result: {response.get('is_valid', False)}")
            print(f"   Validation errors: {response.get('validation_errors', [])}")
        
        return success

    def test_validate_business_nonexistent(self):
        """Test business validation with non-existent number"""
        validation_data = {
            "identifier": "123456789"  # Non-existent SIREN
        }
        success, response = self.run_test(
            "Validate Business - Non-existent",
            "POST",
            "validate/business",
            200,
            data=validation_data
        )
        
        if success:
            print(f"   Validation result: {response.get('is_valid', False)}")
            print(f"   Validation errors: {response.get('validation_errors', [])}")
        
        return success

    def test_autofill_business_siren(self):
        """Test auto-fill business data with SIREN"""
        autofill_data = {
            "identifier": "732829320"  # Google France SIREN
        }
        success, response = self.run_test(
            "Auto-fill Business - SIREN",
            "POST",
            "autofill/business",
            200,
            data=autofill_data
        )
        
        if success:
            print(f"   Auto-fill success: {response.get('success', False)}")
            company_data = response.get('company_data', {})
            if company_data:
                print(f"   Company name: {company_data.get('company_name', 'N/A')}")
                print(f"   Address: {company_data.get('address', 'N/A')}")
                print(f"   City: {company_data.get('city', 'N/A')}")
            missing_fields = response.get('missing_fields', [])
            if missing_fields:
                print(f"   Missing fields: {missing_fields}")
        
        return success

    def test_autofill_business_siret(self):
        """Test auto-fill business data with SIRET"""
        autofill_data = {
            "identifier": "73282932000074"  # Google France SIRET
        }
        success, response = self.run_test(
            "Auto-fill Business - SIRET",
            "POST",
            "autofill/business",
            200,
            data=autofill_data
        )
        
        if success:
            print(f"   Auto-fill success: {response.get('success', False)}")
            company_data = response.get('company_data', {})
            if company_data:
                print(f"   Company name: {company_data.get('company_name', 'N/A')}")
                print(f"   Address: {company_data.get('address', 'N/A')}")
                print(f"   City: {company_data.get('city', 'N/A')}")
        
        return success

    def test_autofill_business_invalid(self):
        """Test auto-fill business data with invalid identifier"""
        autofill_data = {
            "identifier": "invalid123"
        }
        success, response = self.run_test(
            "Auto-fill Business - Invalid",
            "POST",
            "autofill/business",
            200,
            data=autofill_data
        )
        
        if success:
            print(f"   Auto-fill success: {response.get('success', False)}")
            missing_fields = response.get('missing_fields', [])
            if missing_fields:
                print(f"   Missing fields/errors: {missing_fields}")
        
        return success

    def test_send_invoice_notification(self):
        """Test sending invoice notification email"""
        # First get an invoice ID
        success, invoices_response = self.run_test(
            "Get Invoices for Email Test",
            "GET",
            "invoices",
            200
        )
        
        if not success or not invoices_response:
            print("❌ No invoices found for email notification test")
            return False
            
        invoices = invoices_response
        if not invoices:
            print("❌ No invoices available for email notification")
            return False
            
        invoice_id = invoices[0]['id']
        
        email_data = {
            "recipient": "test@example.com",
            "invoice_id": invoice_id
        }
        
        success, response = self.run_test(
            "Send Invoice Notification Email",
            "POST",
            "notifications/invoice",
            200,
            data=email_data
        )
        
        if success:
            print(f"   Email success: {response.get('success', False)}")
            print(f"   Message: {response.get('message', 'N/A')}")
        
        return success

    def test_send_payment_reminder_standard(self):
        """Test sending standard payment reminder email"""
        # First get an invoice ID
        success, invoices_response = self.run_test(
            "Get Invoices for Payment Reminder Test",
            "GET",
            "invoices",
            200
        )
        
        if not success or not invoices_response:
            print("❌ No invoices found for payment reminder test")
            return False
            
        invoices = invoices_response
        if not invoices:
            print("❌ No invoices available for payment reminder")
            return False
            
        invoice_id = invoices[0]['id']
        
        reminder_data = {
            "recipient": "test@example.com",
            "invoice_id": invoice_id,
            "urgency_level": "standard"
        }
        
        success, response = self.run_test(
            "Send Payment Reminder - Standard",
            "POST",
            "notifications/payment-reminder",
            200,
            data=reminder_data
        )
        
        if success:
            print(f"   Email success: {response.get('success', False)}")
            print(f"   Message: {response.get('message', 'N/A')}")
        
        return success

    def test_send_payment_reminder_urgent(self):
        """Test sending urgent payment reminder email"""
        # First get an invoice ID
        success, invoices_response = self.run_test(
            "Get Invoices for Urgent Reminder Test",
            "GET",
            "invoices",
            200
        )
        
        if not success or not invoices_response:
            print("❌ No invoices found for urgent reminder test")
            return False
            
        invoices = invoices_response
        if not invoices:
            print("❌ No invoices available for urgent reminder")
            return False
            
        invoice_id = invoices[0]['id']
        
        reminder_data = {
            "recipient": "test@example.com",
            "invoice_id": invoice_id,
            "urgency_level": "urgent"
        }
        
        success, response = self.run_test(
            "Send Payment Reminder - Urgent",
            "POST",
            "notifications/payment-reminder",
            200,
            data=reminder_data
        )
        
        if success:
            print(f"   Email success: {response.get('success', False)}")
            print(f"   Message: {response.get('message', 'N/A')}")
        
        return success

def main():
    print("🚀 Starting AutoPro Rental API Tests")
    print("=" * 50)
    
    tester = AutoProAPITester()
    
    # Test sequence
    tests = [
        # Authentication tests
        ("Authentication - Register", tester.test_auth_register),
        ("Authentication - Login", tester.test_auth_login),
        ("Authentication - Get Me", tester.test_auth_me),
        
        # Client tests
        ("Client - Create", tester.test_create_client),
        ("Client - Get All", tester.test_get_clients),
        ("Client - Get Specific", tester.test_get_client),
        
        # Vehicle tests
        ("Vehicle - Create", tester.test_create_vehicle),
        ("Vehicle - Get All", tester.test_get_vehicles),
        
        # Order tests (CRITICAL - User reported broken)
        ("Order - Create", tester.test_create_order),
        ("Order - Get All", tester.test_get_orders),
        
        # Document tests (CRITICAL - User reported PDF viewing broken)
        ("Vehicle Documents - Get List", tester.test_get_vehicle_documents),
        ("Vehicle Documents - Upload", tester.test_upload_vehicle_document),
        ("Vehicle Documents - View PDF", tester.test_view_vehicle_document),
        ("Vehicle Documents - Download", tester.test_download_vehicle_document),
        ("Client Documents - Get List", tester.test_get_client_documents),
        
        # Invoice tests
        ("Invoice - Get All", tester.test_get_invoices),
        ("Invoice - Get Overdue", tester.test_get_overdue_invoices),
        
        # PDF Generation tests
        ("PDF - Generate Invoice PDF", tester.test_generate_invoice_pdf),
        ("PDF - Download Invoice PDF", tester.test_download_invoice_pdf),
        ("Invoice - Mark as Paid", tester.test_mark_invoice_paid),
        
        # Accounting tests
        ("Accounting - Get Entries", tester.test_get_accounting_entries),
        ("Accounting - Get Summary", tester.test_get_accounting_summary),
        ("Accounting - Export CSV", tester.test_export_accounting_csv),
        ("Accounting - Export CIEL", tester.test_export_accounting_ciel),
        ("Accounting - Export SAGE", tester.test_export_accounting_sage),
        ("Accounting - Export CEGID", tester.test_export_accounting_cegid),
        
        # Dashboard and Settings
        ("Dashboard - Get Data", tester.test_dashboard),
        ("Settings - Get", tester.test_get_settings),
        ("Settings - Update", tester.test_update_settings),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())