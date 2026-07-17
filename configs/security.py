import hashlib
import binascii
import os
import jwt
import datetime
from configs.config import settings

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2 HMAC SHA-512."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac(
        'sha512', password.encode('utf-8'), salt, 100000
    )
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against a provided password."""
    try:
        salt = stored_password[:64].encode('ascii')
        stored_hash = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac(
            'sha512', provided_password.encode('utf-8'), salt, 100000
        )
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_hash
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode a JWT access token."""
    try:
        decoded_token = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        return decoded_token if decoded_token["exp"] >= datetime.datetime.utcnow().timestamp() else None
    except jwt.PyJWTError:
        return None
