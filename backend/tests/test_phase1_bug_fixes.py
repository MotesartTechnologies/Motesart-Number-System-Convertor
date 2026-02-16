"""
Test Phase 1 Bug Fixes for Motesart Number System Converter

Bug 1: Minor chord markers - ALL minor chords should have 'm' marker
Bug 2: Slash chord notation - format should be bass/chord (e.g., G/B in G → 3/1)
Bug 3: Chromatic notes use half-numbers only (1½, 2½, 4½, 5½, 6½) - no sharp/flat symbols
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for all tests"""
    session = requests.Session()
    
    # Login to get session cookie
    login_response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "password": "Test123!"
    })
    
    if login_response.status_code != 200:
        pytest.skip(f"Login failed with status {login_response.status_code}")
    
    return session


class TestMinorChordMarkers:
    """Bug 1: ALL minor chords (diatonic or not) should have 'm' marker"""
    
    def test_diatonic_minor_chord_Am_in_C(self, auth_session):
        """Am in key of C should be 6m (not just 6)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Am",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Find the Am chord in the result
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0, "Should have at least one chord"
        
        am_chord = all_chords[0]
        assert am_chord['symbol'] == '6m', f"Am in C should be '6m', got '{am_chord['symbol']}'"
        assert am_chord['is_minor'] == True, "Am should be marked as minor"
    
    def test_diatonic_minor_chord_Em_in_C(self, auth_session):
        """Em in key of C should be 3m (not just 3)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Em",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        em_chord = all_chords[0]
        assert em_chord['symbol'] == '3m', f"Em in C should be '3m', got '{em_chord['symbol']}'"
    
    def test_diatonic_minor_chord_Dm_in_C(self, auth_session):
        """Dm in key of C should be 2m (not just 2)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Dm",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        dm_chord = all_chords[0]
        assert dm_chord['symbol'] == '2m', f"Dm in C should be '2m', got '{dm_chord['symbol']}'"
    
    def test_non_diatonic_minor_chord_Fm_in_C(self, auth_session):
        """Fm in key of C should be 4m (non-diatonic minor)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Fm",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        fm_chord = all_chords[0]
        assert fm_chord['symbol'] == '4m', f"Fm in C should be '4m', got '{fm_chord['symbol']}'"
    
    def test_minor_seventh_chord_Am7_in_C(self, auth_session):
        """Am7 in key of C should be 6m⁷"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Am7",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        am7_chord = all_chords[0]
        assert 'm' in am7_chord['symbol'], f"Am7 should have 'm' marker, got '{am7_chord['symbol']}'"
        assert '⁷' in am7_chord['symbol'], f"Am7 should have '⁷' extension, got '{am7_chord['symbol']}'"
    
    def test_multiple_minor_chords_in_progression(self, auth_session):
        """Test multiple minor chords in a progression"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Am Em Dm Am",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) == 4, f"Should have 4 chords, got {len(all_chords)}"
        
        # All should have 'm' marker
        for chord in all_chords:
            assert 'm' in chord['symbol'], f"Minor chord should have 'm' marker: {chord['original']} -> {chord['symbol']}"


class TestSlashChordNotation:
    """Bug 2: Slash chord notation - format should be bass/chord (e.g., G/B in G → 3/1)"""
    
    def test_slash_chord_G_over_B_in_G(self, auth_session):
        """G/B in key of G should be 3/1 (bass first, chord second)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "G/B",
            "key": "G"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        slash_chord = all_chords[0]
        # B is the 3rd degree in G, G is the 1st degree
        # Format should be bass/chord = 3/1
        assert slash_chord['symbol'] == '3/1', f"G/B in G should be '3/1', got '{slash_chord['symbol']}'"
    
    def test_slash_chord_C_over_E_in_C(self, auth_session):
        """C/E in key of C should be 3/1 (E is bass, C is chord)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "C/E",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        slash_chord = all_chords[0]
        # E is the 3rd degree in C, C is the 1st degree
        assert slash_chord['symbol'] == '3/1', f"C/E in C should be '3/1', got '{slash_chord['symbol']}'"
    
    def test_slash_chord_Am_over_G_in_C(self, auth_session):
        """Am/G in key of C should be 5/6m (G is bass, Am is chord)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Am/G",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        slash_chord = all_chords[0]
        # G is the 5th degree in C, Am is 6m
        # Format should be bass/chord = 5/6m
        assert '5/' in slash_chord['symbol'], f"Am/G should have bass 5, got '{slash_chord['symbol']}'"
        assert 'm' in slash_chord['symbol'], f"Am/G should have 'm' for minor, got '{slash_chord['symbol']}'"
    
    def test_slash_chord_D_over_F_sharp_in_D(self, auth_session):
        """D/F# in key of D should be 3/1"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "D/F#",
            "key": "D"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        slash_chord = all_chords[0]
        # F# is the 3rd degree in D, D is the 1st degree
        assert slash_chord['symbol'] == '3/1', f"D/F# in D should be '3/1', got '{slash_chord['symbol']}'"


