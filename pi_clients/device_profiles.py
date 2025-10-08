"""Device-specific metadata for Raspberry Pi clue players."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

from app.data import ROOM_GROUPS


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Information required to run a clue player on a Raspberry Pi."""

    key: str
    label: str
    mqtt_prefix: str
    asset_root: Path
    video_map: Mapping[str, Path]


ASSETS_ROOT = Path(__file__).resolve().parents[1] / "assets"

ROOM_FOLDERS: Dict[str, str] = {
    "Boiler Room": "boiler room",
    "Small Room": "small room",
    "Hall Room": "hall room",
    "Hol Intrare": "hol intrare",
    "Jigsaw Room": "jigsaw room",
    "Last Room": "last room",
}


def _build_video_map(device_key: str) -> Mapping[str, Path]:
    mapping: Dict[str, Path] = {}
    for room_key, room_data in ROOM_GROUPS.items():
        room_label = room_data["label"]
        folder = ROOM_FOLDERS.get(room_label)
        if not folder:
            continue
        base_dir = ASSETS_ROOT / folder
        for game in room_data["games"]:
            if device_key in game.default_targets:
                mapping[game.id] = base_dir / game.video
    return mapping


def get_device_profiles() -> Dict[str, DeviceProfile]:
    profiles: Dict[str, DeviceProfile] = {}
    for key, device in (
        ("boilerroom", {"label": "Boiler Room", "prefix": "boiler"}),
        ("holintrare", {"label": "Hol Intrare", "prefix": "hall"}),
        ("lastroom", {"label": "Last Room", "prefix": "last"}),
    ):
        profiles[key] = DeviceProfile(
            key=key,
            label=device["label"],
            mqtt_prefix=device["prefix"],
            asset_root=ASSETS_ROOT,
            video_map=_build_video_map(key),
        )
    return profiles
