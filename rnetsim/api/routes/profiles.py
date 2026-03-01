"""Device profile CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from rnetsim.api.models.profile import DeviceProfile
from rnetsim.api.services import profile_store

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("")
def list_profiles() -> list[dict]:
    """List all profiles (built-in + custom)."""
    return [p.model_dump() for p in profile_store.list_profiles()]


@router.get("/{profile_id}")
def get_profile(profile_id: str) -> dict:
    """Get a profile by ID."""
    profile = profile_store.get_profile(profile_id)
    if not profile:
        raise HTTPException(404, f"Profile '{profile_id}' not found")
    return profile.model_dump()


@router.post("")
def create_profile(profile: DeviceProfile) -> dict:
    """Create a custom profile."""
    try:
        profile_store.save_profile(profile)
        return {"status": "created", "id": profile.id}
    except ValueError as e:
        raise HTTPException(403, str(e))


@router.put("/{profile_id}")
def update_profile(profile_id: str, profile: DeviceProfile) -> dict:
    """Update a custom profile."""
    profile.id = profile_id
    try:
        profile_store.save_profile(profile)
        return {"status": "updated", "id": profile_id}
    except ValueError as e:
        raise HTTPException(403, str(e))


@router.delete("/{profile_id}")
def delete_profile(profile_id: str) -> dict:
    """Delete a custom profile."""
    try:
        deleted = profile_store.delete_profile(profile_id)
        if not deleted:
            raise HTTPException(404, f"Profile '{profile_id}' not found")
        return {"status": "deleted", "id": profile_id}
    except ValueError as e:
        raise HTTPException(403, str(e))
