#!/usr/bin/env python3
"""
Frontend simulation test for maintenance file upload
This test simulates the exact frontend behavior to identify the issue
"""

import requests
import sys
import os
from datetime import datetime, timezone, timedelta
import json

class FrontendSimulationTester:
    def __init__(self, base_url="https://abetoile-rental.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
        self.errors = []

    def log_error(self, test_name, error_msg):
        """Log errors for detailed reporting"""
        self.errors.append(f"{test_name}: {error_msg}")
        print(f"❌ ERROR in {test_name}: {error_msg}")

    def authenticate(self):
        """Authenticate like the frontend does"""
        print("🔐 Authenticating (simulating frontend login)...")
        
        login_data = {
            "username": "testuser",
            "password": "test123"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                
                # Set up session headers like frontend axios interceptor
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                
                print(f"   ✅ Authentication successful")
                print(f"   Token: {self.token[:20]}...")
                return True
            else:
                print(f"   ❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication error: {str(e)}")
            return False

    def create_maintenance_record(self):
        """Create a maintenance record like the frontend does"""
        print("\n📋 Creating maintenance record (simulating frontend form submission)...")
        
        # First create a vehicle
        vehicle_data = {
            "type": "van",
            "brand": "Mercedes",
            "model": "Sprinter",
            "license_plate": "FE-456-ST",
            "first_registration": "2020-01-15T00:00:00Z",
            "technical_control_expiry": "2025-01-15T00:00:00Z",
            "insurance_company": "Frontend Test Insurance",
            "insurance_contract": "FE123456",
            "insurance_amount": 8000.0,
            "insurance_expiry": "2025-12-31T00:00:00Z",
            "daily_rate": 85.0,
            "accounting_account": "706000"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/vehicles", json=vehicle_data)
            if response.status_code != 200:
                self.log_error("Vehicle Creation", f"Status {response.status_code}: {response.text}")
                return False
            
            vehicle_id = response.json().get('id')
            print(f"   ✅ Vehicle created: {vehicle_id}")
            
        except Exception as e:
            self.log_error("Vehicle Creation", str(e))
            return False
        
        # Create client
        client_data = {
            "company_name": "Frontend Test Garage SARL",
            "contact_name": "Jean Frontend",
            "email": "jean@frontend-test.fr",
            "phone": "+33123456789",
            "address": "123 Rue Frontend",
            "city": "Lyon",
            "postal_code": "69001",
            "country": "France",
            "vat_rate": 20.0
        }
        
        try:
            response = self.session.post(f"{self.base_url}/clients", json=client_data)
            if response.status_code != 200:
                self.log_error("Client Creation", f"Status {response.status_code}: {response.text}")
                return False
            
            client_id = response.json().get('id')
            print(f"   ✅ Client created: {client_id}")
            
        except Exception as e:
            self.log_error("Client Creation", str(e))
            return False
        
        # Create maintenance record exactly like frontend form
        maintenance_data = {
            "vehicle_id": vehicle_id,
            "maintenance_type": "repair",
            "description": "Réparation système de freinage - Test frontend",
            "maintenance_date": datetime.now(timezone.utc).isoformat(),
            "amount_ht": 450.0,
            "vat_rate": 20.0,
            "supplier": "Garage Frontend Test",
            "notes": "Test d'upload de fichier depuis le frontend"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/maintenance", json=maintenance_data)
            if response.status_code != 200:
                self.log_error("Maintenance Creation", f"Status {response.status_code}: {response.text}")
                return False
            
            maintenance_record = response.json()
            self.maintenance_id = maintenance_record.get('id')
            print(f"   ✅ Maintenance record created: {self.maintenance_id}")
            print(f"   Description: {maintenance_record.get('description')}")
            print(f"   Amount TTC: {maintenance_record.get('amount_ttc')}€")
            
            return True
            
        except Exception as e:
            self.log_error("Maintenance Creation", str(e))
            return False

    def test_file_upload_frontend_style(self):
        """Test file upload exactly like the frontend does"""
        print("\n📄 Testing file upload (simulating frontend behavior)...")
        
        if not hasattr(self, 'maintenance_id'):
            self.log_error("File Upload", "No maintenance record ID available")
            return False
        
        # Create test files like frontend would
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Facture Frontend Test) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
284
%%EOF"""
        
        # Test 1: Upload PDF exactly like frontend
        print("\n   Testing PDF upload (frontend simulation)...")
        
        files = {
            'file': ('facture_frontend_test.pdf', pdf_content, 'application/pdf')
        }
        data = {
            'label': 'facture_frontend_test.pdf'  # Frontend uses filename as label
        }
        
        # Remove Content-Type header to let requests handle multipart/form-data
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(
                f"{self.base_url}/maintenance/{self.maintenance_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                pdf_doc_id = result.get('document_id')
                print(f"   ✅ PDF uploaded successfully")
                print(f"   Document ID: {pdf_doc_id}")
                print(f"   Message: {result.get('message')}")
                
                # Verify file exists on disk
                file_path = f"/app/documents/{pdf_doc_id}"
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   ✅ File saved to disk: {file_path} ({file_size} bytes)")
                else:
                    self.log_error("PDF Upload", f"File not found on disk: {file_path}")
                    return False
                
                self.pdf_doc_id = pdf_doc_id
                
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                self.log_error("PDF Upload", error_msg)
                print(f"   Request details:")
                print(f"     URL: {response.url}")
                print(f"     Files: {files}")
                print(f"     Data: {data}")
                return False
                
        except Exception as e:
            self.log_error("PDF Upload", f"Exception: {str(e)}")
            return False
        
        # Test 2: Upload JPG
        print("\n   Testing JPG upload (frontend simulation)...")
        
        jpg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
        files = {
            'file': ('photo_frontend_test.jpg', jpg_content, 'image/jpeg')
        }
        data = {
            'label': 'photo_frontend_test.jpg'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/maintenance/{self.maintenance_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                jpg_doc_id = result.get('document_id')
                print(f"   ✅ JPG uploaded successfully")
                print(f"   Document ID: {jpg_doc_id}")
                
                self.jpg_doc_id = jpg_doc_id
                
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                self.log_error("JPG Upload", error_msg)
                return False
                
        except Exception as e:
            self.log_error("JPG Upload", f"Exception: {str(e)}")
            return False
        
        return True

    def test_document_listing_frontend_style(self):
        """Test document listing like frontend does"""
        print("\n📋 Testing document listing (frontend simulation)...")
        
        if not hasattr(self, 'maintenance_id'):
            self.log_error("Document Listing", "No maintenance record ID available")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/maintenance/{self.maintenance_id}/documents")
            
            if response.status_code == 200:
                documents = response.json()
                print(f"   ✅ Found {len(documents)} documents")
                
                for i, doc in enumerate(documents, 1):
                    print(f"   Document {i}:")
                    print(f"     - ID: {doc.get('id')}")
                    print(f"     - Name: {doc.get('name')}")
                    print(f"     - Label: {doc.get('label')}")
                    print(f"     - Content Type: {doc.get('content_type')}")
                    print(f"     - Size: {doc.get('size')} bytes")
                
                # Verify our documents are there
                pdf_found = any(doc.get('id') == getattr(self, 'pdf_doc_id', None) for doc in documents)
                jpg_found = any(doc.get('id') == getattr(self, 'jpg_doc_id', None) for doc in documents)
                
                if pdf_found and jpg_found:
                    print("   ✅ Both uploaded documents found in list")
                    return True
                else:
                    missing = []
                    if not pdf_found:
                        missing.append("PDF")
                    if not jpg_found:
                        missing.append("JPG")
                    self.log_error("Document Listing", f"Missing documents: {', '.join(missing)}")
                    return False
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                self.log_error("Document Listing", error_msg)
                return False
                
        except Exception as e:
            self.log_error("Document Listing", f"Exception: {str(e)}")
            return False

    def test_document_download_frontend_style(self):
        """Test document download like frontend does"""
        print("\n⬇️ Testing document download (frontend simulation)...")
        
        if not hasattr(self, 'pdf_doc_id'):
            self.log_error("Document Download", "No PDF document ID available")
            return False
        
        try:
            # Test download like frontend window.open() would do
            response = self.session.get(f"{self.base_url}/documents/{self.pdf_doc_id}/download")
            
            if response.status_code == 200:
                print(f"   ✅ Document download successful")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Verify it's a PDF
                if response.content.startswith(b'%PDF'):
                    print("   ✅ Valid PDF content")
                    return True
                else:
                    self.log_error("Document Download", "Invalid PDF content")
                    return False
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                self.log_error("Document Download", error_msg)
                return False
                
        except Exception as e:
            self.log_error("Document Download", f"Exception: {str(e)}")
            return False

    def test_error_scenarios_frontend_style(self):
        """Test error scenarios like frontend would encounter"""
        print("\n⚠️ Testing error scenarios (frontend simulation)...")
        
        if not hasattr(self, 'maintenance_id'):
            print("   Skipping error tests - no maintenance record ID")
            return True
        
        # Test 1: Upload without authentication (simulate expired token)
        print("\n   Testing upload without authentication...")
        
        files = {
            'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')
        }
        data = {
            'label': 'test.pdf'
        }
        
        # Remove authorization header
        headers = {}
        
        try:
            response = requests.post(
                f"{self.base_url}/maintenance/{self.maintenance_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 401:
                print("   ✅ Correctly returned 401 for unauthenticated request")
            else:
                print(f"   ⚠️ Expected 401, got {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Exception during auth test: {str(e)}")
        
        # Test 2: Upload unsupported file type
        print("\n   Testing unsupported file type...")
        
        files = {
            'file': ('test.txt', b'This is a text file', 'text/plain')
        }
        data = {
            'label': 'test.txt'
        }
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(
                f"{self.base_url}/maintenance/{self.maintenance_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 400:
                print("   ✅ Correctly rejected unsupported file type")
                print(f"   Error message: {response.json().get('detail', 'No detail')}")
            else:
                print(f"   ⚠️ Expected 400, got {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Exception during file type test: {str(e)}")
        
        return True

    def run_all_tests(self):
        """Run all frontend simulation tests"""
        print("🚀 Starting Frontend Simulation Tests for Maintenance File Upload")
        print("=" * 70)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue")
            return False
        
        # Create maintenance record
        if not self.create_maintenance_record():
            print("❌ Maintenance record creation failed - cannot continue")
            return False
        
        # Run file upload tests
        tests = [
            ("File Upload", self.test_file_upload_frontend_style),
            ("Document Listing", self.test_document_listing_frontend_style),
            ("Document Download", self.test_document_download_frontend_style),
            ("Error Scenarios", self.test_error_scenarios_frontend_style),
        ]
        
        success_count = 0
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    success_count += 1
                    print(f"✅ {test_name} passed")
                else:
                    print(f"❌ {test_name} failed")
            except Exception as e:
                self.log_error(test_name, f"Exception: {str(e)}")
                print(f"❌ {test_name} failed with exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 FRONTEND SIMULATION TEST SUMMARY")
        print("=" * 70)
        print(f"Tests run: {len(tests)}")
        print(f"Tests passed: {success_count}")
        print(f"Tests failed: {len(tests) - success_count}")
        print(f"Success rate: {(success_count/len(tests)*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n✅ NO ERRORS FOUND - Maintenance file upload works correctly from frontend perspective!")
        
        # Additional diagnosis
        print("\n🔍 DIAGNOSIS:")
        if len(self.errors) == 0:
            print("   • Backend API is working correctly")
            print("   • Authentication is working")
            print("   • File upload endpoints are functional")
            print("   • Files are being saved to disk properly")
            print("   • Document listing and download work")
            print("   • The issue may be in the frontend UI or user workflow")
        else:
            print("   • Issues found in backend API functionality")
            print("   • Check the errors above for specific problems")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    tester = FrontendSimulationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)