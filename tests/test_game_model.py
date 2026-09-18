import unittest
from collections import deque

from arrow_game.levels import LEVELS
from arrow_game.model import Arrow, Direction, GameEngine, GameState, Level


class GameEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.level = Level(
            "测试关",
            3,
            3,
            (
                Arrow(1, 0, Direction.RIGHT),
                Arrow(1, 2, Direction.UP),
            ),
        )
        self.game = GameEngine((self.level,), max_misses=2)
        self.game.start()

    def test_t01_unblocked_arrow_disappears(self) -> None:
        result = self.game.click(1, 2)
        self.assertTrue(result.success)
        self.assertIsNone(self.game.arrow_at(1, 2))
        self.assertEqual(self.game.remaining_arrows, 1)

    def test_t02_blocked_arrow_stays_and_costs_a_miss(self) -> None:
        result = self.game.click(1, 0)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.blocker)
        self.assertIsNotNone(self.game.arrow_at(1, 0))
        self.assertEqual(self.game.remaining_misses, 1)

    def test_t03_boundary_arrow_exits_normally(self) -> None:
        edge = Level("边界", 2, 2, (Arrow(0, 0, Direction.UP),))
        game = GameEngine((edge,))
        game.start()
        result = game.click(0, 0)
        self.assertTrue(result.success)
        self.assertTrue(result.game_won)

    def test_t04_clear_level_and_enter_next(self) -> None:
        levels = (
            Level("一", 2, 2, (Arrow(0, 0, Direction.LEFT),)),
            Level("二", 2, 2, (Arrow(1, 1, Direction.RIGHT),)),
        )
        game = GameEngine(levels)
        game.start()
        result = game.click(0, 0)
        self.assertTrue(result.level_cleared)
        self.assertEqual(game.state, GameState.LEVEL_CLEARED)
        self.assertTrue(game.next_level())
        self.assertEqual(game.level_index, 1)
        self.assertEqual(game.state, GameState.PLAYING)

    def test_t05_misses_exhausted_causes_game_over(self) -> None:
        self.game.click(1, 0)
        result = self.game.click(1, 0)
        self.assertTrue(result.game_over)
        self.assertEqual(self.game.state, GameState.GAME_OVER)

    def test_t06_restart_restores_arrows_and_misses(self) -> None:
        self.game.click(1, 2)
        self.game.restart_level()
        self.assertEqual(self.game.remaining_arrows, 2)
        self.assertEqual(self.game.remaining_misses, 2)
        self.assertEqual(self.game.state, GameState.PLAYING)


class LevelDesignTest(unittest.TestCase):
    @staticmethod
    def has_solution(level: Level) -> bool:
        initial = frozenset(level.arrows)
        queue = deque([initial])
        seen = {initial}
        while queue:
            arrows = queue.popleft()
            if not arrows:
                return True
            engine = GameEngine((Level("搜索", level.rows, level.cols, tuple(arrows)),))
            engine.start()
            for arrow in tuple(arrows):
                if engine.find_blocker(arrow) is None:
                    next_state = arrows - {arrow}
                    if next_state not in seen:
                        seen.add(next_state)
                        queue.append(next_state)
        return False

    def test_all_levels_are_valid_and_solvable(self) -> None:
        self.assertGreaterEqual(len(LEVELS), 3)
        for level in LEVELS:
            with self.subTest(level=level.name):
                self.assertTrue(self.has_solution(level))


if __name__ == "__main__":
    unittest.main()
