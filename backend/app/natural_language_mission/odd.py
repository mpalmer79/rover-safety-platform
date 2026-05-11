"""Operational Design Domain (ODD) profiles.

The platform is **not safety-certified**. The ODD model is an
explicit, declarative envelope. The compiler rejects mission plans
that violate the active ODD; it never silently relaxes the
envelope.
"""

from __future__ import annotations

from .models import OperationalDesignDomain


DEFAULT_ODD_PROFILE_ID: str = "default-warehouse"


# A small, named registry of canonical ODD profiles. Adding a
# profile is a deliberate, reviewable change.
_PROFILES: dict[str, OperationalDesignDomain] = {
    DEFAULT_ODD_PROFILE_ID: OperationalDesignDomain(
        profile_id=DEFAULT_ODD_PROFILE_ID,
        authorized_zones=(
            "alpha",
            "bravo",
            "charlie",
            "delta",
            "loading_zone_one",
            "loading_zone_two",
            "patrol_loop_a",
            "patrol_loop_b",
            "inspection_zone_north",
            "inspection_zone_south",
            "dock",
        ),
        prohibited_regions=(
            "restricted_corridor_one",
            "restricted_corridor_two",
            "human_only_zone",
            "maintenance_bay",
        ),
        speed_limit_mps=1.5,
        max_mission_minutes=30,
        requires_lidar=True,
        requires_battery_min_pct=25,
        requires_dock_known=True,
        operating_window="daylight",
        notes=(
            "Default warehouse profile. Lidar is required for "
            "freshness-gated motion authorisation.",
        ),
    ),
    "night-restricted": OperationalDesignDomain(
        profile_id="night-restricted",
        authorized_zones=("dock",),
        prohibited_regions=(
            "alpha",
            "bravo",
            "charlie",
            "delta",
            "loading_zone_one",
            "loading_zone_two",
            "patrol_loop_a",
            "patrol_loop_b",
            "restricted_corridor_one",
            "restricted_corridor_two",
            "human_only_zone",
            "maintenance_bay",
        ),
        speed_limit_mps=0.5,
        max_mission_minutes=5,
        requires_lidar=True,
        requires_battery_min_pct=50,
        requires_dock_known=True,
        operating_window="night",
        notes=(
            "Restricted night-only profile. Only dock-return is "
            "authorised; everything else is prohibited.",
        ),
    ),
}


def list_profiles() -> tuple[str, ...]:
    return tuple(sorted(_PROFILES))


def get_profile(profile_id: str | None = None) -> OperationalDesignDomain:
    pid = profile_id or DEFAULT_ODD_PROFILE_ID
    if pid not in _PROFILES:
        raise KeyError(f"unknown ODD profile: {pid!r}")
    return _PROFILES[pid]


def is_authorized_zone(profile: OperationalDesignDomain, name: str) -> bool:
    return name.strip().lower() in {z.lower() for z in profile.authorized_zones}


def is_prohibited_region(profile: OperationalDesignDomain, name: str) -> bool:
    return name.strip().lower() in {p.lower() for p in profile.prohibited_regions}


__all__ = [
    "DEFAULT_ODD_PROFILE_ID",
    "list_profiles",
    "get_profile",
    "is_authorized_zone",
    "is_prohibited_region",
]
