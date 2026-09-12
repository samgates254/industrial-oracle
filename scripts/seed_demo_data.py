"""Seed demo data script for Industrial Oracle."""

import asyncio
import uuid
from datetime import datetime, timezone

from industrial_oracle.core.config import settings
from industrial_oracle.core.logging import setup_logging, logger

setup_logging()


async def seed_data() -> None:
    logger.info("Seeding initial demo data for %s...", settings.PROJECT_NAME)
    # Demo organizational data definition
    org_id = uuid.uuid4()
    site_id = uuid.uuid4()
    plant_id = uuid.uuid4()
    line_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    machine_id = uuid.uuid4()

    demo_hierarchy = {
        "organization": {"id": str(org_id), "name": "Global Industrial Corp", "slug": "global-industrial"},
        "site": {"id": str(site_id), "name": "Nairobi Manufacturing Complex", "code": "NBO-01"},
        "plant": {"id": str(plant_id), "name": "Heavy Machinery Assembly Plant", "code": "HMA-01"},
        "production_line": {"id": str(line_id), "name": "Automated Stamping Line A", "code": "STAMP-A"},
        "asset": {"id": str(asset_id), "name": "Hydraulic Stamping Press 500T", "asset_tag": "EQ-STAMP-500T"},
        "machine": {"id": str(machine_id), "name": "Press Unit 1", "model": "H-500T-PRO", "power_rating_kw": 120.0},
    }

    logger.info("Demo hierarchy constructed:")
    for entity, data in demo_hierarchy.items():
        logger.info("  %s: %s", entity.upper(), data)

    logger.info("Seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())
