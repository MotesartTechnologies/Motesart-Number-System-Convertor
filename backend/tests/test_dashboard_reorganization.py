"""
Test Dashboard Reorganization - 4 Major Fixes
Tests for:
1. Manual Entry fallback with key selector and chord input
2. PUT /api/conversions/{id}/manual endpoint
3. /api/convert/text endpoint for manual conversion
4. Export endpoints (PDF, CSV, Text)
"""
import pytest
import requests
import os
import json
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session created in MongoDB
SESSION_TOKEN = "test_session_1770780845118"
USER_ID = "test-user-1770780845118"


class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
    def test_auth_with_session_token(self):
        """Test authentication with session token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            cookies={"session_token": SESSION_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        print(f"✓ Auth working - User ID: {data['user_id']}")


class TestManualConversionEndpoint:
    """Tests for /api/convert/text endpoint - Manual chord conversion"""
    
    def test_convert_text_basic(self):
        """Test basic chord text conversion"""
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "text": "G D Em C",
                "key": "G",
                "time_signature": "4/4",
                "show_half_numbers": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert "chord_count" in data
        assert data["chord_count"] >= 4
        assert "all_chords" in data
        print(f"✓ Convert text basic - {data['chord_count']} chords converted")
    
    def test_convert_text_with_sections(self):
        """Test chord conversion with section markers"""
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "text": "[Verse]\nG D Em C\n[Chorus]\nC G Am F",
                "key": "G",
                "time_signature": "4/4",
                "show_half_numbers": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert len(data["sections"]) >= 2
        print(f"✓ Convert text with sections - {len(data['sections'])} sections detected")
    
    def test_convert_text_auto_key_detection(self):
        """Test auto key detection when key is not specified"""
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "text": "C Am F G",
                "time_signature": "4/4",
                "show_half_numbers": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "key_name" in data
        # C should be detected as key since it's most common major chord
        print(f"✓ Auto key detection - Detected key: {data['key_name']}")
    
    def test_convert_text_complex_chords(self):
        """Test conversion of complex chord symbols"""
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "text": "Cmaj7 Dm7 G7 Am7 Fmaj7 Bdim E7/G#",
                "key": "C",
                "time_signature": "4/4",
                "show_half_numbers": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chord_count"] >= 6
        print(f"✓ Complex chords - {data['chord_count']} chords converted")


class TestManualUpdateEndpoint:
    """Tests for PUT /api/conversions/{id}/manual endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup_test_conversion(self):
        """Create a test conversion for manual update tests"""
        # First upload a file to create a conversion
        import io
        
        # Create a simple test image (1x1 pixel PNG)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test_manual.png", io.BytesIO(png_data), "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            cookies={"session_token": SESSION_TOKEN},
            files=files
        )
        
        if response.status_code == 200:
            self.conversion_id = response.json().get("conversion_id")
        else:
            self.conversion_id = None
        
        yield
        
        # Cleanup - delete the test conversion
        if self.conversion_id:
            requests.delete(
                f"{BASE_URL}/api/conversions/{self.conversion_id}",
                cookies={"session_token": SESSION_TOKEN}
            )
    
    def test_manual_update_endpoint_exists(self):
        """Test that PUT /api/conversions/{id}/manual endpoint exists"""
        if not self.conversion_id:
            pytest.skip("No conversion created for test")
        
        response = requests.put(
            f"{BASE_URL}/api/conversions/{self.conversion_id}/manual",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "key_signature": "1 = G",
                "key_name": "G",
                "chords": [{"original": "G", "symbol": "1"}],
                "sections": [{"name": "Verse", "chords": [{"original": "G", "symbol": "1"}]}]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data.get("manual_entry") == True
        print(f"✓ Manual update endpoint works - Conversion {self.conversion_id} updated")
    
    def test_manual_update_with_full_data(self):
        """Test manual update with complete chord data"""
        if not self.conversion_id:
            pytest.skip("No conversion created for test")
        
        chords = [
            {"original": "G", "symbol": "1", "root": "1", "quality": ""},
            {"original": "D", "symbol": "5", "root": "5", "quality": ""},
            {"original": "Em", "symbol": "6m", "root": "6", "quality": "m"},
            {"original": "C", "symbol": "4", "root": "4", "quality": ""}
        ]
        
        sections = [
            {
                "name": "Verse",
                "chords": chords[:2],
                "progression": "1 - 5"
            },
            {
                "name": "Chorus",
                "chords": chords[2:],
                "progression": "6m - 4"
            }
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/conversions/{self.conversion_id}/manual",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "key_signature": "1 = G",
                "key_name": "G",
                "chords": chords,
                "sections": sections
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("chords", [])) == 4
        assert len(data.get("sections", [])) == 2
        print(f"✓ Manual update with full data - {len(data['chords'])} chords, {len(data['sections'])} sections")
    
    def test_manual_update_nonexistent_conversion(self):
        """Test manual update returns 404 for nonexistent conversion"""
        response = requests.put(
            f"{BASE_URL}/api/conversions/nonexistent_conv_id/manual",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "key_signature": "1 = C",
                "key_name": "C",
                "chords": [],
                "sections": []
            }
        )
        assert response.status_code == 404
        print("✓ Manual update returns 404 for nonexistent conversion")


