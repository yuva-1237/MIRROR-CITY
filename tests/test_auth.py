import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configs.security import hash_password, verify_password, create_access_token, decode_access_token
from configs.config import Settings, validate_settings
from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_password_hashing_bcrypt():
    password = "secret-password-123"
    hashed = hash_password(password)
    
    assert hashed != password
    # Bcrypt standard identifier
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "wrong-password") is False

def test_jwt_generation():
    payload = {"sub": "planner@mirrorcity.gov", "role": "Planner"}
    token = create_access_token(payload)
    
    assert token is not None
    decoded = decode_access_token(token)
    assert decoded["sub"] == "planner@mirrorcity.gov"
    assert decoded["role"] == "Planner"

def test_jwt_secret_required_validation():
    # Attempting to validate settings with an empty secret must fail fast
    bad_settings = Settings()
    bad_settings.JWT_SECRET = ""
    with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR: JWT_SECRET environment variable is required"):
        validate_settings(bad_settings)
        
    # Attempting to validate with insecure legacy development secret must fail fast
    insecure_settings = Settings()
    insecure_settings.JWT_SECRET = "super-secret-key-for-mirror-city-12345"
    with pytest.raises(ValueError, match="Insecure legacy development secret detected"):
        validate_settings(insecure_settings)

def test_force_password_change_flow():
    # Register a new user
    import uuid
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@mirrorcity.gov"
    reg_resp = client.post("/api/auth/register", json={
        "email": test_email,
        "password": "temporary-password-123",
        "role": "Citizen"
    })
    assert reg_resp.status_code == 200

    # Log in
    login_resp = client.post("/api/auth/login", data={
        "username": test_email,
        "password": "temporary-password-123"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert "must_change_password" in login_data

    # Change password
    change_resp = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "temporary-password-123",
            "new_password": "brand-new-secure-password"
        }
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["must_change_password"] is False

    # Verify old password fails
    bad_login = client.post("/api/auth/login", data={
        "username": test_email,
        "password": "temporary-password-123"
    })
    assert bad_login.status_code == 401

    # Verify new password succeeds
    good_login = client.post("/api/auth/login", data={
        "username": test_email,
        "password": "brand-new-secure-password"
    })
    assert good_login.status_code == 200

