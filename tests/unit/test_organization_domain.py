"""Unit tests for Organization and Membership domain entities."""

import unittest
import uuid
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site


class TestOrganizationDomain(unittest.TestCase):
    def test_organization_and_membership(self):
        org = Organization(name="Industrial Corp", slug="industrial-corp")
        self.assertEqual(org.status, "ACTIVE")
        self.assertIsNotNone(org.id)

        user_id = uuid.uuid4()
        membership = Membership(
            user_id=user_id,
            organization_id=org.id,
            role="ADMIN",
        )
        self.assertEqual(membership.role, "ADMIN")
        self.assertTrue(membership.is_active)

        membership.change_role("OWNER")
        self.assertEqual(membership.role, "OWNER")

        membership.deactivate()
        self.assertFalse(membership.is_active)

    def test_site_and_plant_hierarchy(self):
        org_id = uuid.uuid4()
        site = Site(
            organization_id=org_id,
            name="Nairobi Site",
            code="NBO",
            timezone_str="Africa/Nairobi",
        )
        self.assertEqual(site.timezone, "Africa/Nairobi")

        plant = Plant(
            organization_id=org_id,
            site_id=site.id,
            name="Assembly Plant 1",
            code="ASM-1",
        )
        self.assertEqual(plant.organization_id, org_id)
        self.assertEqual(plant.site_id, site.id)
        self.assertEqual(plant.status, "OPERATIONAL")


if __name__ == "__main__":
    unittest.main()
