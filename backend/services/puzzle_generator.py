import random

# 81-element list; 0 = empty
Grid = list[int]

# Precompute peer sets for all 81 cells
def _build_peers() -> list[frozenset[int]]:
    peers: list[frozenset[int]] = []
    for i in range(81):
        r, c = i // 9, i % 9
        box_r, box_c = (r // 3) * 3, (c // 3) * 3
        group: set[int] = set()
        for j in range(9):
            group.add(r * 9 + j)       # same row
            group.add(j * 9 + c)       # same col
            group.add((box_r + j // 3) * 9 + (box_c + j % 3))  # same box
        group.discard(i)
        peers.append(frozenset(group))
    return peers

_PEERS: list[frozenset[int]] = _build_peers()

# How many cells to remove per difficulty
_REMOVALS: dict[str, tuple[int, int]] = {
    "easy":   (30, 35),
    "medium": (40, 46),
    "hard":   (51, 57),
}


def generate_solved_grid() -> Grid:
    """Return a complete, randomly filled valid 9×9 grid (81 ints, 1-9)."""
    grid: Grid = [0] * 81
    _backtrack_fill(grid)
    return grid


def _backtrack_fill(grid: Grid) -> bool:
    try:
        i = grid.index(0)
    except ValueError:
        return True

    digits = list(range(1, 10))
    random.shuffle(digits)
    used = {grid[p] for p in _PEERS[i] if grid[p]}
    for n in digits:
        if n not in used:
            grid[i] = n
            if _backtrack_fill(grid):
                return True
            grid[i] = 0
    return False


def has_unique_solution(givens: Grid) -> bool:
    """Return True iff *givens* has exactly one valid completion."""
    counter = [0]
    _count_solutions(list(givens), counter)
    return counter[0] == 1


def _count_solutions(grid: Grid, counter: list[int]) -> None:
    """Backtracking solution counter; stops as soon as count reaches 2."""
    if counter[0] > 1:
        return

    # MRV: choose empty cell with fewest candidates
    best_i = -1
    best_n = 10
    for i in range(81):
        if grid[i] == 0:
            used = {grid[p] for p in _PEERS[i] if grid[p]}
            n = 9 - len(used)
            if n < best_n:
                best_n = n
                best_i = i
                if best_n == 0:
                    return  # dead end

    if best_i == -1:
        counter[0] += 1
        return

    used = {grid[p] for p in _PEERS[best_i] if grid[p]}
    for digit in range(1, 10):
        if digit not in used:
            grid[best_i] = digit
            _count_solutions(grid, counter)
            grid[best_i] = 0
            if counter[0] > 1:
                return


def make_puzzle(grid: Grid, difficulty: str) -> tuple[Grid, Grid]:
    """
    Carve cells from *grid* to produce a uniquely-solvable puzzle at the
    requested difficulty tier.

    Returns ``(givens, solution)`` where *givens* has 0 for empty cells and
    *solution* is the original complete grid.
    """
    min_remove, max_remove = _REMOVALS.get(difficulty, _REMOVALS["medium"])
    target = random.randint(min_remove, max_remove)

    solution: Grid = list(grid)
    puzzle: Grid = list(grid)

    indices = list(range(81))
    random.shuffle(indices)

    removed = 0
    for i in indices:
        if removed >= target:
            break
        backup = puzzle[i]
        puzzle[i] = 0
        if has_unique_solution(puzzle):
            removed += 1
        else:
            puzzle[i] = backup

    return puzzle, solution
