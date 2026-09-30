"""Controlled ablations for the README; changes exist only inside mock contexts."""
import logging
import math
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grid_utils import Grid
import search
import planner_node
from sim.launch import make_sim
import rclpy_lite as rclpy


def cost(path):
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


def run_case(label, scenario):
    run = make_sim(scenario, 0, False)
    try:
        run.run()
        print(f'{label}: {run.outcome}, ticks={run.tick}, '
              f'blocked={run.rover.blocked_ticks}, plans={run.score.plans}, '
              f'replans={run.score.replans}, needless={run.score.needless}')
    finally:
        run.node.destroy_node()
        rclpy.shutdown()


def main():
    rows = ['........', '....#...', '.#......', '#.......',
            '.......#', '.#.#..#.', '......#.', '...#....']
    grid = Grid.from_ascii(rows)
    optimal = cost(search.astar(grid, (0, 0), (7, 7)))
    with patch('search.heuristic', lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])):
        overestimate = cost(search.astar(grid, (0, 0), (7, 7)))
    print(f'8x8 synthetic fixture: octile={optimal:.6f}, Manhattan={overestimate:.6f}')
    logging.disable(logging.INFO)
    try:
        original = search.astar
        with patch('planner_node.astar', lambda grid, start, goal, **kw:
                   original(grid, start, goal, unknown_is_free=False)):
            run_case('unknown blocked', 'open')
        with patch('planner_node.planning_grid', lambda msg: Grid.from_msg(msg)):
            run_case('no obstacle inflation or edge margin', 'wall')
    finally:
        logging.disable(logging.NOTSET)


if __name__ == '__main__':
    main()
