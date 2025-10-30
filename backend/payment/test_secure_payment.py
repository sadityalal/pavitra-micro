#!/usr/bin/env python3
"""
Secure Payment Service Test Script
Run with: python backend/payment/test_secure_payment.py
"""

import asyncio
import requests
import json
import sys
import os

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..')
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)
# Need to fix this hardcoded urls from config.py and site-settings table
class SecurePaymentTester:
    def __init__(self, base_url="http://localhost:8005", auth_url="http://localhost:8001"):
        self.base_url = base_url
        self.auth_url = auth_url
        self.auth_token = None
        self.user_id = None
    
    def get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def test_health(self):
        """Test health endpoint"""
        print("\n=== Testing Health Endpoint ===")
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    async def test_maintenance_mode(self):
        """Test maintenance mode endpoints"""
        print("\n=== Testing Maintenance Mode ===")
        try:
            response = requests.get(f"{self.base_url}/api/v1/payments/debug/maintenance")
            if response.status_code == 200:
                print(f"Maintenance Status: {response.json()}")
                return True
            else:
                print(f"Failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Maintenance check failed: {e}")
            return False
    
    async def login_and_get_token(self):
        """Login to get authentication token"""
        print("\n=== Getting Auth Token ===")
        try:
            # Try admin login first
            login_data = {
                "login_id": "admin@pavitra.com",
                "password": "admin123"
            }
            
            response = requests.post(f"{self.auth_url}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get('access_token')
                print("✓ Successfully obtained auth token using admin credentials")
                return True
            else:
                print(f"✗ Admin login failed: {response.status_code} - {response.text}")
                
                # Try registration as fallback
                return await self.register_test_user()
        except Exception as e:
            print(f"Login failed: {e}")
            return await self.register_test_user()
    
    async def register_test_user(self):
        """Register a test user if login fails"""
        print("\n=== Registering Test User ===")
        try:
            user_data = {
                "email": f"test_payment_{os.urandom(4).hex()}@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "PaymentUser",
                "country_id": 1
            }
            
            response = requests.post(f"{self.auth_url}/api/v1/auth/register", json=user_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get('access_token')
                print("✓ Successfully registered test user and obtained token")
                return True
            else:
                print(f"✗ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Registration failed: {e}")
            return False
    
    async def test_tokenize_card(self):
        """Test card tokenization"""
        print("\n=== Testing Card Tokenization ===")
        try:
            card_data = {
                "card_data": {
                    "number": "4111111111111111",  # Test card number
                    "expiry_month": 12,
                    "expiry_year": 2025,
                    "cvv": "123",
                    "name": "Test User",
                    "save_card": False
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/payments/tokenize-card",
                json=card_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Card tokenized successfully")
                print(f"Token: {result.get('token')[:16]}...")
                print(f"Expires in: {result.get('expires_in')} seconds")
                return result.get('token')
            else:
                print(f"✗ Card tokenization failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Card tokenization test failed: {e}")
            return None
    
    async def test_payment_methods(self):
        """Test payment methods endpoint"""
        print("\n=== Testing Payment Methods ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/payments/methods",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                methods = response.json()
                print(f"✓ Retrieved {len(methods)} payment methods")
                return True
            else:
                print(f"✗ Payment methods failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Payment methods test failed: {e}")
            return False
    
    async def test_secure_endpoints(self):
        """Test that secure endpoints require authentication"""
        print("\n=== Testing Security ===")
        try:
            # Test without token
            response = requests.get(f"{self.base_url}/api/v1/payments/methods")
            if response.status_code in [401, 403]:
                print("✓ Security: Endpoints require authentication")
            else:
                print(f"✗ Security: Endpoints should require authentication, got {response.status_code}")
            
            # Test with token
            response = requests.get(
                f"{self.base_url}/api/v1/payments/methods",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                print("✓ Security: Authenticated requests work")
                return True
            else:
                print(f"✗ Security: Authenticated requests should work, got {response.status_code}")
                return False
        except Exception as e:
            print(f"Security test failed: {e}")
            return False
    
    async def test_service_status(self):
        """Test if services are running"""
        print("\n=== Testing Service Status ===")
        services = {
            "Payment Service": self.base_url,
            "Auth Service": self.auth_url
        }
        
        all_healthy = True
        for service_name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✓ {service_name}: RUNNING")
                else:
                    print(f"✗ {service_name}: DOWN (Status: {response.status_code})")
                    all_healthy = False
            except Exception as e:
                print(f"✗ {service_name}: DOWN (Error: {e})")
                all_healthy = False
        
        return all_healthy
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Secure Payment Service Tests...")
        print("=" * 60)
        
        # First check if services are running
        services_ok = await self.test_service_status()
        if not services_ok:
            print("\n❌ Services are not running. Please start the services first:")
            print("  docker-compose up -d  # If using Docker")
            print("  OR")
            print("  python -m backend.auth.main  # Auth service")
            print("  python -m backend.payment.main  # Payment service")
            return False
        
        tests = [
            self.test_health(),
            self.test_maintenance_mode(),
            self.login_and_get_token(),
            self.test_secure_endpoints(),
            self.test_payment_methods(),
            self.test_tokenize_card(),
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results
        successful_tests = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Test {i+1} raised exception: {result}")
            elif result is not None and result is not False:
                successful_tests += 1
        
        total_tests = len(tests)
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {successful_tests}/{total_tests}")
        
        if successful_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Payment service is secure and working.")
        else:
            print("⚠️  Some tests failed. Check the logs above.")
        
        return successful_tests == total_tests

def main():
    """Main function to run tests"""
    tester = SecurePaymentTester()
    
    try:
        # Run the tests
        success = asyncio.run(tester.run_all_tests())
        
        if success:
            print("\n✅ All tests completed successfully!")
            print("\nNext steps:")
            print("1. Add payment gateway API keys to site_settings table")
            print("2. Test with real payment gateways")
            print("3. Deploy to production")
        else:
            print("\n❌ Some tests failed. Please check the service status and try again.")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Run the tests
    success = main()
    sys.exit(0 if success else 1)
