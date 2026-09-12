"""Domain enumerations for V0.1."""

from enum import Enum


class ResourceCategory(str, Enum):
    """Authoritative resource categories for V0.1."""

    RAW = "RAW"
    WIP = "WIP"
    FINISHED = "FINISHED"
    CONSUMABLE = "CONSUMABLE"
