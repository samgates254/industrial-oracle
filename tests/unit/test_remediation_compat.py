
import pytest
from pydantic import ValidationError
from industrial_oracle.core.config import Settings
import os

def test_settings_loading():
    """Verify settings load correctly."""
    settings = Settings()
    assert settings.PROJECT_NAME == "Industrial Oracle"
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert not hasattr(settings, "SYNC_DATABASE_URL")

def test_dto_model_validate():
    """Verify DTO validation (emulated for v2/v1 compat)."""
    from industrial_oracle.assets.application.dtos import AssetResponseDTO
    import uuid
    from datetime import datetime
    
    data = {
        "id": uuid.uuid4(),
        "organization_id": uuid.uuid4(),
        "name": "Test Asset",
        "asset_tag": "TAG123",
        "asset_type": "TYPE",
        "status": "NEW",
        "critical": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    # This will work in v1 and v2 with model_validate/parse_obj
    dto = AssetResponseDTO.parse_obj(data)
    assert dto.name == "Test Asset"
