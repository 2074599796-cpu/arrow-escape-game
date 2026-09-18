from .model import Arrow, Direction, Level

U = Direction.UP
D = Direction.DOWN
L = Direction.LEFT
R = Direction.RIGHT


LEVELS = (
    Level(
        "骊珠洞天",
        5,
        5,
        (
            Arrow(2, 0, R), Arrow(2, 2, U), Arrow(0, 2, U),
            Arrow(4, 2, D), Arrow(2, 4, R), Arrow(3, 2, D),
        ),
    ),
    Level(
        "山水问剑",
        6,
        6,
        (
            Arrow(3, 0, R), Arrow(3, 2, U), Arrow(1, 2, L),
            Arrow(1, 0, L), Arrow(3, 5, R), Arrow(5, 4, D),
            Arrow(4, 4, D), Arrow(1, 4, R), Arrow(4, 1, L),
            Arrow(2, 4, U), Arrow(5, 1, U),
        ),
    ),
    Level(
        "剑气长城",
        7,
        7,
        (
            Arrow(3, 0, R), Arrow(3, 2, U), Arrow(0, 2, U),
            Arrow(3, 4, D), Arrow(6, 4, D), Arrow(3, 6, R),
            Arrow(1, 0, L), Arrow(1, 3, R), Arrow(1, 6, R),
            Arrow(5, 0, L), Arrow(5, 3, L), Arrow(5, 6, R),
            Arrow(0, 5, U), Arrow(2, 5, U), Arrow(4, 1, D),
            Arrow(6, 1, D),
        ),
    ),
)
