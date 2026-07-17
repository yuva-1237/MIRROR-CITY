import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configs.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    password = "secret-password"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 64
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "wrong-password") is False

def test_jwt_generation():
    payload = {"sub": "planner@mirrorcity.gov", "role": "Planner"}
    token = create_access_token(payload)
    
    assert token is not None
    decoded = decode_access_token(token)
    assert decoded["sub"] == "planner@mirrorcity.gov"
    assert decoded["role"] == "Planner"
