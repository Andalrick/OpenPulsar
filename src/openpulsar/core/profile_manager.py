from pathlib import Path

from .profile import Profile
from .serialization import (
    save_profile,
    load_profile,
)


PROFILE_DIR = (
    Path.home()
    / ".config"
    / "openpulsar"
    / "profiles"
)


def ensure_profile_dir() -> None:
    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def list_profiles() -> list[str]:
    ensure_profile_dir()

    return sorted(
        file.stem
        for file in PROFILE_DIR.glob("*.json")
    )


def save_profile_to_library(
    profile: Profile,
) -> Path:
    ensure_profile_dir()

    path = PROFILE_DIR / f"{profile.name}.json"

    save_profile(
        profile,
        path,
    )

    return path


def load_profile_from_library(
    name: str,
) -> Profile:
    path = PROFILE_DIR / f"{name}.json"

    return load_profile(path)


def delete_profile(
    name: str,
) -> None:
    path = PROFILE_DIR / f"{name}.json"

    if path.exists():
        path.unlink()
