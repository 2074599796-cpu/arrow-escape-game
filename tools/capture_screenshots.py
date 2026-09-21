"""开发辅助脚本：截取真实 Tkinter 界面，图片用于作业博客。"""

from __future__ import annotations

import sys
import time
import ctypes
from pathlib import Path
from tkinter import Tk

from PIL import ImageGrab

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from arrow_game.app import ArrowGameApp  # noqa: E402


def capture(root: Tk, output: Path) -> None:
    root.update_idletasks()
    root.update()
    time.sleep(0.25)
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()
    ImageGrab.grab((x, y, x + width, y + height)).save(output)


def main() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass

    output_dir = PROJECT_ROOT / "screenshots"
    output_dir.mkdir(exist_ok=True)

    root = Tk()
    root.geometry("860x760+80+60")
    root.attributes("-topmost", True)
    app = ArrowGameApp(root)
    app.progress_path = output_dir / ".capture_progress.json"

    capture(root, output_dir / "start.png")
    app.unlocked_level = len(app.engine.levels) - 1
    app.best_stars = {0: 3, 1: 2, 2: 1}
    app.show_level_select()
    capture(root, output_dir / "level_select.png")
    app.start_game()
    capture(root, output_dir / "game.png")

    app.show_hint()
    capture(root, output_dir / "hint.png")

    hinted_arrow = app.engine.hint()
    if hinted_arrow is not None:
        app.engine.click(hinted_arrow.row, hinted_arrow.col)
        app.undo_last()
        capture(root, output_dir / "undo.png")

    flying_arrow = app.engine.arrow_at(0, 2)
    if flying_arrow is not None:
        app.engine.click(flying_arrow.row, flying_arrow.col)
        app.update_header()
        app.status_label.config(text="飞剑破阵而出", fg="#8fd3a9")
        app.render_board(skip=flying_arrow)
        app.draw_arrow(flying_arrow, "#8fd3a9", (0, -48), "flying", True)
        capture(root, output_dir / "flight.png")

    app.engine.restart_game()
    app.update_header()
    app.render_board()

    blocked_arrow = app.engine.arrow_at(2, 0)
    if blocked_arrow is not None:
        blocker = app.engine.find_blocker(blocked_arrow)
        if blocker is not None:
            app.engine.click(blocked_arrow.row, blocked_arrow.col)
            app.update_header()
            app.status_label.config(text="铮！剑势受阻，剑心 -1", fg="#bd5143")
            start_x, start_y = app.cell_center(blocked_arrow.row, blocked_arrow.col)
            end_x, end_y = app.cell_center(blocker.row, blocker.col)
            center_distance = abs(end_x - start_x) + abs(end_y - start_y)
            travel = max(app.cell * 0.20, center_distance - app.cell * 0.78)
            app.render_collision_frame(blocked_arrow, blocker, travel, 0.35)
            capture(root, output_dir / "collision.png")

    app.engine.score = 600
    app.show_result(game_won=False)
    capture(root, output_dir / "success.png")

    app.engine.select_level(4)
    app.show_game()
    capture(root, output_dir / "final_level.png")

    app.show_failure()
    capture(root, output_dir / "failure.png")

    app.engine.select_level(4)
    app.show_game()
    app.engine.score = 2400
    app.level_started_at = time.monotonic() - 87
    app.show_result(game_won=True)
    capture(root, output_dir / "final_success.png")

    root.destroy()
    app.progress_path.unlink(missing_ok=True)
    print(f"已生成截图：{output_dir}")


if __name__ == "__main__":
    main()
