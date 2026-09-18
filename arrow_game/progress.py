from __future__ import annotations

import json
from pathlib import Path


def default_progress_path() -> Path:
    return Path.home() / ".arrow_escape_game_progress.json"


def load_progress(path: Path, level_count: int) -> tuple[int, dict[int, int]]:
    """读取最高解锁关卡和各关最佳星级，损坏文件会安全回到初始状态。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        unlocked = max(0, min(int(data.get("unlocked_level", 0)), level_count - 1))
        stars = {
            int(index): max(0, min(int(value), 3))
            for index, value in data.get("best_stars", {}).items()
            if 0 <= int(index) < level_count
        }
        return unlocked, stars
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0, {}


def save_progress(path: Path, unlocked: int, stars: dict[int, int]) -> None:
    data = {
        "unlocked_level": unlocked,
        "best_stars": {str(index): value for index, value in stars.items()},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
