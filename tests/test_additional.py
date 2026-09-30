"""Additional contracts and node integration tests; supplied tests are untouched."""
import heapq
import logging
import math
import random
import unittest
from unittest.mock import patch

from grid_utils import Grid, inflate
from search import astar
from planner_node import PlannerNode, planning_grid
from sim.messages import GridSnapshot, path_msg_to_points
from sim.grid_values import FREE, OCCUPIED, UNKNOWN
import rclpy_lite as rclpy
from rclpy_lite.node import Node
from rclpy_lite.qos import QoSProfile, ReliabilityPolicy
from nav_msgs.msg import Path
from sim.launch import make_sim


def snapshot():
    msg = GridSnapshot(width=12, height=8, resolution=0.5,
                       origin_x=-3.0, origin_y=-2.0,
                       occupancy=[FREE] * 96, confidence=[1.0] * 96,
                       rover_x=-1.75, rover_y=-0.75,
                       goal_x=1.75, goal_y=-0.75, robot_radius_m=0.5)
    msg.header.stamp = 0.0
    return msg


class TestAdditionalGridAndSearch(unittest.TestCase):
    def test_optimal_cost_against_independent_dijkstra(self):
        for seed in range(40):
            rng = random.Random(seed)
            grid = Grid(9, 7, 0.3, -2.0, 1.0,
                        [OCCUPIED if rng.random() < 0.23 else FREE for _ in range(63)])
            start, goal = (0, 0), (6, 8)
            grid.occupancy[0] = grid.occupancy[-1] = FREE
            distance = {start: 0.0}
            queue = [(0.0, start)]
            while queue:
                cost, (r, c) = heapq.heappop(queue)
                if cost > distance[(r, c)]:
                    continue
                for rr in range(max(0, r - 1), min(grid.height, r + 2)):
                    for cc in range(max(0, c - 1), min(grid.width, c + 2)):
                        if (rr, cc) == (r, c) or grid.is_occupied(rr, cc):
                            continue
                        if rr != r and cc != c and (grid.is_occupied(rr, c) or grid.is_occupied(r, cc)):
                            continue
                        new_cost = cost + math.hypot(rr - r, cc - c)
                        if new_cost < distance.get((rr, cc), math.inf):
                            distance[(rr, cc)] = new_cost
                            heapq.heappush(queue, (new_cost, (rr, cc)))
            path = astar(grid, start, goal)
            with self.subTest(seed=seed):
                if goal not in distance:
                    self.assertIsNone(path)
                else:
                    self.assertIsNotNone(path)
                    self.assertAlmostEqual(sum(math.dist(a, b) for a, b in zip(path, path[1:])),
                                           distance[goal])

    def test_fractional_radius_rounds_outward_without_cascading(self):
        grid = Grid.from_ascii([".......", "...#...", "......."], resolution=0.5)
        out = inflate(grid, 0.6)
        self.assertTrue(out.is_occupied(1, 5))
        self.assertFalse(out.is_occupied(1, 6))
        self.assertFalse(grid.is_occupied(1, 5))
        out.confidence[0] = 0.4
        self.assertEqual(grid.confidence[0], 1.0)

    def test_unknown_corner_obeys_traversal_policy(self):
        grid = Grid.from_ascii(["..", ".?"])
        self.assertEqual(astar(grid, (0, 0), (1, 1)), [(0, 0), (1, 0), (1, 1)])
        self.assertEqual(astar(grid, (0, 0), (1, 1), True), [(0, 0), (1, 1)])

    def test_same_blocked_start_and_goal_needs_no_movement(self):
        self.assertEqual(astar(Grid.from_ascii(["#"]), (0, 0), (0, 0)), [(0, 0)])

    def test_arena_margin_is_separate_from_generic_inflation(self):
        msg = snapshot()
        self.assertFalse(inflate(Grid.from_msg(msg), 0.5).is_occupied(0, 0))
        prepared = planning_grid(msg)
        self.assertTrue(prepared.is_occupied(0, 0))
        self.assertTrue(prepared.is_occupied(7, 11))
        self.assertFalse(prepared.is_occupied(1, 1))
        self.assertEqual(msg.occupancy, [FREE] * 96)


