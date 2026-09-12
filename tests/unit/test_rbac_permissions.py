"""Unit tests for Role and Permission specifications."""

import unittest
from industrial_oracle.core.security import (
    PermissionEnum,
    ROLE_PERMISSIONS,
    RoleEnum,
)


class TestRBACPermissions(unittest.TestCase):
    def test_all_roles_defined(self):
        expected_roles = {"OWNER", "ADMIN", "ENGINEER", "OPERATOR", "ANALYST", "VIEWER"}
        self.assertEqual(set(RoleEnum.ALL_ROLES), expected_roles)

    def test_owner_has_all_permissions(self):
        owner_perms = ROLE_PERMISSIONS[RoleEnum.OWNER]
        self.assertIn(PermissionEnum.ORGANIZATION_READ, owner_perms)
        self.assertIn(PermissionEnum.ORGANIZATION_UPDATE, owner_perms)
        self.assertIn(PermissionEnum.USERS_READ, owner_perms)
        self.assertIn(PermissionEnum.USERS_CREATE, owner_perms)
        self.assertIn(PermissionEnum.USERS_UPDATE, owner_perms)
        self.assertIn(PermissionEnum.USERS_DISABLE, owner_perms)
        self.assertIn(PermissionEnum.ASSETS_CREATE, owner_perms)
        self.assertIn(PermissionEnum.ASSETS_DELETE, owner_perms)
        self.assertIn(PermissionEnum.OPTIMIZATION_RUN, owner_perms)
        self.assertIn(PermissionEnum.AUDIT_READ, owner_perms)

    def test_admin_permissions(self):
        admin_perms = ROLE_PERMISSIONS[RoleEnum.ADMIN]
        self.assertIn(PermissionEnum.USERS_CREATE, admin_perms)
        self.assertIn(PermissionEnum.USERS_DISABLE, admin_perms)
        self.assertIn(PermissionEnum.ASSETS_CREATE, admin_perms)
        self.assertIn(PermissionEnum.OPTIMIZATION_RUN, admin_perms)

    def test_engineer_permissions(self):
        eng_perms = ROLE_PERMISSIONS[RoleEnum.ENGINEER]
        self.assertIn(PermissionEnum.ASSETS_CREATE, eng_perms)
        self.assertIn(PermissionEnum.OPTIMIZATION_RUN, eng_perms)
        # Engineers cannot disable users or update organization settings
        self.assertNotIn(PermissionEnum.USERS_DISABLE, eng_perms)
        self.assertNotIn(PermissionEnum.ORGANIZATION_UPDATE, eng_perms)

    def test_operator_permissions(self):
        op_perms = ROLE_PERMISSIONS[RoleEnum.OPERATOR]
        self.assertIn(PermissionEnum.OPERATIONS_READ, op_perms)
        self.assertIn(PermissionEnum.OPERATIONS_CREATE, op_perms)
        # Operators cannot delete assets, run optimizations, or manage users
        self.assertNotIn(PermissionEnum.ASSETS_DELETE, op_perms)
        self.assertNotIn(PermissionEnum.OPTIMIZATION_RUN, op_perms)
        self.assertNotIn(PermissionEnum.USERS_CREATE, op_perms)

    def test_viewer_permissions(self):
        viewer_perms = ROLE_PERMISSIONS[RoleEnum.VIEWER]
        self.assertIn(PermissionEnum.ORGANIZATION_READ, viewer_perms)
        self.assertIn(PermissionEnum.ASSETS_READ, viewer_perms)
        self.assertIn(PermissionEnum.OPERATIONS_READ, viewer_perms)
        # Viewers have zero create/update/delete/run permissions
        self.assertNotIn(PermissionEnum.USERS_CREATE, viewer_perms)
        self.assertNotIn(PermissionEnum.ASSETS_CREATE, viewer_perms)
        self.assertNotIn(PermissionEnum.OPTIMIZATION_RUN, viewer_perms)


if __name__ == "__main__":
    unittest.main()
