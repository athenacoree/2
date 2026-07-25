import unittest
from care_clear_crew.tests import BaseTestCase
from care_clear_crew.auth import (
    create_user_record, verify_login, hash_password, verify_password, require_role
)
from care_clear_crew.history_db import (
    get_user_by_email, get_users_by_institution, update_user_status_and_role, clear_all_history_global
)

class TestAuthentication(BaseTestCase):
    """
    Unit tests for auth.py authentication features.
    Verifies secure password hashing, active status logins, multi-tenant isolation of user lists,
    automatic admin role assignment for the first user of a new institution, and update logic.
    """

    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Validate hashing is secure and distinct from plaintext
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))

        # Verify correct matching
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_automatic_admin_assignment_and_multi_tenant_lists(self):
        clear_all_history_global()

        # Create first user for Clinica Alfa - should automatically become administrator
        uid_alfa_1 = create_user_record(
            email="admin.alfa@med.com",
            password="pwd",
            full_name="Admin Alfa",
            role="operativo", # Requested as operative but system must promote to admin
            institution_name="Clinica Alfa"
        )
        user_alfa_1 = get_user_by_email("admin.alfa@med.com")
        self.assertEqual(user_alfa_1["role"], "administrador")

        # Create second user for Clinica Alfa - should retain requested role
        uid_alfa_2 = create_user_record(
            email="op.alfa@med.com",
            password="pwd",
            full_name="Operator Alfa",
            role="operativo",
            institution_name="Clinica Alfa"
        )
        user_alfa_2 = get_user_by_email("op.alfa@med.com")
        self.assertEqual(user_alfa_2["role"], "operativo")

        # Create first user for Clinica Beta - should automatically become administrator
        uid_beta_1 = create_user_record(
            email="admin.beta@med.com",
            password="pwd",
            full_name="Admin Beta",
            role="operativo",
            institution_name="Clinica Beta"
        )
        user_beta_1 = get_user_by_email("admin.beta@med.com")
        self.assertEqual(user_beta_1["role"], "administrador")

        # Validate multi-tenant separation of user lists
        users_alfa = get_users_by_institution("Clinica Alfa")
        self.assertEqual(len(users_alfa), 2)
        for u in users_alfa:
            self.assertEqual(u["institution_name"], "Clinica Alfa")

        users_beta = get_users_by_institution("Clinica Beta")
        self.assertEqual(len(users_beta), 1)
        self.assertEqual(users_beta[0]["email"], "admin.beta@med.com")

    def test_login_verification_and_active_status(self):
        clear_all_history_global()

        # Register a valid user
        create_user_record(
            email="user@med.com",
            password="secret_password_1",
            full_name="Standard User",
            role="operativo",
            institution_name="Clinica Alfa"
        )

        # Successful login returns dictionary of user details
        user_details = verify_login("user@med.com", "secret_password_1")
        self.assertIsNotNone(user_details)
        self.assertEqual(user_details["full_name"], "Standard User")

        # Failed logins
        self.assertIsNone(verify_login("user@med.com", "wrong_pwd"))
        self.assertIsNone(verify_login("nonexistent@med.com", "secret_password_1"))

        # Account deactivation check
        uid = user_details["id"]
        update_user_status_and_role(user_id=uid, is_active=0, role="operativo", inst_name="Clinica Alfa")

        with self.assertRaises(PermissionError):
            verify_login("user@med.com", "secret_password_1")

    def test_require_role_access_control(self):
        # Operative user access control helper
        op_user = {"role": "operativo"}
        admin_user = {"role": "administrador"}

        self.assertTrue(require_role(op_user, ["operativo"]))
        self.assertTrue(require_role(admin_user, ["administrador"]))
        self.assertTrue(require_role(admin_user, ["operativo", "administrador"]))
        self.assertFalse(require_role(op_user, ["administrador"]))
        self.assertFalse(require_role(None, ["operativo"]))

if __name__ == "__main__":
    unittest.main()