class TestPlannerMessages(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.feed = Node("test_feed")
        self.pub = self.feed.create_publisher(
            GridSnapshot, "/grid_feed",
            QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=1))
        self.messages = []
        self.listener = Node("test_listener")
        self.listener.create_subscription(Path, "/planned_path", self.messages.append, 10)
        self.planner = PlannerNode()

    def tearDown(self):
        self.planner.destroy_node()
        self.listener.destroy_node()
        self.feed.destroy_node()
        rclpy.shutdown()

    def test_initial_unknown_route_published_once_with_sim_stamp(self):
        msg = snapshot()
        msg.occupancy = [UNKNOWN] * 96
        msg.confidence = [0.0] * 96
        msg.header.stamp = 7.0
        self.pub.publish(msg)
        msg.header.stamp = 8.0
        self.pub.publish(msg)
        self.assertTrue(self.planner.grid_sub.connected)
        self.assertEqual(len(self.messages), 1)
        path = self.messages[0]
        self.assertEqual(path.header.stamp, 7.0)
        self.assertEqual(path.header.frame_id, "map")
        self.assertEqual(path_msg_to_points(path)[-1], (msg.goal_x, msg.goal_y))
        self.assertEqual(self.planner.plan_count, 1)
        self.assertEqual(self.planner.replan_count, 0)

    def test_stop_once_wait_without_research_and_recover(self):
        msg = snapshot()
        self.pub.publish(msg)
        goal_cell = Grid.from_msg(msg).world_to_cell(msg.goal_x, msg.goal_y)
        msg.occupancy[goal_cell[0] * msg.width + goal_cell[1]] = OCCUPIED
        msg.header.stamp = 1.0
        with patch.object(self.planner, "plan", wraps=self.planner.plan) as search:
            self.pub.publish(msg)
            self.assertEqual(path_msg_to_points(self.messages[-1]), [])
            self.assertEqual(search.call_count, 1)
            for tick in range(2, 6):
                msg.header.stamp = float(tick)
                msg.confidence = [0.2] * 96  # Part 1 ignores confidence-only changes.
                self.pub.publish(msg)
            self.assertEqual(search.call_count, 1)
            self.assertEqual(len(self.messages), 2)
            msg.occupancy[goal_cell[0] * msg.width + goal_cell[1]] = FREE
            msg.header.stamp = 6.0
            self.pub.publish(msg)
            self.assertEqual(search.call_count, 2)
        self.assertTrue(path_msg_to_points(self.messages[-1]))
        self.assertEqual(len(self.messages), 3)
        self.assertEqual(self.planner.plan_count, 2)
        self.assertEqual(self.planner.replan_count, 0)  # Recovery is not a replan.

    def test_obstacle_behind_and_off_path_do_not_publish(self):
        msg = snapshot()
        self.pub.publish(msg)
        msg.rover_x = 0.75
        msg.occupancy[2 * msg.width + 2] = OCCUPIED  # Behind current position.
        msg.occupancy[6 * msg.width + 8] = OCCUPIED  # Far above the route.
        msg.header.stamp = 1.0
        self.pub.publish(msg)
        self.assertEqual(len(self.messages), 1)

    def test_diagonal_side_cell_change_invalidates_route(self):
        grid = Grid.from_ascii(["...."] * 4)
        self.planner.path_xy = [(0.5, 0.5), (1.5, 1.5), (2.5, 2.5)]
        grid.occupancy[grid.index(1, 2)] = OCCUPIED
        self.assertTrue(self.planner.needs_replan(grid, (0.5, 0.5))[0])


class TestSimulationRecovery(unittest.TestCase):
    def test_temporary_goal_block_stops_and_recovers_safely(self):
        # Test-only access to the scoreboard; production never imports the world.
        run = make_sim("goal-blocked", 0, False)
        previous_level = logging.root.manager.disable
        logging.disable(logging.INFO)
        try:
            run.run()
            self.assertEqual(run.outcome, "REACHED")
            self.assertEqual(run.rover.blocked_ticks, 0)
            self.assertEqual(run.score.needless, 0)
            self.assertEqual(run.node.replan_count, run.score.replans)
            stops = [e for e in run.score.events if e.kind == "stop"]
            recoveries = [e for e in run.score.events if e.kind == "recovery"]
            self.assertEqual(len(stops), 1)
            self.assertEqual(len(recoveries), 1)
            self.assertAlmostEqual(recoveries[0].t - stops[0].t, 8.0)
            self.assertEqual(run.empty_paths_seen, 1)
        finally:
            run.node.destroy_node()
            rclpy.shutdown()
            logging.disable(previous_level)
