#!/usr/bin/env python3
"""
Enhanced Features Test Script for Abetoile Location Backend
Tests the new order and payment management features specifically
"""

import requests
import sys
from datetime import datetime, timezone, timedelta
import json

class EnhancedFeaturesAPITester:
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

    def setup_auth_and_data(self):
        """Setup authentication and basic test data"""
        # Login
        login_data = {"username": "testuser", "password": "test123"}
        success, response = self.run_test("User Login", "POST", "auth/login", 200, data=login_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
        else:
            print("❌ Failed to authenticate - cannot continue")
            return False

        # Get existing client and vehicle
        success, clients = self.run_test("Get Clients", "GET", "clients", 200)
        if success and clients:
            self.test_data['client_id'] = clients[0]['id']
            print(f"   Using client: {clients[0]['company_name']}")
        else:
            print("❌ No clients found - cannot continue")
            return False

        success, vehicles = self.run_test("Get Vehicles", "GET", "vehicles", 200)
        if success and vehicles:
            self.test_data['vehicle_id'] = vehicles[0]['id']
            print(f"   Using vehicle: {vehicles[0]['brand']} {vehicles[0]['model']}")
        else:
            print("❌ No vehicles found - cannot continue")
            return False

        return True

    def test_enhanced_order_creation_with_deposit(self):
        """Test enhanced order creation with deposit and complex pricing"""
        print("\n" + "="*60)
        print("🚀 TESTING ENHANCED ORDER CREATION WITH DEPOSIT")
        print("="*60)
        
        # Test scenario: 1 item for 5 days at 50€/day + 200€ deposit
        start_date = datetime.now(timezone.utc) + timedelta(days=1)
        end_date = start_date + timedelta(days=4)  # 5 days total (inclusive)
        
        order_data = {
            "client_id": self.test_data['client_id'],
            "deposit_amount": 200.0,
            "items": [
                {
                    "vehicle_id": self.test_data['vehicle_id'],
                    "quantity": 1,
                    "daily_rate": 50.0,
                    "is_renewable": True,
                    "rental_period": "days",
                    "rental_duration": 5,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            ]
        }
        
        success, response = self.run_test(
            "Enhanced Order Creation - With Deposit",
            "POST",
            "orders",
            200,
            data=order_data
        )
        
        if success:
            # Verify calculations
            expected_total_ht = 5 * 50.0  # 5 days × 50€ = 250€
            expected_vat = expected_total_ht * 0.20  # 20% VAT = 50€
            expected_total_ttc = expected_total_ht + expected_vat  # 300€
            expected_deposit_vat = 200.0 * 0.20  # 40€
            expected_grand_total = expected_total_ttc + 200.0 + expected_deposit_vat  # 540€
            
            print(f"\n📊 ORDER CALCULATION VERIFICATION:")
            print(f"   Order ID: {response.get('id')}")
            print(f"   Total HT: {response.get('total_ht', 0):.2f}€ (expected: {expected_total_ht:.2f}€)")
            print(f"   Total VAT: {response.get('total_vat', 0):.2f}€ (expected: {expected_vat:.2f}€)")
            print(f"   Total TTC: {response.get('total_ttc', 0):.2f}€ (expected: {expected_total_ttc:.2f}€)")
            print(f"   Deposit: {response.get('deposit_amount', 0):.2f}€")
            print(f"   Deposit VAT: {response.get('deposit_vat', 0):.2f}€ (expected: {expected_deposit_vat:.2f}€)")
            print(f"   Grand Total: {response.get('grand_total', 0):.2f}€ (expected: {expected_grand_total:.2f}€)")
            
            # Verify item calculations
            items = response.get('items', [])
            if items:
                item = items[0]
                print(f"   Item total days: {item.get('total_days', 0)} (expected: 5)")
                print(f"   Item total HT: {item.get('item_total_ht', 0):.2f}€ (expected: {expected_total_ht:.2f}€)")
            
            # Store for payment tests
            self.test_data['enhanced_order_id'] = response.get('id')
            
            # Verify calculations are correct
            calculations_correct = (
                abs(response.get('total_ht', 0) - expected_total_ht) < 0.01 and
                abs(response.get('total_vat', 0) - expected_vat) < 0.01 and
                abs(response.get('total_ttc', 0) - expected_total_ttc) < 0.01 and
                abs(response.get('deposit_vat', 0) - expected_deposit_vat) < 0.01 and
                abs(response.get('grand_total', 0) - expected_grand_total) < 0.01
            )
            
            if calculations_correct:
                print("   ✅ All calculations are CORRECT!")
            else:
                print("   ❌ Calculation errors detected!")
                
        return success

    def test_invoice_creation_from_enhanced_order(self):
        """Test that invoice is created from enhanced order with correct structure"""
        print("\n" + "="*60)
        print("🧾 TESTING ENHANCED INVOICE CREATION")
        print("="*60)
        
        if 'enhanced_order_id' not in self.test_data:
            print("❌ Skipping - No enhanced order ID available")
            return False
            
        success, response = self.run_test(
            "Get Invoices - Enhanced Order",
            "GET",
            "invoices",
            200
        )
        
        if success:
            # Find invoice for our enhanced order
            enhanced_invoice = None
            for invoice in response:
                if invoice.get('order_id') == self.test_data['enhanced_order_id']:
                    enhanced_invoice = invoice
                    break
            
            if enhanced_invoice:
                print(f"\n📋 INVOICE STRUCTURE VERIFICATION:")
                print(f"   Found invoice: {enhanced_invoice.get('invoice_number')}")
                print(f"   Invoice deposit amount: {enhanced_invoice.get('deposit_amount', 0):.2f}€")
                print(f"   Invoice deposit VAT: {enhanced_invoice.get('deposit_vat', 0):.2f}€")
                print(f"   Invoice grand total: {enhanced_invoice.get('grand_total', 0):.2f}€")
                print(f"   Invoice remaining amount: {enhanced_invoice.get('remaining_amount', 0):.2f}€")
                print(f"   Invoice status: {enhanced_invoice.get('status')}")
                
                # Store for payment tests
                self.test_data['enhanced_invoice_id'] = enhanced_invoice.get('id')
                self.test_data['enhanced_invoice_total'] = enhanced_invoice.get('grand_total', 0)
                
                return True
            else:
                print("❌ No invoice found for enhanced order")
                return False
        
        return success

    def test_multiple_payment_management(self):
        """Test multiple payment management features"""
        print("\n" + "="*60)
        print("💳 TESTING MULTIPLE PAYMENT MANAGEMENT")
        print("="*60)
        
        if 'enhanced_invoice_id' not in self.test_data:
            print("❌ Skipping - No enhanced invoice ID available")
            return False

        # Test 1: Add partial payment
        payment_data = {
            "amount": 100.0,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": "bank",
            "reference": "BANK001",
            "notes": "First partial payment"
        }
        
        success1, response1 = self.run_test(
            "Add Partial Payment",
            "POST",
            f"invoices/{self.test_data['enhanced_invoice_id']}/payments",
            200,
            data=payment_data
        )
        
        if success1:
            print(f"   Payment ID: {response1.get('id')}")
            print(f"   Payment amount: {response1.get('amount', 0):.2f}€")
            print(f"   Payment method: {response1.get('payment_method')}")
            self.test_data['partial_payment_id'] = response1.get('id')

        # Test 2: Add second payment
        remaining_amount = self.test_data.get('enhanced_invoice_total', 540.0) - 100.0
        
        payment_data2 = {
            "amount": remaining_amount,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": "card",
            "reference": "CARD002",
            "notes": "Final payment to complete invoice"
        }
        
        success2, response2 = self.run_test(
            "Add Final Payment",
            "POST",
            f"invoices/{self.test_data['enhanced_invoice_id']}/payments",
            200,
            data=payment_data2
        )
        
        if success2:
            print(f"   Final payment ID: {response2.get('id')}")
            print(f"   Final payment amount: {response2.get('amount', 0):.2f}€")
            self.test_data['final_payment_id'] = response2.get('id')

        # Test 3: Get all payments for invoice
        success3, response3 = self.run_test(
            "Get Invoice Payments",
            "GET",
            f"invoices/{self.test_data['enhanced_invoice_id']}/payments",
            200
        )
        
        if success3:
            print(f"\n💰 PAYMENT SUMMARY:")
            print(f"   Found {len(response3)} payments")
            total_paid = sum(payment.get('amount', 0) for payment in response3)
            print(f"   Total amount paid: {total_paid:.2f}€")
            
            for i, payment in enumerate(response3, 1):
                print(f"   Payment {i}: {payment.get('amount', 0):.2f}€ via {payment.get('payment_method')} (Ref: {payment.get('reference', 'N/A')})")

        # Test 4: Verify invoice status is updated to 'paid'
        success4, invoices = self.run_test(
            "Verify Invoice Status After Payments",
            "GET",
            "invoices",
            200
        )
        
        if success4:
            enhanced_invoice = None
            for invoice in invoices:
                if invoice.get('id') == self.test_data['enhanced_invoice_id']:
                    enhanced_invoice = invoice
                    break
            
            if enhanced_invoice:
                print(f"\n📊 INVOICE STATUS AFTER PAYMENTS:")
                print(f"   Invoice status: {enhanced_invoice.get('status')}")
                print(f"   Amount paid: {enhanced_invoice.get('amount_paid', 0):.2f}€")
                print(f"   Remaining amount: {enhanced_invoice.get('remaining_amount', 0):.2f}€")
                
                if enhanced_invoice.get('status') == 'paid':
                    print("   ✅ Invoice status correctly updated to 'paid'")
                else:
                    print(f"   ❌ Expected status 'paid', got '{enhanced_invoice.get('status')}'")

        return success1 and success2 and success3 and success4

    def test_payment_deletion(self):
        """Test payment deletion and status updates"""
        print("\n" + "="*60)
        print("🗑️  TESTING PAYMENT DELETION")
        print("="*60)
        
        if 'partial_payment_id' not in self.test_data:
            print("❌ Skipping - No payment ID available")
            return False
            
        success, response = self.run_test(
            "Delete Payment",
            "DELETE",
            f"payments/{self.test_data['partial_payment_id']}",
            200
        )
        
        if success:
            print(f"   Payment deleted: {response.get('message', 'N/A')}")
            
            # Verify invoice status is updated
            success2, invoices = self.run_test(
                "Verify Invoice After Payment Deletion",
                "GET",
                "invoices",
                200
            )
            
            if success2:
                enhanced_invoice = None
                for invoice in invoices:
                    if invoice.get('id') == self.test_data['enhanced_invoice_id']:
                        enhanced_invoice = invoice
                        break
                
                if enhanced_invoice:
                    print(f"\n📊 INVOICE STATUS AFTER DELETION:")
                    print(f"   Updated status: {enhanced_invoice.get('status')}")
                    print(f"   Updated amount paid: {enhanced_invoice.get('amount_paid', 0):.2f}€")
                    print(f"   Updated remaining: {enhanced_invoice.get('remaining_amount', 0):.2f}€")
                    
                    if enhanced_invoice.get('status') == 'partially_paid':
                        print("   ✅ Invoice status correctly updated after payment deletion")
                    else:
                        print(f"   ❌ Expected 'partially_paid', got '{enhanced_invoice.get('status')}'")
                        
        return success

    def test_order_renewal_process(self):
        """Test order renewal process"""
        print("\n" + "="*60)
        print("🔄 TESTING ORDER RENEWAL PROCESS")
        print("="*60)
        
        success, response = self.run_test(
            "Trigger Order Renewal",
            "POST",
            "orders/renew",
            200
        )
        
        if success:
            print(f"   Renewal message: {response.get('message', 'N/A')}")
            print("   ✅ Order renewal process completed successfully")
            
        return success

    def test_payment_edge_cases(self):
        """Test payment validation and edge cases"""
        print("\n" + "="*60)
        print("⚠️  TESTING PAYMENT EDGE CASES")
        print("="*60)
        
        if 'enhanced_invoice_id' not in self.test_data:
            print("❌ Skipping - No enhanced invoice ID available")
            return False
            
        # Test 1: Negative payment amount
        negative_payment = {
            "amount": -50.0,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": "bank",
            "notes": "Negative payment test"
        }
        
        success1, response1 = self.run_test(
            "Payment Edge Case - Negative Amount",
            "POST",
            f"invoices/{self.test_data['enhanced_invoice_id']}/payments",
            400,  # Should fail with 400
            data=negative_payment
        )
        
        if success1:
            print("   ✅ Correctly rejected negative payment amount")
        
        # Test 2: Payment exceeding remaining balance
        success_inv, invoices = self.run_test(
            "Get Invoice for Overpayment Test",
            "GET",
            "invoices",
            200
        )
        
        if success_inv:
            enhanced_invoice = None
            for invoice in invoices:
                if invoice.get('id') == self.test_data['enhanced_invoice_id']:
                    enhanced_invoice = invoice
                    break
            
            if enhanced_invoice:
                remaining = enhanced_invoice.get('remaining_amount', 0)
                overpayment_amount = remaining + 100.0  # Exceed by 100€
                
                overpayment = {
                    "amount": overpayment_amount,
                    "payment_date": datetime.now(timezone.utc).isoformat(),
                    "payment_method": "bank",
                    "notes": "Overpayment test"
                }
                
                success2, response2 = self.run_test(
                    "Payment Edge Case - Overpayment",
                    "POST",
                    f"invoices/{self.test_data['enhanced_invoice_id']}/payments",
                    400,  # Should fail with 400
                    data=overpayment
                )
                
                if success2:
                    print("   ✅ Correctly rejected overpayment")
                    print(f"   Error message: {response2.get('detail', 'N/A')}")
        
        return success1

def main():
    print("🚀 ENHANCED FEATURES TEST - ABETOILE LOCATION BACKEND")
    print("=" * 70)
    print("Testing new order and payment management features")
    print("=" * 70)
    
    tester = EnhancedFeaturesAPITester()
    
    # Setup authentication and basic data
    if not tester.setup_auth_and_data():
        print("❌ Failed to setup test environment")
        return 1
    
    # Test sequence for enhanced features
    tests = [
        ("Enhanced Order Creation", tester.test_enhanced_order_creation_with_deposit),
        ("Enhanced Invoice Creation", tester.test_invoice_creation_from_enhanced_order),
        ("Multiple Payment Management", tester.test_multiple_payment_management),
        ("Payment Deletion", tester.test_payment_deletion),
        ("Order Renewal Process", tester.test_order_renewal_process),
        ("Payment Edge Cases", tester.test_payment_edge_cases),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 ENHANCED FEATURES TEST RESULTS")
    print("=" * 70)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All enhanced features tests passed!")
        return 0
    else:
        print("⚠️  Some enhanced features tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())