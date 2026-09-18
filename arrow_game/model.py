from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Direction(str, Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]

    @property
    def symbol(self) -> str:
        return {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.LEFT: "←",
            Direction.RIGHT: "→",
        }[self]


@dataclass(frozen=True)
class Arrow:
    row: int
    col: int
    direction: Direction


@dataclass(frozen=True)
class Level:
    name: str
    rows: int
    cols: int
    arrows: tuple[Arrow, ...]

    def __post_init__(self) -> None:
        positions: set[tuple[int, int]] = set()
        for arrow in self.arrows:
            if not (0 <= arrow.row < self.rows and 0 <= arrow.col < self.cols):
                raise ValueError(f"箭头超出棋盘：{arrow}")
            if (arrow.row, arrow.col) in positions:
                raise ValueError(f"同一格不能放置两个箭头：{arrow.row, arrow.col}")
            positions.add((arrow.row, arrow.col))


class GameState(str, Enum):
    READY = "ready"
    PLAYING = "playing"
    LEVEL_CLEARED = "level_cleared"
    GAME_WON = "game_won"
    GAME_OVER = "game_over"


@dataclass(frozen=True)
class MoveResult:
    success: bool
    message: str
    arrow: Arrow | None = None
    blocker: Arrow | None = None
    level_cleared: bool = False
    game_won: bool = False
    game_over: bool = False


class GameEngine:
    """只负责游戏规则，不依赖图形界面，便于测试。"""

    def __init__(self, levels: Iterable[Level], max_misses: int = 3) -> None:
        self.levels = tuple(levels)
        if not self.levels:
            raise ValueError("至少需要一个关卡")
        if max_misses < 1:
            raise ValueError("最大失误次数必须大于 0")
        self.max_misses = max_misses
        self.level_index = 0
        self.state = GameState.READY
        self.remaining_misses = max_misses
        self._arrows: dict[tuple[int, int], Arrow] = {}
        self._load_level(0)

    @property
    def level(self) -> Level:
        return self.levels[self.level_index]

    @property
    def arrows(self) -> tuple[Arrow, ...]:
        return tuple(self._arrows.values())

    @property
    def remaining_arrows(self) -> int:
        return len(self._arrows)

    def start(self) -> None:
        self.state = GameState.PLAYING

    def _load_level(self, index: int) -> None:
        self.level_index = index
        self._arrows = {(a.row, a.col): a for a in self.levels[index].arrows}
        self.remaining_misses = self.max_misses

    def restart_level(self) -> None:
        self._load_level(self.level_index)
        self.state = GameState.PLAYING

    def restart_game(self) -> None:
        self._load_level(0)
        self.state = GameState.PLAYING

    def next_level(self) -> bool:
        if self.level_index + 1 >= len(self.levels):
            return False
        self._load_level(self.level_index + 1)
        self.state = GameState.PLAYING
        return True

    def arrow_at(self, row: int, col: int) -> Arrow | None:
        return self._arrows.get((row, col))

    def find_blocker(self, arrow: Arrow) -> Arrow | None:
        dr, dc = arrow.direction.delta
        blockers: list[tuple[int, Arrow]] = []
        for candidate in self._arrows.values():
            if candidate == arrow:
                continue
            row_gap = candidate.row - arrow.row
            col_gap = candidate.col - arrow.col
            if dr and col_gap == 0 and row_gap * dr > 0:
                blockers.append((abs(row_gap), candidate))
            elif dc and row_gap == 0 and col_gap * dc > 0:
                blockers.append((abs(col_gap), candidate))
        return min(blockers, key=lambda item: item[0])[1] if blockers else None

    def click(self, row: int, col: int) -> MoveResult:
        if self.state != GameState.PLAYING:
            return MoveResult(False, "游戏当前不可操作")

        arrow = self.arrow_at(row, col)
        if arrow is None:
            return MoveResult(False, "这里没有箭头")

        blocker = self.find_blocker(arrow)
        if blocker is not None:
            self.remaining_misses -= 1
            game_over = self.remaining_misses <= 0
            if game_over:
                self.state = GameState.GAME_OVER
            return MoveResult(
                False,
                "前方有箭头阻挡！",
                arrow=arrow,
                blocker=blocker,
                game_over=game_over,
            )

        del self._arrows[(row, col)]
        if not self._arrows:
            is_last = self.level_index == len(self.levels) - 1
            self.state = GameState.GAME_WON if is_last else GameState.LEVEL_CLEARED
            return MoveResult(
                True,
                "三境皆破！" if is_last else "此境已破！",
                arrow=arrow,
                level_cleared=True,
                game_won=is_last,
            )
        return MoveResult(True, "飞剑破阵而出", arrow=arrow)
