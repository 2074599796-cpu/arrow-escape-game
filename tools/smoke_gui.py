"""开发辅助脚本：自动点击阻挡箭头并确认碰撞动画能够结束。"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from arrow_game.app import ArrowGameApp  # noqa: E402


def main() -> None:
    root = tk.Tk()
    root.geometry("860x760+80+60")
    app = ArrowGameApp(root)
    app.start_game()
    root.update()

    x, y = app.cell_center(2, 0)
    app.on_canvas_click(SimpleNamespace(x=x, y=y))
    for _ in range(160):
        root.update()
        time.sleep(0.01)

    assert not app.animating, "碰撞动画未按预期结束"
    assert app.engine.remaining_misses == 2, "碰撞后失误次数不正确"
    assert app.engine.arrow_at(2, 0) is not None, "被阻挡箭头不应消失"

    fly_x, fly_y = app.cell_center(0, 2)
    app.on_canvas_click(SimpleNamespace(x=fly_x, y=fly_y))
    for _ in range(100):
        root.update()
        time.sleep(0.01)
    assert not app.animating, "飞出动画未按预期结束"
    assert app.engine.arrow_at(0, 2) is None, "无阻挡飞剑应飞出并消失"
    print("GUI smoke test OK: collision bounce and accelerated flying-sword exit both finished")
    root.destroy()


if __name__ == "__main__":
    main()
