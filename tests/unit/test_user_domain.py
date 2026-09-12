"""Unit tests for User domain entity behavior and invariants."""

import unittest
from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.core.security import hash_password
from industrial_oracle.identity.domain.models import User


class TestUserDomain(unittest.TestCase):
    def test_user_creation_and_password_verification(self):
        raw_pwd = "InitialSecurePassword1!"
        pwd_hash = hash_password(raw_pwd)
        user = User(
            email="Sam.Gates@Example.com ",
            password_hash=pwd_hash,
            full_name="Sam Gates",
        )

        # Email must be normalized
        self.assertEqual(user.email, "sam.gates@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.verify_password(raw_pwd))
        self.assertFalse(user.verify_password("WrongPassword"))

    def test_password_change_enforces_length(self):
        user = User(
            email="test@example.com",
            password_hash=hash_password("OldPassword123!"),
            full_name="Test User",
        )

        with self.assertRaises(BusinessRuleViolationException):
            user.change_password("short")

        user.change_password("NewValidPassword123!")
        self.assertTrue(user.verify_password("NewValidPassword123!"))
        self.assertFalse(user.verify_password("OldPassword123!"))

    def test_activation_and_deactivation(self):
        user = User(
            email="active@example.com",
            password_hash=hash_password("Password123!"),
            full_name="Active User",
        )
        self.assertTrue(user.is_active)

        user.deactivate()
        self.assertFalse(user.is_active)

        user.activate()
        self.assertTrue(user.is_active)


if __name__ == "__main__":
    unittest.main()
