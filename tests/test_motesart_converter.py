"""
Motesart Number System Converter Tests
Tests the chord conversion API endpoint with various chord types and rules.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token (created during test setup)
TEST_SESSION_TOKEN = "test_session_1770776106591"


class TestHealthEndpoint:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("SUCCESS: Health endpoint returns healthy status")


class TestKeysEndpoint:
    """Test /api/keys endpoint"""
    
    def test_get_available_keys(self):
        """Test /api/keys returns list of available keys"""
        response = requests.get(f"{BASE_URL}/api/keys")
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) > 0
        
        # Check for auto-detect option
        key_values = [k["value"] for k in data["keys"]]
        assert "auto" in key_values
        assert "C" in key_values
        assert "G" in key_values
        print(f"SUCCESS: Keys endpoint returns {len(data['keys'])} keys")


class TestConvertTextEndpoint:
    """Test /api/convert/text endpoint - Core conversion logic"""
    
    @pytest.fixture
    def auth_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
        }
    
    def test_basic_chord_conversion_key_g(self, auth_headers):
        """Test basic chord conversion in key of G: G=1, D=5, Em=6m, C=4"""
        payload = {
            "text": "G  D  Em  C",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify key detection
        assert data["key"] == "1 = G"
        assert data["key_name"] == "G"
        
        # Verify chord conversions
        chords = data["all_chords"]
        symbols = [c["symbol"] for c in chords]
        
        assert "1" in symbols, "G should convert to 1"
        assert "5" in symbols, "D should convert to 5"
        assert "6m" in symbols, "Em should convert to 6m"
        assert "4" in symbols, "C should convert to 4"
        
        print("SUCCESS: Basic chord conversion in key of G works correctly")
    
    def test_minor_chords_always_marked_with_m(self, auth_headers):
        """Rule §6: Minor chords ALWAYS marked with 'm'"""
        payload = {
            "text": "Am  Bm  Cm  Dm  Em  Fm  Gm",
            "key": "C",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All minor chords should have 'm' suffix
        for chord in data["all_chords"]:
            if chord["is_minor"]:
                assert "m" in chord["symbol"], f"Minor chord {chord['original']} should have 'm' in symbol"
                assert chord["quality"] == "m", f"Minor chord {chord['original']} should have quality 'm'"
        
        print("SUCCESS: All minor chords are marked with 'm'")
    
    def test_diatonic_major_no_modifier(self, auth_headers):
        """Rule §6: Diatonic major chords have no modifier"""
        payload = {
            "text": "G  C  D",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Diatonic major chords should have no quality modifier
        for chord in data["all_chords"]:
            if chord["is_diatonic"] and not chord["is_minor"]:
                assert chord["quality"] == "", f"Diatonic major {chord['original']} should have no quality modifier"
        
        print("SUCCESS: Diatonic major chords have no modifier")
    
    def test_non_diatonic_major_gets_M(self, auth_headers):
        """Rule §6: Non-diatonic major gets 'M' (F in G = ♭7M)"""
        payload = {
            "text": "G  F  C  D",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find F chord (non-diatonic in G)
        f_chord = None
        for chord in data["all_chords"]:
            if chord["original"] == "F":
                f_chord = chord
                break
        
        assert f_chord is not None, "F chord should be found"
        assert f_chord["is_diatonic"] == False, "F should be non-diatonic in key of G"
        assert "M" in f_chord["symbol"], "Non-diatonic major F should have 'M' in symbol"
        assert "♭7" in f_chord["symbol"] or "b7" in f_chord["root"], "F in G should be ♭7"
        
        print("SUCCESS: Non-diatonic major F converts to ♭7M in key of G")
    
    def test_slash_chords_chord_bass_format(self, auth_headers):
        """Rule §7: Slash chords format is chord/bass (G/B → 1/3)"""
        payload = {
            "text": "G/B  D/F#",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check G/B → 1/3
        gb_chord = None
        df_chord = None
        for chord in data["all_chords"]:
            if chord["original"] == "G/B":
                gb_chord = chord
            elif chord["original"] == "D/F#":
                df_chord = chord
        
        assert gb_chord is not None, "G/B chord should be found"
        assert gb_chord["symbol"] == "1/3", f"G/B should convert to 1/3, got {gb_chord['symbol']}"
        assert gb_chord["root"] == "1", "G/B root should be 1"
        assert gb_chord["bass"] == "3", "G/B bass should be 3"
        
        assert df_chord is not None, "D/F# chord should be found"
        assert df_chord["symbol"] == "5/7", f"D/F# should convert to 5/7, got {df_chord['symbol']}"
        assert df_chord["root"] == "5", "D/F# root should be 5"
        assert df_chord["bass"] == "7", "D/F# bass should be 7"
        
        print("SUCCESS: Slash chords convert correctly (G/B → 1/3, D/F# → 5/7)")
    
    def test_extensions_with_superscripts(self, auth_headers):
        """Rule §4c: Extensions use superscripts (7→⁷, 9→⁹, 11→¹¹, 13→¹³)"""
        payload = {
            "text": "Cmaj7  Dm7  G7  Am7",
            "key": "C",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check conversions
        expected = {
            "Cmaj7": "1M⁷",
            "Dm7": "2m⁷",
            "G7": "5⁷",
            "Am7": "6m⁷"
        }
        
        for chord in data["all_chords"]:
            if chord["original"] in expected:
                assert chord["symbol"] == expected[chord["original"]], \
                    f"{chord['original']} should convert to {expected[chord['original']]}, got {chord['symbol']}"
        
        print("SUCCESS: Extensions convert with superscripts (Cmaj7→1M⁷, Dm7→2m⁷, G7→5⁷, Am7→6m⁷)")
    
    def test_auto_key_detection(self, auth_headers):
        """Test auto key detection from chord chart"""
        payload = {
            "text": "G  D  Em  C\nG  D  G",
            "key": "auto",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should detect G as the key
        assert data["key_name"] == "G", f"Should auto-detect key as G, got {data['key_name']}"
        assert data["key"] == "1 = G"
        
        print("SUCCESS: Auto key detection works (detected G from G D Em C progression)")
    
    def test_section_headers_detected(self, auth_headers):
        """Test section headers are detected (Verse, Chorus, etc.)"""
        payload = {
            "text": "[Verse]\nG  D  Em  C\n\n[Chorus]\nC  G  D  G",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check sections
        assert len(data["sections"]) >= 2, "Should have at least 2 sections"
        section_names = [s["name"] for s in data["sections"]]
        assert "Verse" in section_names, "Should have Verse section"
        assert "Chorus" in section_names, "Should have Chorus section"
        
        print("SUCCESS: Section headers detected (Verse, Chorus)")
    
    def test_chord_count_returned(self, auth_headers):
        """Test chord count is returned in response"""
        payload = {
            "text": "G  D  Em  C",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "chord_count" in data
        assert data["chord_count"] == 4, f"Should have 4 chords, got {data['chord_count']}"
        
        print("SUCCESS: Chord count returned correctly (4 chords)")
    
    def test_empty_input_returns_error(self, auth_headers):
        """Test empty input returns appropriate error"""
        payload = {
            "text": "",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return error or empty sections
        assert "error" in data or data["chord_count"] == 0
        
        print("SUCCESS: Empty input handled correctly")
    
    def test_chromatic_chord_roots_use_flat_sharp(self, auth_headers):
        """Rule §3: Chord roots use ♭/♯ notation for chromatic tones (not half-numbers)"""
        payload = {
            "text": "C  Db  D  Eb  E  F  F#  G  Ab  A  Bb  B",
            "key": "C",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that chromatic roots use flat/sharp notation
        for chord in data["all_chords"]:
            # Chromatic chord roots should NOT use half-numbers (½)
            if not chord["is_diatonic"]:
                assert "½" not in chord["root"], \
                    f"Chromatic chord root {chord['original']} should use ♭/♯, not half-numbers"
        
        print("SUCCESS: Chromatic chord roots use ♭/♯ notation")


class TestAuthenticationRequired:
    """Test that /api/convert/text requires authentication"""
    
    def test_convert_without_auth_returns_401(self):
        """Test conversion endpoint requires authentication"""
        payload = {
            "text": "G  D  Em  C",
            "key": "G",
            "time_signature": "4/4",
            "show_half_numbers": True
        }
        response = requests.post(
            f"{BASE_URL}/api/convert/text",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, "Should return 401 without authentication"
        print("SUCCESS: Conversion endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
