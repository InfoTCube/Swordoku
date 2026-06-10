from enum import Enum

from .puzzle_generator import Grid, _PEERS

# fmt: off
_UNITS: list[list[int]] = (
    [[r * 9 + c for c in range(9)] for r in range(9)] +        # rows
    [[r * 9 + c for r in range(9)] for c in range(9)] +        # cols
    [
        [(box_r + dr) * 9 + (box_c + dc)
         for dr in range(3) for dc in range(3)]
        for box_r in range(0, 9, 3)
        for box_c in range(0, 9, 3)
    ]
)
# fmt: on


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


def _compute_candidates(grid: Grid) -> list[set[int]]:
    return [
        set()
        if grid[i] != 0
        else {d for d in range(1, 10) if d not in {grid[p] for p in _PEERS[i] if grid[p]}}
        for i in range(81)
    ]


def _solve_with_singles(givens: Grid) -> tuple[int, int, int]:
    """
    Simulate a human solver using only naked singles and hidden singles.
    Returns (naked_count, hidden_count, remaining_empty_cells).
    """
    grid = list(givens)
    naked_count = 0
    hidden_count = 0

    changed = True
    while changed:
        changed = False
        candidates = _compute_candidates(grid)

        # Naked singles: cells with exactly one candidate
        for i in range(81):
            if grid[i] == 0 and len(candidates[i]) == 1:
                grid[i] = next(iter(candidates[i]))
                naked_count += 1
                changed = True

        if changed:
            continue  # recompute candidates before looking for hidden singles

        # Hidden singles: a digit fits in only one cell within a unit.
        # Update candidates after each placement so later units in the same pass
        # don't see stale positions for the placed digit.
        for unit in _UNITS:
            for d in range(1, 10):
                positions = [i for i in unit if grid[i] == 0 and d in candidates[i]]
                if len(positions) == 1:
                    cell = positions[0]
                    grid[cell] = d
                    candidates[cell] = set()
                    for peer in _PEERS[cell]:
                        candidates[peer].discard(d)
                    hidden_count += 1
                    changed = True

    return naked_count, hidden_count, sum(1 for v in grid if v == 0)


def classify_difficulty(givens: Grid) -> Difficulty:
    """
    Classify a puzzle as easy / medium / hard.

    Uses three signals:
    - given_count: pre-filled cells (fewer → harder)
    - hidden_count: hidden-single steps required during simulation (more → harder)
    - remaining: cells still empty after exhausting naked/hidden singles
      (any residual means advanced techniques are needed → hard)

    Thresholds align with the generator's removal ranges:
      easy   46-51 givens  (30-35 removed)
      medium 35-41 givens  (40-46 removed)
      hard   24-30 givens  (51-57 removed)
    """
    given_count = sum(1 for v in givens if v != 0)
    naked_count, hidden_count, remaining = _solve_with_singles(givens)

    if remaining > 0 or given_count <= 30:
        return Difficulty.hard

    # Easy: many givens and the puzzle leans on naked singles over hidden ones.
    if given_count >= 46 and hidden_count <= 5:
        return Difficulty.easy

    return Difficulty.medium
