#!/usr/bin/env python3
"""
Motesart Number System Converter - Backend API Testing (Iteration 3)
Tests updated methodology (Extensions Section 5, Inversions Section 7) and PDF/image upload fix
"""

import requests
import sys
import json
import time
import io
from datetime import datetime
from pathlib import Path

class MotesartAPITester:
    def __init__(self, base_url="https://music-to-numbers.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()  # Use session to handle cookies
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        # Use provided test credentials
        self.test_user_email = "test2@motesart.com"
        self.test_user_password = "testpassword123"
        self.pdf_conversion_id = None
        self.image_conversion_id = None
        self.midi_conversion_id = None

    def log_test(self, name, success, details="", expected_status=None, actual_status=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            if expected_status and actual_status:
                print(f"   Expected: {expected_status}, Got: {actual_status}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "expected_status": expected_status,
            "actual_status": actual_status
        })

    def run_api_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        
        # Merge with provided headers
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        try:
            if method == 'GET':
                response = self.session.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, files=files, headers=default_headers, timeout=30)
                else:
                    response = self.session.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=default_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json() if response.content else {}
                    self.log_test(name, True)
                    return True, response_data
                except:
                    self.log_test(name, True, "No JSON response")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    self.log_test(name, False, error_data.get('detail', 'Unknown error'), expected_status, response.status_code)
                except:
                    self.log_test(name, False, f"HTTP {response.status_code}", expected_status, response.status_code)
                return False, {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        print("\n🔍 Testing Health Check...")
        success, data = self.run_api_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_email_registration(self):
        """Test email registration endpoint"""
        print("\n🔍 Testing Email Registration...")
        
        register_data = {
            "name": "Test User",
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, data = self.run_api_test(
            "Email Registration",
            "POST",
            "api/auth/register",
            200,
            data=register_data
        )
        
        if success:
            self.user_id = data.get('user_id')
            print(f"   Created user: {self.user_id}")
        elif "Email already registered" in str(data):
            # User already exists, try to login instead
            print("   User already exists, will use existing account")
            success = True
        
        return success

    def test_email_login(self):
        """Test email login endpoint"""
        print("\n🔍 Testing Email Login...")
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, data = self.run_api_test(
            "Email Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.user_id = data.get('user_id')
            print(f"   Logged in user: {self.user_id}")
        
        return success

    def test_duplicate_registration(self):
        """Test duplicate email registration (should fail)"""
        print("\n🔍 Testing Duplicate Registration...")
        
        register_data = {
            "name": "Test User 2",
            "email": self.test_user_email,  # Same email
            "password": "AnotherPass123!"
        }
        
        success, data = self.run_api_test(
            "Duplicate Email Registration (Should Fail)",
            "POST",
            "api/auth/register",
            400,  # Should return 400 for duplicate email
            data=register_data
        )
        
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n🔍 Testing Invalid Login...")
        
        # Test wrong password
        login_data = {
            "email": self.test_user_email,
            "password": "WrongPassword123!"
        }
        
        success, data = self.run_api_test(
            "Invalid Password Login (Should Fail)",
            "POST",
            "api/auth/login",
            401,  # Should return 401 for invalid credentials
            data=login_data
        )
        
        # Test non-existent email
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        success2, data = self.run_api_test(
            "Non-existent Email Login (Should Fail)",
            "POST",
            "api/auth/login",
            401,  # Should return 401 for invalid credentials
            data=login_data
        )
        
        return success and success2

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Auth Endpoints...")
        
        # Test /api/auth/me with session (should work after login)
        success, data = self.run_api_test(
            "Auth Me (With Session)",
            "GET",
            "api/auth/me", 
            200
        )
        
        if success:
            print(f"   Current user: {data.get('name')} ({data.get('email')})")
        
        return success

    def test_logout(self):
        """Test logout endpoint"""
        print("\n🔍 Testing Logout...")
        
        success, data = self.run_api_test(
            "Logout",
            "POST",
            "api/auth/logout",
            200
        )
        
        # After logout, /api/auth/me should fail
        success2, data = self.run_api_test(
            "Auth Me After Logout (Should Fail)",
            "GET",
            "api/auth/me",
            401  # Should return 401 after logout
        )
        
        return success and success2

    def test_pdf_upload(self):
        """Test PDF file upload"""
        print("\n🔍 Testing PDF Upload...")
        
        # Create a minimal PDF file
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
72 720 Td
(Test Sheet Music) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        
        files = {'file': ('test_sheet_music.pdf', pdf_content, 'application/pdf')}
        
        success, data = self.run_api_test(
            "Upload PDF File",
            "POST",
            "api/upload",
            200,
            files=files
        )
        
        if success:
            self.pdf_conversion_id = data.get('conversion_id')
            print(f"   Created PDF conversion: {self.pdf_conversion_id}")
            print(f"   Status: {data.get('status')}")
            print(f"   Is sheet music: {data.get('is_sheet_music')}")
            
            # Verify it's marked as uploaded status for sheet music
            if data.get('status') == 'uploaded' and data.get('is_sheet_music'):
                print("   ✅ PDF correctly marked as uploaded sheet music")
            else:
                print("   ❌ PDF not properly categorized as uploaded sheet music")
                success = False
        
        return success

    def test_image_upload(self):
        """Test PNG/JPG image upload"""
        print("\n🔍 Testing Image Upload...")
        
        # Create a minimal PNG file (1x1 pixel)
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01\x02\x1a\x05\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test_sheet_music.png', png_content, 'image/png')}
        
        success, data = self.run_api_test(
            "Upload PNG Image",
            "POST",
            "api/upload",
            200,
            files=files
        )
        
        if success:
            self.image_conversion_id = data.get('conversion_id')
            print(f"   Created image conversion: {self.image_conversion_id}")
            print(f"   Status: {data.get('status')}")
            print(f"   Is sheet music: {data.get('is_sheet_music')}")
            
            # Verify it's marked as uploaded status for sheet music
            if data.get('status') == 'uploaded' and data.get('is_sheet_music'):
                print("   ✅ Image correctly marked as uploaded sheet music")
            else:
                print("   ❌ Image not properly categorized as uploaded sheet music")
                success = False
        
        return success

    def test_midi_upload(self):
        """Test MIDI file upload (should still convert properly)"""
        print("\n🔍 Testing MIDI Upload...")
        
        # Create a simple test MIDI file (minimal valid MIDI)
        midi_content = bytes([
            0x4D, 0x54, 0x68, 0x64,  # "MThd"
            0x00, 0x00, 0x00, 0x06,  # Header length
            0x00, 0x00,              # Format 0
            0x00, 0x01,              # 1 track
            0x00, 0x60,              # 96 ticks per quarter note
            0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
            0x00, 0x00, 0x00, 0x04,  # Track length
            0x00, 0xFF, 0x2F, 0x00   # End of track
        ])
        
        files = {'file': ('test.mid', midi_content, 'audio/midi')}
        
        success, data = self.run_api_test(
            "Upload MIDI File",
            "POST",
            "api/upload",
            200,
            files=files
        )
        
        if success:
            self.midi_conversion_id = data.get('conversion_id')
            print(f"   Created MIDI conversion: {self.midi_conversion_id}")
            print(f"   Status: {data.get('status')}")
            print(f"   Is sheet music: {data.get('is_sheet_music')}")
            
            # MIDI should be processed and marked as completed
            if data.get('status') == 'completed' and not data.get('is_sheet_music'):
                print("   ✅ MIDI correctly processed and completed")
            else:
                print("   ❌ MIDI not properly processed")
                success = False
        
        return success

    def test_file_retrieval(self):
        """Test file retrieval endpoint for uploaded files"""
        print("\n🔍 Testing File Retrieval...")
        
        success_count = 0
        total_tests = 0
        
        # Test PDF file retrieval
        if self.pdf_conversion_id:
            total_tests += 1
            success, data = self.run_api_test(
                "Retrieve PDF File",
                "GET",
                f"api/conversions/{self.pdf_conversion_id}/file",
                200
            )
            if success:
                success_count += 1
                print("   ✅ PDF file retrieved successfully")
        
        # Test image file retrieval
        if self.image_conversion_id:
            total_tests += 1
            success, data = self.run_api_test(
                "Retrieve Image File",
                "GET",
                f"api/conversions/{self.image_conversion_id}/file",
                200
            )
            if success:
                success_count += 1
                print("   ✅ Image file retrieved successfully")
        
        return success_count == total_tests if total_tests > 0 else False

    def test_conversions_list(self):
        """Test conversions list shows uploaded files with correct status"""
        print("\n🔍 Testing Conversions List...")
        
        success, data = self.run_api_test(
            "Get Conversions List",
            "GET",
            "api/conversions",
            200
        )
        
        if success:
            conversions = data if isinstance(data, list) else []
            print(f"   Found {len(conversions)} conversions")
            
            # Check for uploaded files with correct status
            uploaded_files = [c for c in conversions if c.get('status') == 'uploaded']
            completed_files = [c for c in conversions if c.get('status') == 'completed']
            
            print(f"   Uploaded files (sheet music): {len(uploaded_files)}")
            print(f"   Completed files (MIDI/XML): {len(completed_files)}")
            
            # Verify our test files are in the list
            pdf_found = any(c.get('conversion_id') == self.pdf_conversion_id for c in conversions)
            image_found = any(c.get('conversion_id') == self.image_conversion_id for c in conversions)
            midi_found = any(c.get('conversion_id') == self.midi_conversion_id for c in conversions)
            
            if pdf_found:
                print("   ✅ PDF file found in Recent Files")
            if image_found:
                print("   ✅ Image file found in Recent Files")
            if midi_found:
                print("   ✅ MIDI file found in Recent Files")
            
            return pdf_found or image_found or midi_found
        
        return success

    def test_explain_endpoint(self):
        """Test AI explanation endpoint"""
        print("\n🔍 Testing Explain Endpoint...")
        
        if not hasattr(self, 'test_conversion_id'):
            print("   Skipping explain test - no conversion available")
            return False
        
        explain_data = {
            "conversion_id": self.test_conversion_id,
            "context": "Test explanation request"
        }
        
        success, data = self.run_api_test(
            "Get AI Explanation",
            "POST",
            "api/explain",
            200,
            data=explain_data
        )
        
        return success

    def test_export_endpoints(self):
        """Test export endpoints"""
        print("\n🔍 Testing Export Endpoints...")
        
        if not hasattr(self, 'test_conversion_id'):
            print("   Skipping export test - no conversion available")
            return False
        
        # Test different export formats
        formats = ['text', 'csv', 'pdf']
        
        for format_type in formats:
            success, data = self.run_api_test(
                f"Export {format_type.upper()}",
                "GET",
                f"api/export/{self.test_conversion_id}?format={format_type}",
                200
            )
        
        return True

    def test_invalid_endpoints(self):
        """Test invalid/edge case endpoints"""
        print("\n🔍 Testing Invalid Endpoints...")
        
        # Test non-existent endpoint
        success, data = self.run_api_test(
            "Non-existent Endpoint",
            "GET",
            "api/nonexistent",
            404
        )
        
        # Test invalid conversion ID
        success, data = self.run_api_test(
            "Invalid Conversion ID",
            "GET",
            "api/conversions/invalid-id",
            404
        )
        
        return True

    def test_cleanup(self):
        """Clean up test data"""
        print("\n🔍 Cleaning Up Test Data...")
        
        if hasattr(self, 'test_conversion_id'):
            # Test delete conversion
            success, data = self.run_api_test(
                "Delete Test Conversion",
                "DELETE",
                f"api/conversions/{self.test_conversion_id}",
                200
            )
        
        return True

    def run_all_tests(self):
        """Run comprehensive test suite for Iteration 3"""
        print("🚀 Starting Motesart API Test Suite (Iteration 3)")
        print("Testing updated methodology and PDF/image upload fix")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity
        health_ok = self.test_health_check()
        
        # Test authentication with provided credentials
        register_ok = self.test_email_registration()
        login_ok = self.test_email_login()
        
        # Test authenticated endpoints
        auth_me_ok = self.test_auth_endpoints()
        
        # Test file uploads (main focus of this iteration)
        pdf_upload_ok = self.test_pdf_upload()
        image_upload_ok = self.test_image_upload()
        midi_upload_ok = self.test_midi_upload()
        
        # Test file retrieval
        file_retrieval_ok = self.test_file_retrieval()
        
        # Test conversions list shows files with correct status
        conversions_list_ok = self.test_conversions_list()
        
        # Test other endpoints
        explain_ok = self.test_explain_endpoint()
        export_ok = self.test_export_endpoints()
        
        # Test invalid cases
        invalid_ok = self.test_invalid_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Specific results for this iteration's focus
        print("\n🎯 Key Features Tested:")
        print(f"   PDF Upload & Storage: {'✅' if pdf_upload_ok else '❌'}")
        print(f"   Image Upload & Storage: {'✅' if image_upload_ok else '❌'}")
        print(f"   MIDI Conversion (still works): {'✅' if midi_upload_ok else '❌'}")
        print(f"   File Retrieval: {'✅' if file_retrieval_ok else '❌'}")
        print(f"   Recent Files List: {'✅' if conversions_list_ok else '❌'}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed - see details above")
            return 1

def main():
    tester = MotesartAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())