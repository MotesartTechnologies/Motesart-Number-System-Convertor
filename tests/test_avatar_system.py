"""
Test suite for Multi-user Avatar System
Features tested:
1. User registration creates unique avatar_url using DiceBear API
2. Login returns computed_avatar and display_name fields
3. Founder account detection (email: motesartproductions@gmail.com)
4. Founder gets username 'Motesart' and special avatar_url
5. Profile update endpoint
6. Avatar upload endpoint
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "test123456"
FOUNDER_EMAIL = "motesartproductions@gmail.com"
FOUNDER_PASSWORD = "founder123456"

# DiceBear API pattern
DICEBEAR_PATTERN = "https://api.dicebear.com/7.x/initials/svg"

# Motesart founder avatar
MOTESART_FOUNDER_AVATAR = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png"


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ API health check passed")


class TestUserRegistration:
    """Test user registration with avatar generation"""
    
    def test_register_new_user_gets_dicebear_avatar(self):
        """New user registration should create unique DiceBear avatar"""
        unique_email = f"test_avatar_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Avatar User",
            "email": unique_email,
            "password": "testpass123"
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Check avatar_url is set and uses DiceBear
        assert "avatar_url" in data, "avatar_url field missing"
        assert DICEBEAR_PATTERN in data["avatar_url"], f"Expected DiceBear URL, got: {data['avatar_url']}"
        
        # Check computed_avatar is returned
        assert "computed_avatar" in data, "computed_avatar field missing"
        
        # Check display_name is returned
        assert "display_name" in data, "display_name field missing"
        assert data["display_name"] == "Test Avatar User", f"Expected 'Test Avatar User', got: {data['display_name']}"
        
        # Check is_founder is false for regular user
        assert data.get("is_founder") == False, "Regular user should not be founder"
        
        print(f"✓ New user registered with DiceBear avatar: {data['avatar_url'][:60]}...")
        print(f"✓ computed_avatar: {data['computed_avatar'][:60]}...")
        print(f"✓ display_name: {data['display_name']}")
        
    def test_register_founder_gets_special_avatar(self):
        """Founder registration should get Motesart logo avatar and username"""
        # First try to login to check if founder exists
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": FOUNDER_EMAIL,
            "password": FOUNDER_PASSWORD
        })
        
        if login_response.status_code == 200:
            # Founder already exists, verify fields
            data = login_response.json()
            print(f"Founder already exists, verifying fields...")
        else:
            # Register founder
            response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Motesart Productions",
                "email": FOUNDER_EMAIL,
                "password": FOUNDER_PASSWORD
            })
            
            if response.status_code == 400 and "already registered" in response.text:
                # Try login instead
                login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                    "email": FOUNDER_EMAIL,
                    "password": FOUNDER_PASSWORD
                })
                assert login_response.status_code == 200, f"Founder login failed: {login_response.text}"
                data = login_response.json()
            else:
                assert response.status_code == 200, f"Founder registration failed: {response.text}"
                data = response.json()
        
        # Verify founder-specific fields
        assert data.get("is_founder") == True, f"Expected is_founder=True, got: {data.get('is_founder')}"
        assert data.get("username") == "Motesart", f"Expected username='Motesart', got: {data.get('username')}"
        assert data.get("avatar_url") == MOTESART_FOUNDER_AVATAR, f"Expected Motesart logo avatar, got: {data.get('avatar_url')}"
        
        # Check computed fields
        assert "computed_avatar" in data, "computed_avatar field missing"
        assert "display_name" in data, "display_name field missing"
        assert data["display_name"] == "Motesart", f"Expected display_name='Motesart', got: {data['display_name']}"
        
        print(f"✓ Founder is_founder: {data['is_founder']}")
        print(f"✓ Founder username: {data['username']}")
        print(f"✓ Founder avatar_url: {data['avatar_url'][:60]}...")
        print(f"✓ Founder display_name: {data['display_name']}")


class TestUserLogin:
    """Test login returns avatar and display_name fields"""
    
    def test_login_returns_computed_avatar_and_display_name(self):
        """Login should return computed_avatar and display_name"""
        # First ensure test user exists
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test User",
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "computed_avatar" in data, "computed_avatar field missing from login response"
        assert "display_name" in data, "display_name field missing from login response"
        assert "avatar_url" in data, "avatar_url field missing from login response"
        assert "is_founder" in data, "is_founder field missing from login response"
        
        # Verify values
        assert data["is_founder"] == False, "Test user should not be founder"
        assert data["display_name"] == "Test User", f"Expected 'Test User', got: {data['display_name']}"
        
        print(f"✓ Login returns computed_avatar: {data['computed_avatar'][:60]}...")
        print(f"✓ Login returns display_name: {data['display_name']}")
        print(f"✓ Login returns is_founder: {data['is_founder']}")
        
        return data  # Return for use in other tests
    
    def test_founder_login_returns_correct_fields(self):
        """Founder login should return is_founder=true and special avatar"""
        # Ensure founder exists
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Motesart Productions",
            "email": FOUNDER_EMAIL,
            "password": FOUNDER_PASSWORD
        })
        
        # Login as founder
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": FOUNDER_EMAIL,
            "password": FOUNDER_PASSWORD
        })
        
        assert response.status_code == 200, f"Founder login failed: {response.text}"
        data = response.json()
        
        # Verify founder fields
        assert data.get("is_founder") == True, f"Expected is_founder=True, got: {data.get('is_founder')}"
        assert data.get("username") == "Motesart", f"Expected username='Motesart', got: {data.get('username')}"
        assert data.get("display_name") == "Motesart", f"Expected display_name='Motesart', got: {data.get('display_name')}"
        
        print(f"✓ Founder login is_founder: {data['is_founder']}")
        print(f"✓ Founder login username: {data['username']}")
        print(f"✓ Founder login display_name: {data['display_name']}")


class TestAuthMe:
    """Test /api/auth/me endpoint returns avatar info"""
    
    def test_auth_me_returns_avatar_fields(self):
        """GET /api/auth/me should return computed_avatar and display_name"""
        # Login first to get session
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            # Register first
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Test User",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
        
        # Get session token from cookies
        session_token = login_response.cookies.get("session_token")
        
        if not session_token:
            # Try to extract from response if set-cookie header exists
            print("Note: session_token not in cookies, using Bearer auth")
            # Use the user_id to create a test session
            pytest.skip("Session token not available in response cookies")
        
        # Call /api/auth/me with session
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            cookies={"session_token": session_token}
        )
        
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        data = response.json()
        
        assert "computed_avatar" in data, "computed_avatar missing from /api/auth/me"
        assert "display_name" in data, "display_name missing from /api/auth/me"
        
        print(f"✓ /api/auth/me returns computed_avatar")
        print(f"✓ /api/auth/me returns display_name: {data['display_name']}")


class TestProfileUpdate:
    """Test profile update endpoint"""
    
    def test_update_profile_username(self):
        """PUT /api/auth/profile should update username"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Test User",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
        
        session_token = login_response.cookies.get("session_token")
        if not session_token:
            pytest.skip("Session token not available")
        
        # Update profile
        new_username = f"TestUser_{uuid.uuid4().hex[:4]}"
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"username": new_username},
            cookies={"session_token": session_token}
        )
        
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        data = response.json()
        
        assert data.get("username") == new_username, f"Username not updated: {data.get('username')}"
        assert data.get("display_name") == new_username, f"display_name should reflect new username"
        
        print(f"✓ Profile username updated to: {new_username}")
        print(f"✓ display_name reflects new username: {data['display_name']}")
    
    def test_non_founder_cannot_use_motesart_username(self):
        """Non-founder should not be able to use 'Motesart' username"""
        # Login as regular user
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Test user login failed")
        
        session_token = login_response.cookies.get("session_token")
        if not session_token:
            pytest.skip("Session token not available")
        
        # Try to set username to "Motesart"
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"username": "Motesart"},
            cookies={"session_token": session_token}
        )
        
        assert response.status_code == 400, f"Expected 400 for reserved username, got: {response.status_code}"
        assert "reserved" in response.text.lower(), f"Expected 'reserved' in error message: {response.text}"
        
        print("✓ Non-founder cannot use 'Motesart' username (correctly rejected)")


