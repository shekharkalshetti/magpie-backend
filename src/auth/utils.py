"""
Authentication utility functions.

Provides helper functions for:
- API key generation and hashing
- Password hashing and verification
- JWT token generation and validation
"""

import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

# Use native bcrypt if available, otherwise use simpler hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    HAS_BCRYPT = True
except Exception:
    pwd_context = None
    HAS_BCRYPT = False


def generate_api_key(length: int = 32, prefix: str = "tr") -> str:
    """
    Generate a secure random API key.

    Format: <prefix>_<random_string>

    Args:
        length: Length of random portion (default: 32)
        prefix: Prefix for the key (default: "tr")

    Returns:
        API key string (e.g., "tr_abc123...")
    """
    alphabet = string.ascii_letters + string.digits
    random_string = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}_{random_string}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The raw API key string

    Returns:
        Hex-encoded hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_key_prefix(api_key: str, length: int = 8) -> str:
    """
    Extract the prefix from an API key for identification.

    Args:
        api_key: The raw API key string
        length: Number of characters to include (default: 8)

    Returns:
        First N characters of the API key (e.g., "tr_abc12")
    """
    return api_key[:length]


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password for user invitations.

    Creates a password with mix of uppercase, lowercase, digits, and special chars.

    Args:
        length: Length of password to generate (default: 12)

    Returns:
        Random temporary password (e.g., "xK9#mL2$pQ8w")
    """
    # Mix of character types for strong password
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*"

    all_chars = uppercase + lowercase + digits + special_chars

    # Ensure at least one of each type
    password_chars = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special_chars),
    ]

    # Fill the rest randomly
    password_chars += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable patterns
    import random
    random.shuffle(password_chars)

    return "".join(password_chars)


def extract_bearer_token(authorization: str | None) -> str | None:
    """
    Extract token from Authorization header.

    Expected format: "Bearer <token>"

    Args:
        authorization: Authorization header value

    Returns:
        Extracted token or None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt if available, otherwise SHA256.

    Args:
        password: Plain text password (max 72 characters for bcrypt)

    Returns:
        Hashed password
    """
    # Ensure password is not longer than bcrypt's 72-byte limit
    password = password[:72]

    if HAS_BCRYPT and pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass

    # Fallback to SHA256-based hashing if bcrypt fails
    # This is not as secure as bcrypt but works when bcrypt is unavailable
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt.encode(), 100000)
    return f"sha256${salt}${hash_obj.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Supports both bcrypt and SHA256-based hashes.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    plain_password = plain_password[:72]  # Bcrypt limit

    # Try bcrypt first if available
    if HAS_BCRYPT and pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass

    # Fallback for SHA256-based hashes
    if hashed_password.startswith("sha256$"):
        try:
            parts = hashed_password.split('$')
            if len(parts) == 3:
                salt = parts[1]
                stored_hash = parts[2]
                hash_obj = hashlib.pbkdf2_hmac(
                    'sha256', plain_password.encode(), salt.encode(), 100000)
                return hash_obj.hex() == stored_hash
        except Exception:
            pass

    return False


def generate_jwt_token(
    user_id: str,
    email: str,
    project_id: Optional[str] = None,
    secret_key: str = "",
    expires_in_hours: int = 24,
) -> str:
    """
    Generate a JWT token for user authentication.

    Args:
        user_id: User ID
        email: User email
        project_id: Optional project ID for project-scoped tokens
        secret_key: Secret key for signing (from settings)
        expires_in_hours: Token expiration time in hours (default: 24)

    Returns:
        Encoded JWT token
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
    }

    if project_id:
        payload["project_id"] = project_id

    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_jwt_token(token: str, secret_key: str) -> Optional[dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key for verification

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None


def generate_invite_token(length: int = 32) -> str:
    """
    Generate a secure token for user invitations.

    Args:
        length: Length of random token

    Returns:
        Hex-encoded random token
    """
    return secrets.token_urlsafe(length)
