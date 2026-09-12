"""Unit tests for cryptographic password hashing and JWT token operations."""

from datetime import timedelta
import time
import unittest
import uuid

from industrial_oracle.core.exceptions import AuthenticationException
from industrial_oracle.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestSecurityAuth(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        password = "EnterpriseSecurePassword123!"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$pbkdf2-sha256$"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword123!", hashed))
        self.assertFalse(verify_password("", hashed))

    def test_salt_randomness(self):
        password = "IdenticalPassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Even with identical passwords, salts must differ
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))

    def test_jwt_creation_and_decoding(self):
        user_id = uuid.uuid4()
        email = "engineer@industrialoracle.com"
        token = create_access_token(user_id=user_id, email=email, expires_delta=timedelta(minutes=15))

        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertEqual(payload["email"], email)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_jwt_expiration_rejection(self):
        user_id = uuid.uuid4()
        email = "expired@industrialoracle.com"
        # Create token that expired 10 seconds ago
        token = create_access_token(user_id=user_id, email=email, expires_delta=timedelta(seconds=-10))

        with self.assertRaises(AuthenticationException) as ctx:
            decode_access_token(token)
        self.assertIn("expired", ctx.exception.message.lower())

    def test_jwt_tampered_signature_rejection(self):
        user_id = uuid.uuid4()
        email = "tamper@industrialoracle.com"
        token = create_access_token(user_id=user_id, email=email)
        parts = token.split(".")
        # Tamper with signature
        tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"

        with self.assertRaises(AuthenticationException):
            decode_access_token(tampered_token)

    def test_jwt_malformed_token_rejection(self):
        with self.assertRaises(AuthenticationException):
            decode_access_token("not.a.valid.jwt.token")
        with self.assertRaises(AuthenticationException):
            decode_access_token("random_garbage_string")


if __name__ == "__main__":
    unittest.main()
