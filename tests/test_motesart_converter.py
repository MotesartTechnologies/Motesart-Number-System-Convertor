"""
Motesart Number Converter - Comprehensive Backend Tests
Tests: Auth (register/login), File Upload (MIDI/PDF), Conversion, Export (PDF/CSV/Text)
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://music-numbers.preview.emergentagent.com')

# Test user credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "test123456"
TEST_NAME = "Test User"

# Existing test user (from review_request)
EXISTING_EMAIL = "test@test.com"
EXISTING_PASSWORD = "test123"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")


class TestAuthRegistration:
    """User registration tests"""
    
    def test_register_new_user(self):
        """Test user registration with email/password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": TEST_NAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "user_id" in data
        assert data["email"] == TEST_EMAIL
        assert data["name"] == TEST_NAME
        assert "password_hash" not in data  # Should not expose password hash
        print(f"✓ User registration passed - user_id: {data['user_id']}")
        return data
    
    def test_register_duplicate_email(self):
        """Test registration with existing email fails"""
        # First register
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "Duplicate User",
                "email": f"dup_{uuid.uuid4().hex[:8]}@test.com",
                "password": "test123"
            }
        )
        # Try to register again with same email - should fail
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "Duplicate User 2",
                "email": EXISTING_EMAIL,  # Use existing test user
                "password": "different123"
            }
        )
        assert response.status_code == 400
        print("✓ Duplicate email registration correctly rejected")


class TestAuthLogin:
    """User login tests"""
    
    def test_login_with_valid_credentials(self):
        """Test login with valid email/password"""
        # First ensure user exists
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "Login Test",
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "user_id" in data
        assert data["email"] == EXISTING_EMAIL
        assert "password_hash" not in data
        print(f"✓ Login passed - user_id: {data['user_id']}")
        return response
    
    def test_login_with_invalid_password(self):
        """Test login with wrong password fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        print("✓ Invalid password correctly rejected")
    
    def test_login_with_nonexistent_email(self):
        """Test login with non-existent email fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "anypassword"
            }
        )
        assert response.status_code == 401
        print("✓ Non-existent email correctly rejected")


class TestFileUpload:
    """File upload and conversion tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        # Login to get session cookie
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        if response.status_code != 200:
            # Register first if user doesn't exist
            session.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "name": "Test User",
                    "email": EXISTING_EMAIL,
                    "password": EXISTING_PASSWORD
                }
            )
            session.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": EXISTING_EMAIL,
                    "password": EXISTING_PASSWORD
                }
            )
        return session
    
    def test_upload_midi_file(self, auth_session):
        """Test MIDI file upload - should convert instantly"""
        midi_path = "/tmp/test_c_major.mid"
        
        with open(midi_path, "rb") as f:
            response = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("test_c_major.mid", f, "audio/midi")}
            )
        
        assert response.status_code == 200, f"MIDI upload failed: {response.text}"
        data = response.json()
        
        # Verify conversion data
        assert data["status"] == "completed", f"Expected 'completed' status, got: {data['status']}"
        assert data["file_type"] == "mid"
        assert "conversion_id" in data
        assert "key_signature" in data
        assert "notes" in data or "chords" in data or "sections" in data
        
        print(f"✓ MIDI upload passed - status: {data['status']}, key: {data.get('key_signature')}")
        return data
    
    def test_upload_pdf_file_phase2_messaging(self, auth_session):
        """Test PDF file upload - should show Phase 2 messaging (OMR not active)"""
        pdf_path = "/tmp/test_sheet_music.pdf"
        
        with open(pdf_path, "rb") as f:
            response = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("test_sheet_music.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200, f"PDF upload failed: {response.text}"
        data = response.json()
        
        # Verify Phase 2 status
        assert data["status"] == "uploaded", f"Expected 'uploaded' status for PDF, got: {data['status']}"
        assert data["is_sheet_music"] == True
        assert data["file_type"] == "pdf"
        assert "Phase 2" in data.get("status_message", "") or "OMR" in data.get("status_message", "")
        
        print(f"✓ PDF upload passed - status: {data['status']}, message: {data.get('status_message', '')[:50]}")
        return data
    
    def test_upload_unsupported_file(self, auth_session):
        """Test unsupported file type is rejected"""
        # Create a fake .exe file
        response = auth_session.post(
            f"{BASE_URL}/api/upload",
            files={"file": ("test.exe", b"fake content", "application/octet-stream")}
        )
        
        assert response.status_code == 400
        print("✓ Unsupported file type correctly rejected")


class TestConversions:
    """Conversion retrieval and management tests"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        return session
    
    def test_get_conversions_list(self, auth_session):
        """Test getting user's conversion history"""
        response = auth_session.get(f"{BASE_URL}/api/conversions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get conversions passed - found {len(data)} conversions")
        return data
    
    def test_get_single_conversion(self, auth_session):
        """Test getting a specific conversion"""
        # First get list
        list_response = auth_session.get(f"{BASE_URL}/api/conversions")
        conversions = list_response.json()
        
        if len(conversions) > 0:
            conv_id = conversions[0]["conversion_id"]
            response = auth_session.get(f"{BASE_URL}/api/conversions/{conv_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversion_id"] == conv_id
            print(f"✓ Get single conversion passed - id: {conv_id}")
        else:
            print("⚠ No conversions to test single retrieval")