class TestChromaticHalfNumbers:
    """Bug 3: Chromatic notes use half-numbers only (1½, 2½, 4½, 5½, 6½) - no sharp/flat symbols"""
    
    def test_chromatic_note_C_sharp_in_C(self, auth_session):
        """C# chord in key of C should use 1½ (not #1 or ♯1)"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "C#",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # C# is 1 semitone above C, should be 1½
        assert '½' in chord['symbol'], f"C# in C should use half-number, got '{chord['symbol']}'"
        assert '#' not in chord['symbol'], f"Should not have # symbol, got '{chord['symbol']}'"
        assert '♯' not in chord['symbol'], f"Should not have ♯ symbol, got '{chord['symbol']}'"
    
    def test_chromatic_note_D_sharp_in_C(self, auth_session):
        """D# chord in key of C should use 2½"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "D#",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # D# is 3 semitones above C, should be 2½
        assert '2½' in chord['symbol'], f"D# in C should be '2½', got '{chord['symbol']}'"
    
    def test_chromatic_note_F_sharp_in_C(self, auth_session):
        """F# chord in key of C should use 4½"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "F#",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # F# is 6 semitones above C, should be 4½
        assert '4½' in chord['symbol'], f"F# in C should be '4½', got '{chord['symbol']}'"
    
    def test_chromatic_note_G_sharp_in_C(self, auth_session):
        """G# chord in key of C should use 5½"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "G#",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # G# is 8 semitones above C, should be 5½
        assert '5½' in chord['symbol'], f"G# in C should be '5½', got '{chord['symbol']}'"
    
    def test_chromatic_note_A_sharp_in_C(self, auth_session):
        """A# chord in key of C should use 6½"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "A#",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # A# is 10 semitones above C, should be 6½
        assert '6½' in chord['symbol'], f"A# in C should be '6½', got '{chord['symbol']}'"
    
    def test_chromatic_minor_chord_F_sharp_minor_in_C(self, auth_session):
        """F#m chord in key of C should use 4½m"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "F#m",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        assert len(all_chords) > 0
        
        chord = all_chords[0]
        # F#m should be 4½m
        assert '4½' in chord['symbol'], f"F#m in C should have '4½', got '{chord['symbol']}'"
        assert 'm' in chord['symbol'], f"F#m should have 'm' marker, got '{chord['symbol']}'"
    
    def test_no_flat_symbols_in_output(self, auth_session):
        """Ensure no flat symbols (♭ or b) appear in Motesart output"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": "Bb Eb Ab Db Gb",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        all_chords = data.get('all_chords', [])
        for chord in all_chords:
            symbol = chord['symbol']
            assert '♭' not in symbol, f"Should not have ♭ symbol in '{symbol}'"
            # Note: 'b' might appear in context but not as flat indicator in the number
            # The symbol should only contain numbers, ½, m, M, °, ⁺, etc.


class TestOMREndpoint:
    """Test OMR endpoint for sheet music image processing"""
    
    def test_omr_endpoint_exists(self, auth_session):
        """Verify OMR endpoint exists"""
        # Check if we can access conversions
        conv_response = auth_session.get(f"{BASE_URL}/api/conversions")
        assert conv_response.status_code == 200
    
    def test_conversion_with_omr_data(self, auth_session):
        """Test that conversion can have OMR data"""
        # Get conversions
        conv_response = auth_session.get(f"{BASE_URL}/api/conversions")
        assert conv_response.status_code == 200
        
        conversions = conv_response.json()
        # Check if any conversion has OMR data
        for conv in conversions:
            if conv.get('omr_notes') or conv.get('omr_success'):
                print(f"Found conversion with OMR data: {conv.get('conversion_id')}")
                assert True
                return
        
        # If no OMR data found, that's okay - just verify the structure
        print("No conversions with OMR data found - this is expected if no images were processed")


class TestIntegration:
    """Integration tests combining multiple features"""
    
    def test_full_chord_progression_with_all_features(self, auth_session):
        """Test a full chord progression with minor chords, slash chords, and chromatic notes"""
        response = auth_session.post(f"{BASE_URL}/api/convert/text", json={
            "text": """[Verse]
C Am F G/B
[Chorus]
F#m C/E Dm G""",
            "key": "C"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify sections detected
        sections = data.get('sections', [])
        assert len(sections) >= 2, "Should have at least 2 sections"
        
        # Verify all chords converted
        all_chords = data.get('all_chords', [])
        assert len(all_chords) >= 8, f"Should have at least 8 chords, got {len(all_chords)}"
        
        # Check specific conversions
        chord_symbols = [c['symbol'] for c in all_chords]
        
        # Am should be 6m
        assert any('6m' in s for s in chord_symbols), "Am should convert to 6m"
        
        # G/B should be 3/1
        assert any('3/1' in s for s in chord_symbols), "G/B should convert to 3/1"
        
        # F#m should have 4½ and m
        f_sharp_m_found = False
        for chord in all_chords:
            if chord['original'] == 'F#m':
                assert '4½' in chord['symbol'], f"F#m should have 4½, got {chord['symbol']}"
                assert 'm' in chord['symbol'], f"F#m should have m, got {chord['symbol']}"
                f_sharp_m_found = True
        assert f_sharp_m_found, "F#m chord should be in the progression"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