class TestAvatarUpload:
    """Test avatar upload endpoint"""
    
    def test_avatar_upload_endpoint_exists(self):
        """POST /api/auth/avatar should accept image uploads"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            requests.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Test User",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
        
        session_token = login_response.cookies.get("session_token")
        if not session_token:
            pytest.skip("Session token not available")
        
        # Create a simple test image (1x1 PNG)
        import base64
        # Minimal valid PNG (1x1 transparent pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        # Upload avatar
        files = {"file": ("test_avatar.png", png_data, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/auth/avatar",
            files=files,
            cookies={"session_token": session_token}
        )
        
        assert response.status_code == 200, f"Avatar upload failed: {response.text}"
        data = response.json()
        
        # Check avatar_url is updated (should be base64 data URL)
        assert "avatar_url" in data, "avatar_url missing from response"
        assert data["avatar_url"].startswith("data:image/"), f"Expected data URL, got: {data['avatar_url'][:50]}"
        
        # Check computed_avatar reflects the new avatar
        assert "computed_avatar" in data, "computed_avatar missing"
        assert data["computed_avatar"] == data["avatar_url"], "computed_avatar should match uploaded avatar"
        
        print("✓ Avatar upload successful")
        print(f"✓ avatar_url updated to data URL")
        print(f"✓ computed_avatar reflects uploaded avatar")


class TestAvatarDelete:
    """Test avatar delete endpoint"""
    
    def test_delete_avatar_reverts_to_default(self):
        """DELETE /api/auth/avatar should revert to DiceBear default"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Test user login failed")
        
        session_token = login_response.cookies.get("session_token")
        if not session_token:
            pytest.skip("Session token not available")
        
        # Delete avatar
        response = requests.delete(
            f"{BASE_URL}/api/auth/avatar",
            cookies={"session_token": session_token}
        )
        
        assert response.status_code == 200, f"Avatar delete failed: {response.text}"
        data = response.json()
        
        # Check avatar_url is reverted to DiceBear
        assert "avatar_url" in data, "avatar_url missing"
        assert DICEBEAR_PATTERN in data["avatar_url"], f"Expected DiceBear URL after delete, got: {data['avatar_url']}"
        
        print("✓ Avatar deleted, reverted to DiceBear default")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