class TestExportEndpoints:
    """Tests for export endpoints (PDF, CSV, Text)"""
    
    @pytest.fixture(autouse=True)
    def setup_test_conversion_with_chords(self):
        """Create a test conversion with chords for export tests"""
        # First convert some text to get chord data
        convert_response = requests.post(
            f"{BASE_URL}/api/convert/text",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "text": "[Verse]\nG D Em C\n[Chorus]\nC G Am F",
                "key": "G",
                "time_signature": "4/4",
                "show_half_numbers": True
            }
        )
        
        if convert_response.status_code != 200:
            self.conversion_id = None
            return
        
        chord_data = convert_response.json()
        
        # Upload a file and update with manual data
        import io
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test_export.png", io.BytesIO(png_data), "image/png")}
        upload_response = requests.post(
            f"{BASE_URL}/api/upload",
            cookies={"session_token": SESSION_TOKEN},
            files=files
        )
        
        if upload_response.status_code != 200:
            self.conversion_id = None
            return
        
        self.conversion_id = upload_response.json().get("conversion_id")
        
        # Update with manual chord data
        requests.put(
            f"{BASE_URL}/api/conversions/{self.conversion_id}/manual",
            cookies={"session_token": SESSION_TOKEN},
            json={
                "key_signature": chord_data.get("key", "1 = G"),
                "key_name": chord_data.get("key_name", "G"),
                "chords": chord_data.get("all_chords", []),
                "sections": chord_data.get("sections", [])
            }
        )
        
        yield
        
        # Cleanup
        if self.conversion_id:
            requests.delete(
                f"{BASE_URL}/api/conversions/{self.conversion_id}",
                cookies={"session_token": SESSION_TOKEN}
            )
    
    def test_export_pdf(self):
        """Test PDF export"""
        if not self.conversion_id:
            pytest.skip("No conversion created for test")
        
        response = requests.get(
            f"{BASE_URL}/api/export/{self.conversion_id}?format=pdf",
            cookies={"session_token": SESSION_TOKEN}
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 0
        print(f"✓ PDF export works - {len(response.content)} bytes")
    
    def test_export_csv(self):
        """Test CSV export"""
        if not self.conversion_id:
            pytest.skip("No conversion created for test")
        
        response = requests.get(
            f"{BASE_URL}/api/export/{self.conversion_id}?format=csv",
            cookies={"session_token": SESSION_TOKEN}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        content = response.text
        assert "Original" in content or "Symbol" in content or len(content) > 0
        print(f"✓ CSV export works - {len(content)} chars")
    
    def test_export_text(self):
        """Test Text export"""
        if not self.conversion_id:
            pytest.skip("No conversion created for test")
        
        response = requests.get(
            f"{BASE_URL}/api/export/{self.conversion_id}?format=text",
            cookies={"session_token": SESSION_TOKEN}
        )
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        content = response.text
        assert len(content) > 0
        print(f"✓ Text export works - {len(content)} chars")


class TestAvailableKeys:
    """Test /api/keys endpoint for key selector dropdown"""
    
    def test_get_available_keys(self):
        """Test that available keys endpoint returns all keys"""
        response = requests.get(f"{BASE_URL}/api/keys")
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        keys = data["keys"]
        
        # Should have auto-detect + 12 keys
        assert len(keys) >= 12
        
        # Check for common keys
        key_values = [k["value"] for k in keys]
        assert "C" in key_values
        assert "G" in key_values
        assert "D" in key_values
        assert "A" in key_values
        print(f"✓ Available keys endpoint - {len(keys)} keys returned")


class TestConversionsEndpoint:
    """Test conversions list endpoint"""
    
    def test_get_conversions_list(self):
        """Test getting list of conversions"""
        response = requests.get(
            f"{BASE_URL}/api/conversions",
            cookies={"session_token": SESSION_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Conversions list - {len(data)} conversions found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
