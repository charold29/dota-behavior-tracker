"""
Adapter: implements the ConductSource port by finding Dota 2's
latest_conduct file in the Steam libraries.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from ..application.ports import ConductFile

CFG_PATH = Path("steamapps") / "common" / "dota 2 beta" / "game" / "dota" / "cfg"
DEFAULT_STEAM_PATHS = (Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam"))


class SteamConductSource:
    def __init__(self, folders: Iterable[Path] | None = None):
        self.folders = folders  # None: look them up in the registry and the default paths

    def latest(self) -> ConductFile | None:
        path = find_conduct_file(self.folders)
        if path is None:
            return None
        return ConductFile(location=str(path), text=path.read_text(encoding="utf-8", errors="ignore"))


def steam_folders() -> list[Path]:
    """Main Steam folder + extra libraries (other drives/folders), without duplicates."""
    paths = [p for p in [_registry_steam_path(), *DEFAULT_STEAM_PATHS] if p is not None]

    extra = []
    for p in paths:
        vdf = p / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            extra += library_paths(vdf.read_text(encoding="utf-8", errors="ignore"))

    seen, unique = set(), []
    for p in paths + extra:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def library_paths(vdf_text: str) -> list[Path]:
    """Library folders listed in Steam's libraryfolders.vdf."""
    return [Path(m.group(1).replace("\\\\", "\\")) for m in re.finditer(r'"path"\s+"([^"]+)"', vdf_text)]


def find_conduct_file(folders: Iterable[Path] | None = None) -> Path | None:
    """The most recent latest_conduct_*.txt across the Steam libraries, or None."""
    candidates = []
    for steam in steam_folders() if folders is None else folders:
        cfg = steam / CFG_PATH
        if cfg.is_dir():
            candidates += list(cfg.glob("latest_conduct_*.txt"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _registry_steam_path() -> Path | None:
    try:
        import winreg  # only exists on Windows
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return Path(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        return None
