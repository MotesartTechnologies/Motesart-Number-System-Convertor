"""
Test suite for Motesart OMR Pipeline
Tests the critical bug fix: Gemini OMR pipeline triggered on file upload
"""
import pytest
import requests
import os
import io
from PIL import Image, ImageDraw

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://chord-converter.preview.emergentagent.com')

# Test session token - will be created in setup
SESSION_TOKEN = None
USER_ID = None


@pytest.fixture(scope="module")
def auth_session():
    """Create test user and session for authenticated requests"""
    import subprocess
    import re
    
    # Create test user and session via mongosh
    result = subprocess.run([
        'mongosh', '--eval', '''
        use('test_database');
        var userId = 'test-omr-pytest-' + Date.now();
        var sessionToken = 'pytest_session_' + Date.now();
        
        var existingUser = db.users.findOne({email: 'pytest_omr@example.com'});
        if (existingUser) {
            userId = existingUser.user_id;
            db.user_sessions.deleteMany({user_id: userId});
        } else {
            db.users.insertOne({
                user_id: userId,
                email: 'pytest_omr@example.com',
                name: 'Pytest OMR User',
                auth_type: 'email',
                created_at: new Date()
            });
        }
        
        db.user_sessions.insertOne({
            user_id: userId,
            session_token: sessionToken,
            expires_at: new Date(Date.now() + 7*24*60*60*1000),
            created_at: new Date()
        });
        print('SESSION:' + sessionToken);
        print('USERID:' + userId);
        '''
    ], capture_output=True, text=True)
    
    output = result.stdout
    session_match = re.search(r'SESSION:(\S+)', output)
    user_match = re.search(r'USERID:(\S+)', output)
    
    if session_match and user_match:
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {session_match.group(1)}",
            "Content-Type": "application/json"
        })
        return {
            "session": session,
            "token": session_match.group(1),
            "user_id": user_match.group(1)
        }
    
    pytest.skip("Could not create test session")


def create_test_image():
    """Create a simple test image that looks like sheet music"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw staff lines
    for i in range(5):
        y = 50 + i * 15
        draw.line([(20, y), (380, y)], fill='black', width=1)
    
    # Draw some note-like circles
    notes = [(60, 65), (100, 80), (140, 65), (180, 95), (220, 80)]
    for x, y in notes:
        draw.ellipse([x-8, y-6, x+8, y+6], fill='black')
    
    # Add text
    draw.text((150, 150), "Test Music", fill='black')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_auth_me_returns_user(self, auth_session):
        """Test /api/auth/me returns user data"""
        response = auth_session["session"].get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == "pytest_omr@example.com"
    
    def test_auth_me_without_token_returns_401(self):
        """Test /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestOMRPipeline:
    """Test the critical OMR pipeline functionality"""
    
    def test_upload_triggers_omr_pipeline(self, auth_session):
        """
        CRITICAL TEST: Verify upload triggers Gemini OMR pipeline
        This was the bug: old extraction functions returned 'No Chords Detected'
        Fix: upload now calls process_sheet_music_omr directly
        """
        # Create test image
        img_bytes = create_test_image()
        
        # Upload file
        files = {"file": ("test_omr.png", img_bytes, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_session['token']}"},
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        # CRITICAL ASSERTIONS - These verify the bug is fixed
        assert data.get("status") == "completed", f"Status should be 'completed', got: {data.get('status')}"
        assert data.get("omr_success") == True, f"OMR should succeed, got: {data.get('omr_success')}"
        assert data.get("omr_processed") == True, "OMR should be processed"
        
        # Verify notes were extracted (not 'No Chords Detected')
        omr_notes = data.get("omr_notes", [])
        assert len(omr_notes) > 0, "OMR should extract notes"
        
        # Verify analysis method is Gemini
        assert data.get("analysis_method") == "gemini-2.5-flash", f"Should use Gemini, got: {data.get('analysis_method')}"
        
        # Verify key signature is set
        assert data.get("key_signature") is not None, "Key signature should be set"
        
        print(f"✓ Upload triggered OMR pipeline successfully")
        print(f"  - Status: {data.get('status')}")
        print(f"  - OMR Success: {data.get('omr_success')}")
        print(f"  - Notes extracted: {len(omr_notes)}")
        print(f"  - Analysis method: {data.get('analysis_method')}")
    
    def test_upload_status_not_uploaded(self, auth_session):
        """
        Verify status is 'completed' after upload, NOT 'uploaded'
        The old bug left status as 'uploaded' requiring manual entry
        """
        img_bytes = create_test_image()
        files = {"file": ("test_status.png", img_bytes, "image/png")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_session['token']}"},
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Status should NOT be 'uploaded' - that was the bug
        assert data.get("status") != "uploaded", "Status should not be 'uploaded' after OMR processing"
        assert data.get("status") == "completed", f"Status should be 'completed', got: {data.get('status')}"
    
    def test_omr_notes_have_correct_structure(self, auth_session):
        """Verify OMR notes have the expected structure"""
        img_bytes = create_test_image()
        files = {"file": ("test_structure.png", img_bytes, "image/png")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_session['token']}"},
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        
        omr_notes = data.get("omr_notes", [])
        if len(omr_notes) > 0:
            note = omr_notes[0]
            # Check note structure
            assert "pitch" in note or "motesart" in note, "Note should have pitch or motesart field"
            print(f"✓ Note structure verified: {list(note.keys())}")


class TestConversionEndpoints:
    """Test conversion-related endpoints"""
    
    def test_get_conversions_list(self, auth_session):
        """Test getting list of conversions"""
        response = auth_session["session"].get(f"{BASE_URL}/api/conversions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_single_conversion(self, auth_session):
        """Test getting a single conversion by ID"""
        # First upload a file
        img_bytes = create_test_image()
        files = {"file": ("test_single.png", img_bytes, "image/png")}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_session['token']}"},
            files=files
        )
        
        assert upload_response.status_code == 200
        conversion_id = upload_response.json().get("conversion_id")
        
        # Get the conversion
        response = auth_session["session"].get(f"{BASE_URL}/api/conversions/{conversion_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("conversion_id") == conversion_id
        assert data.get("status") == "completed"
        assert data.get("omr_success") == True


class TestTextConversion:
    """Test text/chord conversion endpoints"""
    
    def test_convert_text_endpoint(self, auth_session):
        """Test the /api/convert/text endpoint"""
        payload = {
            "text": "[Verse]\nG Am C D\nHello world",
            "key": "G",
            "time_signature": "4/4"
        }
        
        response = auth_session["session"].post(
            f"{BASE_URL}/api/convert/text",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert "key_name" in data
        assert data.get("key_name") == "G"
    
    def test_minor_chord_conversion(self, auth_session):
        """Test minor chords get 'm' marker (Bug #1 fix)"""
        payload = {
            "text": "Am Em Dm",
            "key": "C",
            "time_signature": "4/4"
        }
        
        response = auth_session["session"].post(
            f"{BASE_URL}/api/convert/text",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get("all_chords", [])
        for chord in all_chords:
            if chord.get("is_minor"):
                assert "m" in chord.get("symbol", ""), f"Minor chord should have 'm': {chord}"


class TestHealthAndStatus:
    """Test health and status endpoints"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_keys_endpoint(self):
        """Test /api/keys returns available keys"""
        response = requests.get(f"{BASE_URL}/api/keys")
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
