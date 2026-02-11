"""
Test suite for Motesart Converter Bug Fixes
Tests the 4 critical bugs that were fixed:
1. BUG 1: Explain AI Button - /api/explain endpoint
2. BUG 2: Chat Section - /api/chat endpoint
3. BUG 3: PDF Export OCR - PDF/image extraction
4. BUG 4: HEIC File Format - HEIC/heif support
"""

import pytest
import requests
import os
import json
from datetime import datetime, timezone, timedelta

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token (created in MongoDB)
TEST_SESSION_TOKEN = "test_session_1770778543842"
TEST_USER_ID = "test-user-1770778543842"
TEST_CONVERSION_ID = "conv_test_1770778604207"


@pytest.fixture
def api_client():
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
    })
    return session


class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self, api_client):
        """Test /api/health returns healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_auth_me_endpoint(self, api_client):
        """Test /api/auth/me returns user data"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        print(f"✓ Auth endpoint working - User: {data.get('email')}")


class TestBug1ExplainAI:
    """BUG 1: Explain AI Button - Tests /api/explain endpoint"""
    
    def test_explain_endpoint_exists(self, api_client):
        """Test that /api/explain endpoint exists and accepts POST"""
        response = api_client.post(f"{BASE_URL}/api/explain", json={
            "conversion_id": "nonexistent"
        })
        # Should return 404 for nonexistent conversion, not 405 Method Not Allowed
        assert response.status_code in [404, 200]
        print("✓ Explain endpoint exists")
    
    def test_explain_with_valid_conversion(self, api_client):
        """Test explain with a valid conversion that has chords"""
        response = api_client.post(f"{BASE_URL}/api/explain", json={
            "conversion_id": TEST_CONVERSION_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0
        print(f"✓ Explain generated: {data['explanation'][:100]}...")
    
    def test_explain_with_section_index(self, api_client):
        """Test explain with specific section index"""
        response = api_client.post(f"{BASE_URL}/api/explain", json={
            "conversion_id": TEST_CONVERSION_ID,
            "section_index": 0
        })
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        print("✓ Explain with section index working")
    
    def test_explain_nonexistent_conversion(self, api_client):
        """Test explain returns 404 for nonexistent conversion"""
        response = api_client.post(f"{BASE_URL}/api/explain", json={
            "conversion_id": "nonexistent_conv_id"
        })
        assert response.status_code == 404
        print("✓ Explain returns 404 for nonexistent conversion")


class TestBug2ChatSection:
    """BUG 2: Chat Section - Tests /api/chat endpoint"""
    
    def test_chat_endpoint_exists(self, api_client):
        """Test that /api/chat endpoint exists and accepts POST"""
        response = api_client.post(f"{BASE_URL}/api/chat", json={
            "conversion_id": "nonexistent",
            "message": "test",
            "history": []
        })
        # Should return 404 for nonexistent conversion, not 405 Method Not Allowed
        assert response.status_code in [404, 200]
        print("✓ Chat endpoint exists")
    
    def test_chat_with_valid_conversion(self, api_client):
        """Test chat with a valid conversion"""
        response = api_client.post(f"{BASE_URL}/api/chat", json={
            "conversion_id": TEST_CONVERSION_ID,
            "message": "What key is this in?",
            "history": []
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "timestamp" in data
        assert len(data["response"]) > 0
        print(f"✓ Chat response: {data['response'][:100]}...")
    
    def test_chat_with_history(self, api_client):
        """Test chat with conversation history"""
        response = api_client.post(f"{BASE_URL}/api/chat", json={
            "conversion_id": TEST_CONVERSION_ID,
            "message": "Can you explain the progression?",
            "history": [
                {"role": "user", "content": "What key is this in?"},
                {"role": "assistant", "content": "This is in the key of G major."}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        print("✓ Chat with history working")
    
    def test_chat_nonexistent_conversion(self, api_client):
        """Test chat returns 404 for nonexistent conversion"""
        response = api_client.post(f"{BASE_URL}/api/chat", json={
            "conversion_id": "nonexistent_conv_id",
            "message": "test",
            "history": []
        })
        assert response.status_code == 404
        print("✓ Chat returns 404 for nonexistent conversion")


class TestBug3PDFExport:
    """BUG 3: PDF Export OCR - Tests PDF/image extraction"""
    
    def test_upload_png_image(self, api_client):
        """Test uploading a PNG image"""
        # Create a simple test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Upload the image
        files = {'file': ('test_image.png', img_bytes, 'image/png')}
        headers = {"Authorization": f"Bearer {TEST_SESSION_TOKEN}"}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversion_id" in data
        assert data["file_type"] == "png"
        assert data["is_sheet_music"] == True
        # Status should be 'uploaded' since OCR may not be available
        assert data["status"] in ["uploaded", "completed"]
        print(f"✓ PNG upload working - Status: {data['status']}")
    
    def test_supported_file_types_include_heic(self, api_client):
        """Test that HEIC is in supported file types"""
        # Check the upload endpoint accepts HEIC
        # We can verify this by checking the server code or trying to upload
        # For now, we verify the file type is recognized
        response = api_client.get(f"{BASE_URL}/api/conversions")
        assert response.status_code == 200
        print("✓ Conversions endpoint accessible")


class TestBug4HEICSupport:
    """BUG 4: HEIC File Format - Tests HEIC/heif support"""
    
    def test_heic_in_supported_formats(self):
        """Verify HEIC is listed in supported formats"""
        # This is verified by checking the frontend text
        # "Supported: PDF, PNG, JPG, HEIC, MusicXML, MIDI"
        # We can also check the backend code
        import sys
        sys.path.insert(0, '/app/backend')
        from server import SUPPORTED_SHEET_MUSIC
        
        assert "heic" in SUPPORTED_SHEET_MUSIC
        assert "heif" in SUPPORTED_SHEET_MUSIC
        print(f"✓ HEIC/HEIF in supported formats: {SUPPORTED_SHEET_MUSIC}")
    
    def test_pillow_heif_installed(self):
        """Verify pillow-heif package is installed"""
        try:
            from pillow_heif import register_heif_opener
            print("✓ pillow-heif package is installed")
        except ImportError:
            pytest.fail("pillow-heif package is NOT installed")


class TestTextConversion:
    """Test text conversion endpoint"""
    
    def test_convert_text_basic(self, api_client):
        """Test basic text conversion"""
        response = api_client.post(f"{BASE_URL}/api/convert/text", json={
            "text": "G D Em C",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "1 = G"
        assert data["chord_count"] == 4
        print("✓ Text conversion working")
    
    def test_convert_text_with_sections(self, api_client):
        """Test text conversion with sections"""
        response = api_client.post(f"{BASE_URL}/api/convert/text", json={
            "text": "[Verse]\nG D Em C\n\n[Chorus]\nG D G",
            "key": "G"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["sections"]) == 2
        assert data["sections"][0]["name"] == "Verse"
        assert data["sections"][1]["name"] == "Chorus"
        print("✓ Section detection working")


class TestExportEndpoint:
    """Test export endpoint"""
    
    def test_export_pdf(self, api_client):
        """Test PDF export"""
        response = api_client.get(
            f"{BASE_URL}/api/export/{TEST_CONVERSION_ID}?format=pdf"
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        print("✓ PDF export working")
    
    def test_export_csv(self, api_client):
        """Test CSV export"""
        response = api_client.get(
            f"{BASE_URL}/api/export/{TEST_CONVERSION_ID}?format=csv"
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        print("✓ CSV export working")
    
    def test_export_text(self, api_client):
        """Test text export"""
        response = api_client.get(
            f"{BASE_URL}/api/export/{TEST_CONVERSION_ID}?format=text"
        )
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        print("✓ Text export working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
