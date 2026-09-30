"""
A* search on a Grid — pure Python, NO ROS in this file.

    python -m unittest tests.test_search -v

Movement rules (fixed, so the tests can check them)
---------------------------------------------------
* 8-connected: a cell has up to 8 neighbours (up, down, left, right and the 4 diagonals).
* Cost of a move: 1.0 for up/down/left/right, sqrt(2) for a diagonal. (Cost is in
  cell-widths, not metres — multiply by grid.resolution if you need metres.)
* No corner cutting: a diagonal move is only allowed if BOTH of the two cells it
  squeezes between are passable. (A real rover cannot slip between two obstacles
  that touch at a corner.)
* Cells outside the grid don't exist.
"""

import heapq
import math
from typing import List, Optional

from grid_utils import Grid, Cell
from sim.grid_values import FREE, UNKNOWN


def heuristic(a: Cell, b: Cell) -> float:
    """
    Estimate of the cost to travel from cell `a` to cell `b` on an EMPTY grid
    under the movement rules above.

    Choose and justify your choice in the README. The one hard requirement:
    it must NEVER OVERESTIMATE the true cost (that's what "admissible" means, and
    A* is only guaranteed to return the shortest path if it holds). The test
    checks this, and it is worth understanding why some very common heuristics
    fail it on an 8-connected grid.
    """
    dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dr, dc) + (math.sqrt(2.0) - 1.0) * min(dr, dc)


def astar(grid: Grid, start: Cell, goal: Cell, unknown_is_free: bool = False) -> Optional[List[Cell]]:
    """
    Find the cheapest path from `start` to `goal`.

    Args:
        grid             the grid to search. OCCUPIED cells can't be entered.
        start, goal      (row, col) cells.
        unknown_is_free  how to treat UNKNOWN cells: True = passable, False = blocked.
                         Which is right for a rover that has only seen a small
                         circle of the world so far? Look at the very first tick
                         of a run before you decide.

    Returns:
        The path as a list of (row, col) cells, INCLUDING both start and goal, or
        None if there is no path. If start == goal, returns [start].

    Things to think about (the tests poke at each):
      * What if the goal is occupied?
      * The rover might already be standing on a cell that your obstacle
        inflation marked as blocked. Should search refuse to leave it?
      * Speed: a 100 x 100 grid must finish in well under a second. What data
        structure makes "give me the cheapest open node" fast?
    """
    if not grid.in_bounds(*start) or not grid.in_bounds(*goal):
        return None
    # No movement is necessary, even if inflation covers the current cell.
    if start == goal:
        return [start]

    def passable(cell):
        return grid.in_bounds(*cell) and (
            grid.get(*cell) == FREE or (unknown_is_free and grid.get(*cell) == UNKNOWN)
        )

    if not passable(goal):
        return None
    costs = {start: 0.0}
    parents = {}
    frontier = [(heuristic(start, goal), 0.0, start)]
    moves = [(dr, dc, math.sqrt(2.0) if dr and dc else 1.0)
             for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while frontier:
        _, cost, current = heapq.heappop(frontier)
        if cost != costs[current]:
            continue  # An improved entry for this cell superseded this one.
        if current == goal:
            path = [current]
            while current != start:
                current = parents[current]
                path.append(current)
            return path[::-1]
        row, col = current
        for dr, dc, move_cost in moves:
            neighbour = (row + dr, col + dc)
            if not passable(neighbour):
                continue
            if dr and dc and not (passable((row + dr, col)) and
                                  passable((row, col + dc))):
                continue
            candidate = cost + move_cost
            if candidate < costs.get(neighbour, math.inf):
                costs[neighbour] = candidate
                parents[neighbour] = current
                heapq.heappush(frontier, (candidate + heuristic(neighbour, goal),
                                         candidate, neighbour))
    return None
