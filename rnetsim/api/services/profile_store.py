"""Filesystem CRUD for device profiles.

Built-in profiles are constants. Custom profiles stored as JSON in /data/profiles/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from rnetsim.api.models.profile import (
    BUILTIN_PROFILE_MAP,
    BUILTIN_PROFILES,
    DeviceProfile,
)
from rnetsim.config import PROFILES_DIR

logger = logging.getLogger(__name__)


def ensure_dirs() -> None:
    """Create profiles directory if it doesn't exist."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def list_profiles() -> list[DeviceProfile]:
    """List all profiles (built-in + custom)."""
    ensure_dirs()
    profiles = list(BUILTIN_PROFILES)

    for path in sorted(PROFILES_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            profiles.append(DeviceProfile(**data, built_in=False))
        except Exception as e:
            logger.warning("Failed to read profile %s: %s", path, e)

    return profiles


def get_profile(profile_id: str) -> Optional[DeviceProfile]:
    """Get a profile by ID."""
    if profile_id in BUILTIN_PROFILE_MAP:
        return BUILTIN_PROFILE_MAP[profile_id]

    ensure_dirs()
    path = PROFILES_DIR / f"{profile_id}.json"
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return DeviceProfile(**data, built_in=False)

    return None


def save_profile(profile: DeviceProfile) -> Path:
    """Save a custom profile."""
    if profile.id in BUILTIN_PROFILE_MAP:
        raise ValueError(f"Cannot overwrite built-in profile '{profile.id}'")

    ensure_dirs()
    path = PROFILES_DIR / f"{profile.id}.json"
    with open(path, "w") as f:
        json.dump(profile.model_dump(exclude={"built_in"}), f, indent=2)
    logger.info("Saved profile: %s", path)
    return path


def delete_profile(profile_id: str) -> bool:
    """Delete a custom profile. Rejects built-in profiles."""
    if profile_id in BUILTIN_PROFILE_MAP:
        raise ValueError(f"Cannot delete built-in profile '{profile_id}'")

    path = PROFILES_DIR / f"{profile_id}.json"
    if path.exists():
        path.unlink()
        logger.info("Deleted profile: %s", profile_id)
        return True
    return False