class TestExport:
    """Export functionality tests - PDF, CSV, Text"""
    
    @pytest.fixture
    def auth_session_with_conversion(self):
        """Get authenticated session and ensure a completed conversion exists"""
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        
        # Upload MIDI to get a completed conversion
        midi_path = "/tmp/test_c_major.mid"
        with open(midi_path, "rb") as f:
            response = session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("export_test.mid", f, "audio/midi")}
            )
        
        if response.status_code == 200:
            conversion = response.json()
            return session, conversion["conversion_id"]
        
        # Fallback: get existing conversion
        list_response = session.get(f"{BASE_URL}/api/conversions")
        conversions = list_response.json()
        completed = [c for c in conversions if c.get("status") == "completed"]
        if completed:
            return session, completed[0]["conversion_id"]
        
        pytest.skip("No completed conversion available for export test")
    
    def test_export_pdf_with_unicode(self, auth_session_with_conversion):
        """Test PDF export works without Unicode errors (DejaVu font fix)"""
        session, conv_id = auth_session_with_conversion
        
        response = session.get(f"{BASE_URL}/api/export/{conv_id}?format=pdf")
        
        assert response.status_code == 200, f"PDF export failed: {response.status_code} - {response.text[:200]}"
        assert response.headers.get("content-type") == "application/pdf"
        
        # Verify it's a valid PDF (starts with %PDF)
        content = response.content
        assert content[:4] == b"%PDF", "Response is not a valid PDF"
        assert len(content) > 100, "PDF content too small"
        
        print(f"✓ PDF export passed - size: {len(content)} bytes")
    
    def test_export_csv(self, auth_session_with_conversion):
        """Test CSV export with branded header"""
        session, conv_id = auth_session_with_conversion
        
        response = session.get(f"{BASE_URL}/api/export/{conv_id}?format=csv")
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        
        content = response.text
        assert "Motesart" in content, "CSV should contain Motesart branding"
        assert "Key" in content
        
        print(f"✓ CSV export passed - contains branding")
    
    def test_export_text(self, auth_session_with_conversion):
        """Test Text export with branded template and legend"""
        session, conv_id = auth_session_with_conversion
        
        response = session.get(f"{BASE_URL}/api/export/{conv_id}?format=text")
        
        assert response.status_code == 200
        
        content = response.text
        assert "Motesart" in content, "Text should contain Motesart branding"
        # Check for legend symbols
        assert "½" in content or "chromatic" in content.lower(), "Text should contain legend"
        
        print(f"✓ Text export passed - contains branding and legend")


class TestDashboardStateReset:
    """Test dashboard state resets when switching files"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        return session
    
    def test_multiple_uploads_have_separate_state(self, auth_session):
        """Test that uploading multiple files creates separate conversions"""
        midi_path = "/tmp/test_c_major.mid"
        
        # Upload first file
        with open(midi_path, "rb") as f:
            response1 = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("file1.mid", f, "audio/midi")}
            )
        
        # Upload second file
        with open(midi_path, "rb") as f:
            response2 = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("file2.mid", f, "audio/midi")}
            )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Verify they have different conversion IDs
        assert data1["conversion_id"] != data2["conversion_id"]
        
        print(f"✓ Multiple uploads create separate conversions")


class TestStatusBadges:
    """Test status badges show correctly"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXISTING_EMAIL,
                "password": EXISTING_PASSWORD
            }
        )
        return session
    
    def test_midi_shows_converted_status(self, auth_session):
        """Test MIDI file shows 'completed' status"""
        midi_path = "/tmp/test_c_major.mid"
        
        with open(midi_path, "rb") as f:
            response = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("status_test.mid", f, "audio/midi")}
            )
        
        data = response.json()
        assert data["status"] == "completed"
        print(f"✓ MIDI shows 'completed' status")
    
    def test_pdf_shows_uploaded_phase2_status(self, auth_session):
        """Test PDF file shows 'uploaded' status with Phase 2 message"""
        pdf_path = "/tmp/test_sheet_music.pdf"
        
        with open(pdf_path, "rb") as f:
            response = auth_session.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("status_test.pdf", f, "application/pdf")}
            )
        
        data = response.json()
        assert data["status"] == "uploaded"
        assert "Phase 2" in data.get("status_message", "") or "OMR" in data.get("status_message", "")
        print(f"✓ PDF shows 'uploaded' status with Phase 2 message")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
