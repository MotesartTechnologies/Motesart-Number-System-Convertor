"""
Test Lead Sheet View and Manual Entry Live Preview Features
Tests for iteration 9 - Lead Sheet View (Format B) with live preview functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthFlow:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "test123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["email"] == "testuser@example.com"
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestConversionAPI:
    """Conversion API tests for Motesart Number System"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get session cookie"""
        self.session = requests.Session()
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "test123456"
        })
        assert response.status_code == 200
        
    def test_convert_text_basic(self):
        """Test basic chord conversion"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "G Am C D",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "1 = G"
        assert data["chord_count"] == 4
        
    def test_convert_text_key_of_ab(self):
        """Test conversion in key of Ab - Db=4, Fm=6m, Ab=1, Eb=5"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Db Fm Ab Eb",
            "key": "Ab",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "1 = Ab"
        assert data["key_name"] == "Ab"
        
        # Verify correct Motesart numbers
        all_chords = data["all_chords"]
        symbols = [c["symbol"] for c in all_chords]
        assert "4" in symbols  # Db = 4
        assert "6m" in symbols  # Fm = 6m
        assert "1" in symbols  # Ab = 1
        assert "5" in symbols  # Eb = 5
        
    def test_convert_text_with_sections(self):
        """Test conversion with section labels [Verse], [Chorus]"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": """[Verse]
Db   Fm   Db   Ab
You saw me, You loved me

[Chorus]
Ab   Db   Eb   Fm
Lord You reign forever""",
            "key": "Ab",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify sections are detected
        sections = data["sections"]
        assert len(sections) == 2
        
        # Verify section names
        section_names = [s["name"] for s in sections]
        assert "Verse" in section_names
        assert "Chorus" in section_names
        
        # Verify Verse section has correct chords
        verse_section = next(s for s in sections if s["name"] == "Verse")
        assert len(verse_section["chords"]) == 4
        
        # Verify Chorus section has correct chords
        chorus_section = next(s for s in sections if s["name"] == "Chorus")
        assert len(chorus_section["chords"]) == 4
        
    def test_convert_text_with_lyrics(self):
        """Test that lyrics are preserved in conversion"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": """[Verse]
G    D    Em   C
Amazing grace how sweet the sound""",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify lyrics are preserved
        sections = data["sections"]
        assert len(sections) > 0
        
        verse = sections[0]
        lines = verse["lines"]
        
        # Should have chord line and lyric line
        chord_lines = [l for l in lines if l["type"] == "chord_line"]
        lyric_lines = [l for l in lines if l["type"] == "lyric_line"]
        
        assert len(chord_lines) > 0
        assert len(lyric_lines) > 0
        
        # Verify lyric content
        lyric_text = lyric_lines[0]["original"]
        assert "Amazing grace" in lyric_text
        
    def test_convert_text_complex_chords(self):
        """Test conversion of complex chords (maj7, dim, sus)"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Cmaj7 Dm7 G7 Am7",
            "key": "C",
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify complex chords are converted
        all_chords = data["all_chords"]
        assert len(all_chords) == 4
        
        # Check for 7th chord extensions
        has_seventh = any("⁷" in c["symbol"] or "7" in c["extensions"] for c in all_chords)
        assert has_seventh
        
    def test_convert_text_auto_key_detection(self):
        """Test auto key detection when no key specified"""
        response = self.session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "C G Am F",
            "key": None,  # Auto-detect
            "time_signature": "4/4",
            "show_half_numbers": True
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should detect C as the key
        assert data["key_name"] == "C"
        

class TestKeysAPI:
    """Test keys endpoint"""
    
    def test_get_keys(self):
        """Test that keys endpoint returns all available keys"""
        response = requests.get(f"{BASE_URL}/api/keys")
        assert response.status_code == 200
        data = response.json()
        
        assert "keys" in data
        keys = data["keys"]
        
        # Should have at least 12 keys plus auto-detect
        assert len(keys) >= 12
        
        # Verify auto-detect option exists
        key_values = [k["value"] for k in keys]
        assert "auto" in key_values
        assert "C" in key_values
        assert "Ab" in key_values


class TestHealthAPI:
    """Test health endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestConversionsAPI:
    """Test conversions list endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get session cookie"""
        self.session = requests.Session()
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "test123456"
        })
        assert response.status_code == 200
        
    def test_get_conversions_list(self):
        """Test getting list of conversions"""
        response = self.session.get(f"{BASE_URL}/api/conversions")
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
