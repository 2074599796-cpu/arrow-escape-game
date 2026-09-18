from __future__ import annotations

import math
import time
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

try:
    import winsound
except ImportError:  # 非 Windows 系统仍可正常运行
    winsound = None

from .levels import LEVELS
from .model import Arrow, Direction, GameEngine, GameState, MoveResult
from .progress import default_progress_path, load_progress, save_progress


BG = "#090d0b"
PANEL = "#121b17"
GRID = "#38483f"
CYAN = "#72d5ad"       # 青玉剑气
PURPLE = "#809b8c"
YELLOW = "#d7b66a"     # 古金
WHITE = "#f1e8d2"      # 宣纸白
MUTED = "#9eaa9f"
RED = "#bd5143"        # 朱砂
GREEN = "#8fd3a9"


class ArrowGameApp:
    WIDTH = 860
    HEIGHT = 760

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = GameEngine(LEVELS, max_misses=3)
        self.animating = False
        self.canvas: tk.Canvas | None = None
        self.board_left = 0.0
        self.board_top = 0.0
        self.cell = 0.0
        self.hover_arrow: Arrow | None = None
        self.timer_job: str | None = None
        self.level_started_at = time.monotonic()
        self.elapsed_seconds = 0
        self.progress_path = default_progress_path()
        self.unlocked_level, self.best_stars = load_progress(
            self.progress_path, len(self.engine.levels)
        )
        self.sword_images = self.load_sword_images()
        self.start_background = tk.PhotoImage(
            file=str(Path(__file__).resolve().parents[1] / "assets" / "start_background.png")
        )

        root.title("一箭又一箭 · 飞剑问道")
        root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        root.minsize(760, 680)
        root.configure(bg=BG)
        root.bind("<Key-r>", lambda _event: self.restart_level())
        root.bind("<Key-R>", lambda _event: self.restart_level())
        root.bind("<Key-h>", lambda _event: self.show_hint())
        root.bind("<Key-H>", lambda _event: self.show_hint())
        root.bind("<Control-z>", lambda _event: self.undo_last())
        self.show_start()

    @staticmethod
    def load_sword_images() -> dict[Direction, tk.PhotoImage]:
        asset_dir = Path(__file__).resolve().parents[1] / "assets"
        filenames = {
            Direction.UP: "sword_up.png",
            Direction.DOWN: "sword_down.png",
            Direction.LEFT: "sword_left.png",
            Direction.RIGHT: "sword_right.png",
        }
        return {
            direction: tk.PhotoImage(file=str(asset_dir / filename))
            for direction, filename in filenames.items()
        }

    def clear(self) -> None:
        if self.timer_job is not None:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        for child in self.root.winfo_children():
            child.destroy()

    def make_button(
        self, parent: tk.Misc, text: str, command,
        primary: bool = True, compact: bool = False,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Microsoft YaHei UI", 10 if compact else 13, "bold"),
            fg=BG if primary else WHITE,
            bg=YELLOW if primary else PANEL,
            activebackground=GREEN if primary else GRID,
            activeforeground=BG if primary else WHITE,
            relief="flat",
            bd=0,
            padx=12 if compact else 28,
            pady=8 if compact else 12,
            cursor="hand2",
        )

    @staticmethod
    def play_sound(kind: str) -> None:
        if winsound is None:
            return
        sounds = {
            "fly": winsound.MB_OK,
            "collision": winsound.MB_ICONHAND,
            "clear": winsound.MB_ICONASTERISK,
        }
        try:
            winsound.MessageBeep(sounds.get(kind, winsound.MB_OK))
        except RuntimeError:
            pass

    def show_start(self) -> None:
        self.clear()
        self.root.configure(bg=BG)
        canvas = tk.Canvas(
            self.root, width=self.WIDTH, height=self.HEIGHT,
            bg=BG, highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.create_image(self.WIDTH / 2, self.HEIGHT / 2, image=self.start_background, anchor="center")

        canvas.create_text(
            self.WIDTH / 2 + 2, 610 + 3, text="一箭又一箭",
            font=("STKaiti", 38, "bold"), fill="#050807",
        )
        canvas.create_text(
            self.WIDTH / 2, 610, text="一箭又一箭",
            font=("STKaiti", 38, "bold"), fill=YELLOW,
        )
        canvas.create_text(
            self.WIDTH / 2, 650,
            text="无阻则出剑 · 有阻则损剑心 · 清空剑阵即可破境",
            font=("STKaiti", 14), fill=WHITE,
        )
        button_row = tk.Frame(canvas, bg="#101512")
        self.make_button(button_row, "执剑入局", self.start_game).pack(side="left", padx=6)
        self.make_button(
            button_row, "境界选择", self.show_level_select, primary=False
        ).pack(side="left", padx=6)
        canvas.create_window(self.WIDTH / 2, 705, window=button_row)
        canvas.create_text(
            self.WIDTH / 2, 748, text="R 重整剑阵 · H 提示 · Ctrl+Z 撤销",
            font=("Microsoft YaHei UI", 9), fill="#c5cec6",
        )

    def start_game(self) -> None:
        self.engine.restart_game()
        self.show_game()

    def show_level_select(self) -> None:
        self.clear()
        wrap = tk.Frame(self.root, bg=BG, padx=70, pady=42)
        wrap.pack(fill="both", expand=True)
        tk.Label(
            wrap, text="择境问剑", font=("STKaiti", 38, "bold"), fg=YELLOW, bg=BG,
        ).pack(pady=(20, 8))
        tk.Label(
            wrap, text="通关后自动解锁下一境，进度会保存到本机",
            font=("Microsoft YaHei UI", 11), fg=MUTED, bg=BG,
        ).pack(pady=(0, 24))
        for index, level in enumerate(self.engine.levels):
            unlocked = index <= self.unlocked_level
            stars = "★" * self.best_stars.get(index, 0) or "尚未通关"
            text = f"第 {index + 1} 境 · {level.name}    {stars}" if unlocked else f"第 {index + 1} 境 · 尚未解锁"
            button = self.make_button(
                wrap,
                text,
                lambda selected=index: self.play_level(selected),
                primary=unlocked,
                compact=True,
            )
            button.config(font=("Microsoft YaHei UI", 12, "bold"))
            button.config(state="normal" if unlocked else "disabled")
            button.pack(fill="x", pady=4)
        self.make_button(wrap, "返回山门", self.show_start, primary=False, compact=True).pack(pady=12)

    def play_level(self, index: int) -> None:
        if index > self.unlocked_level:
            return
        self.engine.select_level(index)
        self.show_game()

    def show_game(self) -> None:
        self.clear()
        self.animating = False
        self.level_started_at = time.monotonic()
        self.elapsed_seconds = 0
        header = tk.Frame(self.root, bg=BG, padx=28, pady=12)
        header.pack(fill="x")

        top_row = tk.Frame(header, bg=BG)
        top_row.pack(fill="x")
        self.level_label = tk.Label(top_row, font=("Microsoft YaHei UI", 15, "bold"), fg=WHITE, bg=BG)
        self.level_label.pack(side="left")
        self.info_label = tk.Label(header, font=("Microsoft YaHei UI", 12), fg=MUTED, bg=BG)
        self.info_label.pack(anchor="w", pady=(8, 0))
        self.make_button(
            top_row, "重整", self.restart_level, primary=False, compact=True
        ).pack(side="right", padx=(5, 0))
        self.make_button(
            top_row, "撤销", self.undo_last, primary=False, compact=True
        ).pack(side="right", padx=5)
        self.make_button(
            top_row, "提示", self.show_hint, primary=False, compact=True
        ).pack(side="right", padx=5)

        self.canvas = tk.Canvas(self.root, bg=PANEL, highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self.render_board())
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)

        self.status_label = tk.Label(
            self.root, text="观其剑锋，择一路无碍的飞剑", font=("STKaiti", 14),
            fg=CYAN, bg=BG, pady=12,
        )
        self.status_label.pack()
        self.engine.start()
        self.update_header()
        self.update_timer()
        self.root.after(20, self.render_board)

    def update_header(self) -> None:
        level = self.engine.level
        self.level_label.config(
            text=f"第 {self.engine.level_index + 1}/{len(self.engine.levels)} 关 · {level.name}"
        )
        hearts = "◆" * self.engine.remaining_misses + "◇" * (self.engine.max_misses - self.engine.remaining_misses)
        self.info_label.config(
            text=(
                f"飞剑 {self.engine.remaining_arrows}  剑心 {hearts}  "
                f"积分 {self.engine.score}  {self.elapsed_seconds:02d}秒"
            )
        )

    def update_timer(self) -> None:
        if self.engine.state == GameState.PLAYING and self.root.winfo_exists():
            self.elapsed_seconds = int(time.monotonic() - self.level_started_at)
            if hasattr(self, "info_label") and self.info_label.winfo_exists():
                self.update_header()
            self.timer_job = self.root.after(1000, self.update_timer)

    def show_hint(self) -> None:
        if self.animating or self.engine.state != GameState.PLAYING:
            return
        arrow = self.engine.hint()
        if arrow is None:
            self.status_label.config(text="此阵暂无线索", fg=RED)
            return
        self.render_board(blocker=arrow)
        self.status_label.config(
            text=f"剑意所指：第 {arrow.row + 1} 行第 {arrow.col + 1} 列可出剑",
            fg=YELLOW,
        )

    def undo_last(self) -> None:
        if self.animating or self.engine.state != GameState.PLAYING:
            return
        if self.engine.undo():
            self.hover_arrow = None
            self.update_header()
            self.render_board()
            self.status_label.config(text="时光回溯，已撤销上一步", fg=CYAN)
        else:
            self.status_label.config(text="当前没有可撤销的步骤", fg=MUTED)

    def board_geometry(self) -> tuple[float, float, float]:
        assert self.canvas is not None
        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 500)
        level = self.engine.level
        cell = min((width - 100) / level.cols, (height - 70) / level.rows, 82)
        left = (width - cell * level.cols) / 2
        top = (height - cell * level.rows) / 2
        return left, top, cell

    def render_board(
        self,
        selected: Arrow | None = None,
        blocker: Arrow | None = None,
        skip: Arrow | None = None,
    ) -> None:
        if self.canvas is None or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        self.board_left, self.board_top, self.cell = self.board_geometry()
        level = self.engine.level

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.create_polygon(
            0, height, 0, height * 0.73,
            width * 0.12, height * 0.56, width * 0.21, height * 0.72,
            width * 0.34, height * 0.48, width * 0.46, height * 0.71,
            width * 0.61, height * 0.53, width * 0.76, height * 0.72,
            width * 0.90, height * 0.58, width, height * 0.69, width, height,
            fill="#0c1512", outline="",
        )
        self.canvas.create_polygon(
            0, height, 0, height * 0.84,
            width * 0.18, height * 0.70, width * 0.31, height * 0.84,
            width * 0.55, height * 0.67, width * 0.72, height * 0.84,
            width * 0.88, height * 0.73, width, height * 0.82, width, height,
            fill="#101b17", outline="",
        )
        for y in range(24, height, 42):
            for x in range(24 + (y // 42 % 2) * 20, width, 42):
                self.canvas.create_oval(x, y, x + 2, y + 2, fill="#33483d", outline="")

        self.canvas.create_line(
            16, height * 0.28, width * 0.27, height * 0.28,
            width * 0.34, height * 0.25, width * 0.55, height * 0.25,
            fill="#263a31", width=2, smooth=True,
        )
        self.canvas.create_line(
            width * 0.63, height * 0.36, width * 0.76, height * 0.36,
            width * 0.83, height * 0.33, width - 18, height * 0.33,
            fill="#263a31", width=2, smooth=True,
        )

        board_right = self.board_left + level.cols * self.cell
        board_bottom = self.board_top + level.rows * self.cell
        self.canvas.create_rectangle(
            self.board_left + 8, self.board_top + 10, board_right + 8, board_bottom + 10,
            fill="#050807", outline="",
        )
        self.canvas.create_rectangle(
            self.board_left - 3, self.board_top - 3, board_right + 3, board_bottom + 3,
            fill="#111a16", outline=YELLOW, width=2,
        )

        for row in range(level.rows):
            for col in range(level.cols):
                x1 = self.board_left + col * self.cell
                y1 = self.board_top + row * self.cell
                self.canvas.create_rectangle(
                    x1, y1, x1 + self.cell, y1 + self.cell,
                    fill="#111b17" if (row + col) % 2 == 0 else "#16211c",
                    outline=GRID, width=1,
                )

        if self.board_left > 100:
            self.canvas.create_text(
                width - 34, height / 2, text="浩\n然\n天\n下",
                font=("STKaiti", 15, "bold"), fill="#6e806f", justify="center",
            )

        for arrow in self.engine.arrows:
            if skip == arrow:
                continue
            color = RED if arrow == selected else YELLOW if arrow == blocker else WHITE if arrow == self.hover_arrow else CYAN
            self.draw_arrow(arrow, color, emphasized=arrow in (selected, blocker, self.hover_arrow))

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        return (
            self.board_left + (col + 0.5) * self.cell,
            self.board_top + (row + 0.5) * self.cell,
        )

    def draw_arrow(
        self,
        arrow: Arrow,
        color: str,
        offset: tuple[float, float] = (0, 0),
        tag: str = "",
        emphasized: bool = False,
    ) -> None:
        assert self.canvas is not None
        x, y = self.cell_center(arrow.row, arrow.col)
        x += offset[0]
        y += offset[1]
        dr, dc = arrow.direction.delta
        px, py = -dr, dc
        if emphasized:
            for index, trail in enumerate((0.30, 0.42, 0.54)):
                half_width = self.cell * (0.11 - index * 0.02)
                self.canvas.create_line(
                    x - dc * self.cell * trail + px * half_width,
                    y - dr * self.cell * trail + py * half_width,
                    x - dc * self.cell * trail - px * half_width,
                    y - dr * self.cell * trail - py * half_width,
                    fill=color, width=max(1, 3 - index), tags=tag,
                )
        self.canvas.create_image(
            x, y, image=self.sword_images[arrow.direction], anchor="center", tags=tag,
        )

    def arrow_from_pointer(self, x: float, y: float) -> Arrow | None:
        if self.cell <= 0:
            return None
        col = int((x - self.board_left) // self.cell)
        row = int((y - self.board_top) // self.cell)
        if 0 <= row < self.engine.level.rows and 0 <= col < self.engine.level.cols:
            return self.engine.arrow_at(row, col)
        return None

    def on_canvas_motion(self, event: tk.Event) -> None:
        if self.animating or self.engine.state != GameState.PLAYING:
            return
        arrow = self.arrow_from_pointer(event.x, event.y)
        if arrow != self.hover_arrow:
            self.hover_arrow = arrow
            self.render_board()

    def on_canvas_leave(self, _event: tk.Event) -> None:
        if self.hover_arrow is not None and not self.animating:
            self.hover_arrow = None
            self.render_board()

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.animating or self.engine.state != GameState.PLAYING:
            return
        arrow = self.arrow_from_pointer(event.x, event.y)
        if arrow is None:
            self.status_label.config(text="此处无剑", fg=MUTED)
            return

        result = self.engine.click(arrow.row, arrow.col)
        self.update_header()
        self.hover_arrow = None
        if result.success and result.arrow:
            self.play_sound("fly")
            self.status_label.config(text=result.message, fg=GREEN)
            self.animate_fly(result)
        elif result.arrow:
            self.play_sound("collision")
            self.status_label.config(text="铮！剑势受阻，剑心 -1", fg=RED)
            self.animate_collision(result)

    def animate_fly(self, result: MoveResult) -> None:
        assert result.arrow is not None and self.canvas is not None
        arrow = result.arrow
        self.animating = True
        self.render_board(skip=arrow)
        dr, dc = arrow.direction.delta
        distance = max(self.canvas.winfo_width(), self.canvas.winfo_height())
        steps = 14

        def frame(index: int) -> None:
            if self.canvas is None or not self.canvas.winfo_exists():
                return
            self.canvas.delete("flying")
            fraction = (index / steps) ** 2
            self.draw_arrow(arrow, GREEN, (dc * distance * fraction, dr * distance * fraction), "flying", True)
            for spark_index in range(3):
                spark_distance = self.cell * (0.24 + spark_index * 0.18)
                spark_x = self.cell_center(arrow.row, arrow.col)[0] + dc * distance * fraction - dc * spark_distance
                spark_y = self.cell_center(arrow.row, arrow.col)[1] + dr * distance * fraction - dr * spark_distance
                size = max(1, 3 - spark_index)
                self.canvas.create_oval(
                    spark_x - size, spark_y - size, spark_x + size, spark_y + size,
                    fill=YELLOW if spark_index == 0 else GREEN, outline="", tags="flying",
                )
            if index < steps:
                self.root.after(18, lambda: frame(index + 1))
            else:
                self.canvas.delete("flying")
                self.animating = False
                if result.level_cleared:
                    self.play_sound("clear")
                    self.show_result(result.game_won)
                else:
                    self.render_board()

        frame(0)

    def draw_impact(self, x: float, y: float, progress: float) -> None:
        assert self.canvas is not None
        radius = self.cell * (0.16 + progress * 0.38)
        fade_color = YELLOW if progress < 0.5 else RED
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill="", outline=fade_color, width=max(1, int(4 - progress * 3)), tags="collision",
        )
        for index in range(10):
            angle = index * math.tau / 10
            inner = self.cell * (0.13 + progress * 0.12)
            outer = self.cell * (0.28 + progress * 0.45)
            self.canvas.create_line(
                x + math.cos(angle) * inner,
                y + math.sin(angle) * inner,
                x + math.cos(angle) * outer,
                y + math.sin(angle) * outer,
                fill=YELLOW if index % 2 == 0 else RED,
                width=3 if progress < 0.6 else 2,
                tags="collision",
            )
        self.canvas.create_text(
            x, y - self.cell * (0.45 + progress * 0.2), text="剑势受阻!",
            font=("STKaiti", max(12, int(self.cell * 0.17)), "bold"),
            fill=WHITE, tags="collision",
        )

    def render_collision_frame(
        self,
        arrow: Arrow,
        blocker: Arrow,
        travel: float,
        impact_progress: float | None = None,
    ) -> None:
        self.render_board(blocker=blocker, skip=arrow)
        dr, dc = arrow.direction.delta
        self.draw_arrow(arrow, RED, (dc * travel, dr * travel), "collision", True)
        if impact_progress is not None:
            start_x, start_y = self.cell_center(arrow.row, arrow.col)
            impact_x = start_x + dc * (travel + self.cell * 0.38)
            impact_y = start_y + dr * (travel + self.cell * 0.38)
            self.draw_impact(impact_x, impact_y, impact_progress)

    def animate_collision(self, result: MoveResult) -> None:
        assert result.arrow is not None and result.blocker is not None and self.canvas is not None
        arrow = result.arrow
        blocker = result.blocker
        self.animating = True
        start_x, start_y = self.cell_center(arrow.row, arrow.col)
        end_x, end_y = self.cell_center(blocker.row, blocker.col)
        center_distance = abs(end_x - start_x) + abs(end_y - start_y)
        max_travel = max(self.cell * 0.20, center_distance - self.cell * 0.78)
        approach_steps = 8
        impact_steps = 7
        return_steps = 9

        def approach(index: int) -> None:
            fraction = index / approach_steps
            eased = 1 - (1 - fraction) ** 3
            self.render_collision_frame(arrow, blocker, max_travel * eased)
            if index < approach_steps:
                self.root.after(18, lambda: approach(index + 1))
            else:
                impact(0)

        def impact(index: int) -> None:
            progress = index / impact_steps
            recoil = math.sin(progress * math.pi * 4) * self.cell * 0.045 * (1 - progress)
            self.render_collision_frame(arrow, blocker, max_travel - recoil, progress)
            if index < impact_steps:
                self.root.after(38, lambda: impact(index + 1))
            else:
                retreat(0)

        def retreat(index: int) -> None:
            fraction = index / return_steps
            eased = fraction * fraction * (3 - 2 * fraction)
            self.render_collision_frame(arrow, blocker, max_travel * (1 - eased))
            if index < return_steps:
                self.root.after(20, lambda: retreat(index + 1))
            else:
                self.finish_blocked(result)

        approach(0)

    def finish_blocked(self, result: MoveResult) -> None:
        self.animating = False
        if result.game_over:
            self.show_failure()
        else:
            self.render_board()
            self.status_label.config(text="飞剑归位，请另寻剑路", fg=MUTED)

    def show_result(self, game_won: bool) -> None:
        self.elapsed_seconds = int(time.monotonic() - self.level_started_at)
        stars = 3 if self.engine.remaining_misses == self.engine.max_misses else 2 if self.engine.remaining_misses > 0 else 1
        level_index = self.engine.level_index
        self.best_stars[level_index] = max(self.best_stars.get(level_index, 0), stars)
        if level_index + 1 < len(self.engine.levels):
            self.unlocked_level = max(self.unlocked_level, level_index + 1)
        try:
            save_progress(self.progress_path, self.unlocked_level, self.best_stars)
        except OSError:
            pass
        self.clear()
        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(expand=True)
        tk.Label(wrap, text="劍", font=("STKaiti", 82, "bold"), fg=YELLOW, bg=BG).pack()
        title = f"{len(self.engine.levels)}境皆破" if game_won else "此境已破"
        detail = "剑心澄明，诸境剑阵尽数勘破" if game_won else "剑路无碍，可往下一境"
        tk.Label(wrap, text=title, font=("STKaiti", 38, "bold"), fg=WHITE, bg=BG).pack()
        tk.Label(wrap, text=detail, font=("STKaiti", 15), fg=CYAN, bg=BG).pack(pady=(10, 30))
        tk.Label(
            wrap,
            text=f"{'★' * stars}{'☆' * (3 - stars)}    积分 {self.engine.score}    用时 {self.elapsed_seconds} 秒",
            font=("Microsoft YaHei UI", 14, "bold"), fg=YELLOW, bg=BG,
        ).pack(pady=(0, 24))
        if game_won:
            self.make_button(wrap, "再入剑阵", self.start_game).pack()
            self.make_button(wrap, "境界选择", self.show_level_select, primary=False).pack(pady=8)
            self.make_button(wrap, "归返山门", self.show_start, primary=False).pack(pady=14)
        else:
            self.make_button(wrap, "前往下一境", self.go_next_level).pack()
            self.make_button(wrap, "境界选择", self.show_level_select, primary=False).pack(pady=12)

    def show_failure(self) -> None:
        self.clear()
        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(expand=True)
        tk.Label(wrap, text="封", font=("STKaiti", 72, "bold"), fg=RED, bg=BG).pack()
        tk.Label(wrap, text="问剑未成", font=("STKaiti", 38, "bold"), fg=WHITE, bg=BG).pack()
        tk.Label(
            wrap, text="剑心已耗尽，静观剑路后再来破阵",
            font=("STKaiti", 15), fg=MUTED, bg=BG,
        ).pack(pady=(10, 30))
        self.make_button(wrap, "再问此境", self.restart_level).pack()
        self.make_button(wrap, "归返山门", self.show_start, primary=False).pack(pady=14)

    def go_next_level(self) -> None:
        if self.engine.next_level():
            self.show_game()

    def restart_level(self) -> None:
        self.engine.restart_level()
        self.show_game()


def run() -> None:
    root = tk.Tk()
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Microsoft YaHei UI", size=11)
    except tk.TclError:
        pass
    ArrowGameApp(root)
    root.mainloop()
