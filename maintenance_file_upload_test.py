#!/usr/bin/env python3
"""
Focused test for maintenance file upload functionality
Testing the specific issue reported by user: "Dans la fonctionnalité 'Maintenance & Réparations' l'ajout de fichier ne fonctionne pas"
"""

import requests
import sys
import os
from datetime import datetime, timezone, timedelta
import json

class MaintenanceFileUploadTester:
    def __init__(self, base_url="https://abetoile-rental.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}
        self.errors = []

    def log_error(self, test_name, error_msg):
        """Log errors for detailed reporting"""
        self.errors.append(f"{test_name}: {error_msg}")
        print(f"❌ ERROR in {test_name}: {error_msg}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Only add Content-Type for JSON requests
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    # Remove Content-Type header for multipart/form-data
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, files=files, data=data, headers=headers)
                else:
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
                    return success, response.content
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                    print(f"❌ Failed - {error_msg}")
                except:
                    error_msg += f" - {response.text}"
                    print(f"❌ Failed - {error_msg}")
                
                self.log_error(name, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"❌ Failed - {error_msg}")
            self.log_error(name, error_msg)
            return False, {}

    def authenticate(self):
        """Authenticate and get token"""
        print("🔐 Authenticating...")
        
        # Try to login with existing user first
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
            print(f"   ✅ Authentication successful")
            return True
        
        # If login fails, try to register
        print("   Login failed, trying to register new user...")
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
            # Now login
            success, response = self.run_test(
                "User Login After Registration",
                "POST", 
                "auth/login",
                200,
                data=login_data
            )
            if success and 'access_token' in response:
                self.token = response['access_token']
                print(f"   ✅ Authentication successful after registration")
                return True
        
        print("   ❌ Authentication failed")
        return False

    def setup_test_data(self):
        """Create necessary test data (client, vehicle, maintenance record)"""
        print("\n📋 Setting up test data...")
        
        # Create client
        client_data = {
            "company_name": "Garage Maintenance Test SARL",
            "contact_name": "Pierre Mécanicien",
            "email": "pierre@garage-test.fr",
            "phone": "+33123456789",
            "address": "15 Rue de la Réparation",
            "city": "Lyon",
            "postal_code": "69001",
            "country": "France",
            "vat_rate": 20.0,
            "vat_number": "FR12345678901",
            "rcs_number": "123456789"
        }
        success, response = self.run_test(
            "Create Test Client",
            "POST",
            "clients",
            200,
            data=client_data
        )
        if success:
            self.test_data['client_id'] = response.get('id')
            print(f"   ✅ Client created: {response.get('id')}")
        else:
            return False

        # Create vehicle
        vehicle_data = {
            "type": "van",
            "brand": "Mercedes",
            "model": "Sprinter",
            "license_plate": "MT-123-ST",
            "first_registration": "2020-01-15T00:00:00Z",
            "technical_control_expiry": "2025-01-15T00:00:00Z",
            "insurance_company": "Maintenance Insurance Co",
            "insurance_contract": "MAINT123456",
            "insurance_amount": 8000.0,
            "insurance_expiry": "2025-12-31T00:00:00Z",
            "daily_rate": 85.0,
            "accounting_account": "706000"
        }
        success, response = self.run_test(
            "Create Test Vehicle",
            "POST",
            "vehicles",
            200,
            data=vehicle_data
        )
        if success:
            self.test_data['vehicle_id'] = response.get('id')
            print(f"   ✅ Vehicle created: {response.get('id')}")
        else:
            return False

        # Create maintenance record
        maintenance_data = {
            "vehicle_id": self.test_data['vehicle_id'],
            "maintenance_type": "repair",
            "description": "Réparation système de freinage - Test upload fichier",
            "maintenance_date": datetime.now(timezone.utc).isoformat(),
            "amount_ht": 450.0,
            "vat_rate": 20.0,
            "supplier": "Garage Expert Freins",
            "notes": "Remplacement plaquettes et disques avant"
        }
        success, response = self.run_test(
            "Create Maintenance Record",
            "POST",
            "maintenance",
            200,
            data=maintenance_data
        )
        if success:
            self.test_data['maintenance_record_id'] = response.get('id')
            print(f"   ✅ Maintenance record created: {response.get('id')}")
            print(f"   Description: {response.get('description')}")
            print(f"   Amount HT: {response.get('amount_ht')}€")
            print(f"   Amount TTC: {response.get('amount_ttc')}€")
            return True
        else:
            return False

    def test_file_upload_pdf(self):
        """Test PDF file upload to maintenance record"""
        if 'maintenance_record_id' not in self.test_data:
            self.log_error("PDF Upload", "No maintenance record ID available")
            return False
            
        print("\n📄 Testing PDF file upload...")
        
        # Create a realistic PDF content (invoice-like)
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
(Facture Maintenance) Tj
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
        
        files = {
            'file': ('facture_maintenance_freins.pdf', pdf_content, 'application/pdf')
        }
        data = {
            'label': 'Facture réparation freinage - Garage Expert Freins'
        }

        success, response = self.run_test(
            "Upload PDF Document",
            "POST",
            f"maintenance/{self.test_data['maintenance_record_id']}/documents",
            200,
            data=data,
            files=files
        )
        
        if success:
            document_id = response.get('document_id')
            self.test_data['pdf_document_id'] = document_id
            print(f"   ✅ PDF uploaded successfully")
            print(f"   Document ID: {document_id}")
            print(f"   Message: {response.get('message')}")
            
            # Verify file exists on disk
            file_path = f"/app/documents/{document_id}"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ File saved to disk: {file_path} ({file_size} bytes)")
            else:
                self.log_error("PDF Upload", f"File not found on disk: {file_path}")
                return False
                
            return True
        else:
            return False

    def test_file_upload_jpg(self):
        """Test JPG file upload to maintenance record"""
        if 'maintenance_record_id' not in self.test_data:
            self.log_error("JPG Upload", "No maintenance record ID available")
            return False
            
        print("\n🖼️ Testing JPG file upload...")
        
        # Create a minimal JPG content (JPEG header)
        jpg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
        files = {
            'file': ('photo_reparation_freins.jpg', jpg_content, 'image/jpeg')
        }
        data = {
            'label': 'Photo avant/après réparation freinage'
        }

        success, response = self.run_test(
            "Upload JPG Document",
            "POST",
            f"maintenance/{self.test_data['maintenance_record_id']}/documents",
            200,
            data=data,
            files=files
        )
        
        if success:
            document_id = response.get('document_id')
            self.test_data['jpg_document_id'] = document_id
            print(f"   ✅ JPG uploaded successfully")
            print(f"   Document ID: {document_id}")
            print(f"   Message: {response.get('message')}")
            
            # Verify file exists on disk
            file_path = f"/app/documents/{document_id}"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ File saved to disk: {file_path} ({file_size} bytes)")
            else:
                self.log_error("JPG Upload", f"File not found on disk: {file_path}")
                return False
                
            return True
        else:
            return False

    def test_document_listing(self):
        """Test listing documents for maintenance record"""
        if 'maintenance_record_id' not in self.test_data:
            self.log_error("Document Listing", "No maintenance record ID available")
            return False
            
        print("\n📋 Testing document listing...")
        
        success, response = self.run_test(
            "List Maintenance Documents",
            "GET",
            f"maintenance/{self.test_data['maintenance_record_id']}/documents",
            200
        )
        
        if success:
            documents = response if isinstance(response, list) else []
            print(f"   ✅ Found {len(documents)} documents")
            
            for i, doc in enumerate(documents, 1):
                print(f"   Document {i}:")
                print(f"     - ID: {doc.get('id')}")
                print(f"     - Name: {doc.get('name')}")
                print(f"     - Label: {doc.get('label')}")
                print(f"     - Content Type: {doc.get('content_type')}")
                print(f"     - Size: {doc.get('size')} bytes")
                print(f"     - Created: {doc.get('created_at')}")
            
            # Verify our uploaded documents are in the list
            pdf_found = any(doc.get('id') == self.test_data.get('pdf_document_id') for doc in documents)
            jpg_found = any(doc.get('id') == self.test_data.get('jpg_document_id') for doc in documents)
            
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
            return False

    def test_document_download_pdf(self):
        """Test downloading PDF document"""
        if 'pdf_document_id' not in self.test_data:
            self.log_error("PDF Download", "No PDF document ID available")
            return False
            
        print("\n⬇️ Testing PDF document download...")
        
        url = f"{self.base_url}/documents/{self.test_data['pdf_document_id']}/download"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Verify it's a PDF
                if response.headers.get('Content-Type') == 'application/pdf':
                    print("   ✅ Correct PDF content type")
                else:
                    self.log_error("PDF Download", f"Wrong content type: {response.headers.get('Content-Type')}")
                    return False
                
                # Verify PDF content starts correctly
                if response.content.startswith(b'%PDF'):
                    print("   ✅ Valid PDF content")
                    return True
                else:
                    self.log_error("PDF Download", "Invalid PDF content")
                    return False
            else:
                error_msg = f"Expected 200, got {response.status_code} - {response.text}"
                self.log_error("PDF Download", error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.log_error("PDF Download", error_msg)
            return False

    def test_document_download_jpg(self):
        """Test downloading JPG document"""
        if 'jpg_document_id' not in self.test_data:
            self.log_error("JPG Download", "No JPG document ID available")
            return False
            
        print("\n⬇️ Testing JPG document download...")
        
        url = f"{self.base_url}/documents/{self.test_data['jpg_document_id']}/download"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Verify it's a JPEG
                if response.headers.get('Content-Type') == 'image/jpeg':
                    print("   ✅ Correct JPEG content type")
                else:
                    self.log_error("JPG Download", f"Wrong content type: {response.headers.get('Content-Type')}")
                    return False
                
                # Verify JPEG content starts correctly
                if response.content.startswith(b'\xff\xd8\xff'):
                    print("   ✅ Valid JPEG content")
                    return True
                else:
                    self.log_error("JPG Download", "Invalid JPEG content")
                    return False
            else:
                error_msg = f"Expected 200, got {response.status_code} - {response.text}"
                self.log_error("JPG Download", error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.log_error("JPG Download", error_msg)
            return False

    def test_maintenance_record_update(self):
        """Test that maintenance record is properly updated with document IDs"""
        if 'maintenance_record_id' not in self.test_data:
            self.log_error("Record Update Check", "No maintenance record ID available")
            return False
            
        print("\n🔄 Testing maintenance record document association...")
        
        success, response = self.run_test(
            "Get Updated Maintenance Record",
            "GET",
            f"maintenance/{self.test_data['maintenance_record_id']}",
            200
        )
        
        if success:
            documents = response.get('documents', [])
            print(f"   ✅ Maintenance record has {len(documents)} associated documents")
            
            for i, doc_id in enumerate(documents, 1):
                print(f"   Document {i} ID: {doc_id}")
            
            # Verify our documents are associated
            pdf_associated = self.test_data.get('pdf_document_id') in documents
            jpg_associated = self.test_data.get('jpg_document_id') in documents
            
            if pdf_associated and jpg_associated:
                print("   ✅ Both documents properly associated with maintenance record")
                return True
            else:
                missing = []
                if not pdf_associated:
                    missing.append("PDF")
                if not jpg_associated:
                    missing.append("JPG")
                self.log_error("Record Update Check", f"Documents not associated: {', '.join(missing)}")
                return False
        else:
            return False

    def test_file_system_verification(self):
        """Verify files are actually stored in /app/documents/"""
        print("\n💾 Verifying file system storage...")
        
        # Check if documents directory exists
        if not os.path.exists("/app/documents"):
            self.log_error("File System", "/app/documents directory does not exist")
            return False
        
        print("   ✅ /app/documents directory exists")
        
        # List all files in documents directory
        try:
            files = os.listdir("/app/documents")
            print(f"   Found {len(files)} files in /app/documents/")
            
            # Check our specific documents
            pdf_file_exists = self.test_data.get('pdf_document_id') in files
            jpg_file_exists = self.test_data.get('jpg_document_id') in files
            
            if pdf_file_exists:
                pdf_path = f"/app/documents/{self.test_data['pdf_document_id']}"
                pdf_size = os.path.getsize(pdf_path)
                print(f"   ✅ PDF file exists: {pdf_path} ({pdf_size} bytes)")
            else:
                self.log_error("File System", f"PDF file not found: {self.test_data.get('pdf_document_id')}")
            
            if jpg_file_exists:
                jpg_path = f"/app/documents/{self.test_data['jpg_document_id']}"
                jpg_size = os.path.getsize(jpg_path)
                print(f"   ✅ JPG file exists: {jpg_path} ({jpg_size} bytes)")
            else:
                self.log_error("File System", f"JPG file not found: {self.test_data.get('jpg_document_id')}")
            
            return pdf_file_exists and jpg_file_exists
            
        except Exception as e:
            self.log_error("File System", f"Error checking files: {str(e)}")
            return False

    def test_error_scenarios(self):
        """Test various error scenarios"""
        print("\n⚠️ Testing error scenarios...")
        
        if 'maintenance_record_id' not in self.test_data:
            print("   Skipping error tests - no maintenance record ID")
            return True
        
        # Test 1: Upload unsupported file type
        print("\n   Testing unsupported file type...")
        files = {
            'file': ('test.txt', b'This is a text file', 'text/plain')
        }
        data = {
            'label': 'Text file test'
        }
        
        success, response = self.run_test(
            "Upload Unsupported File Type",
            "POST",
            f"maintenance/{self.test_data['maintenance_record_id']}/documents",
            400,  # Should fail
            data=data,
            files=files
        )
        
        if success:
            print("   ✅ Correctly rejected unsupported file type")
        
        # Test 2: Upload to non-existent maintenance record
        print("\n   Testing upload to non-existent record...")
        files = {
            'file': ('test.pdf', b'%PDF-1.4', 'application/pdf')
        }
        data = {
            'label': 'Test PDF'
        }
        
        success, response = self.run_test(
            "Upload to Non-existent Record",
            "POST",
            "maintenance/non-existent-id/documents",
            404,  # Should fail
            data=data,
            files=files
        )
        
        if success:
            print("   ✅ Correctly returned 404 for non-existent record")
        
        return True

    def run_all_tests(self):
        """Run all maintenance file upload tests"""
        print("🚀 Starting Maintenance File Upload Tests")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed - cannot continue")
            return False
        
        # Run file upload tests
        tests = [
            ("PDF File Upload", self.test_file_upload_pdf),
            ("JPG File Upload", self.test_file_upload_jpg),
            ("Document Listing", self.test_document_listing),
            ("PDF Download", self.test_document_download_pdf),
            ("JPG Download", self.test_document_download_jpg),
            ("Maintenance Record Update", self.test_maintenance_record_update),
            ("File System Verification", self.test_file_system_verification),
            ("Error Scenarios", self.test_error_scenarios),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    print(f"❌ {test_name} failed")
            except Exception as e:
                self.log_error(test_name, f"Exception: {str(e)}")
                print(f"❌ {test_name} failed with exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n✅ NO ERRORS FOUND - All maintenance file upload functionality is working correctly!")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    tester = MaintenanceFileUploadTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)