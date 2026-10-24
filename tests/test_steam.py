import os
from pathlib import Path

from dota_behavior_tracker.steam import CFG_PATH, find_conduct_file, library_paths

VDF = r'''
"libraryfolders"
{
	"0"
	{
		"path"		"C:\\Program Files (x86)\\Steam"
		"label"		""
	}
	"1"
	{
		"path"		"D:\\SteamLibrary"
	}
}
'''


def test_library_paths_reads_libraryfolders_vdf():
    assert library_paths(VDF) == [Path(r"C:\Program Files (x86)\Steam"), Path(r"D:\SteamLibrary")]


def test_find_conduct_file_picks_the_newest_across_libraries(tmp_path):
    old = _conduct_file(tmp_path / "lib1", "latest_conduct_1.111.txt", mtime=1_000)
    new = _conduct_file(tmp_path / "lib2", "latest_conduct_1.222.txt", mtime=2_000)

    assert find_conduct_file([tmp_path / "lib1", tmp_path / "lib2"]) == new
    assert old.exists()


def test_find_conduct_file_returns_none_when_missing(tmp_path):
    assert find_conduct_file([tmp_path, tmp_path / "does-not-exist"]) is None


def _conduct_file(library: Path, name: str, mtime: int) -> Path:
    cfg = library / CFG_PATH
    cfg.mkdir(parents=True)
    path = cfg / name
    path.write_text("seq_num: 1", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path
