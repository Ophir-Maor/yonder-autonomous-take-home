"""ROS-style wiring for the grid planner; launch with python sim/launch.py."""

# Import sim first so its message/shim packages also resolve in direct imports.
from sim.messages import GridSnapshot, make_path_msg
from sim.grid_values import OCCUPIED
from rclpy_lite.node import Node
from rclpy_lite.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import Path

from grid_utils import Grid, inflate, path_length_m
from search import astar
from replan import next_waypoint_index, path_is_valid


def planning_grid(msg: GridSnapshot) -> Grid:
    """Inflate observed obstacles and exclude centres too close to arena walls."""
    grid = inflate(Grid.from_msg(msg), msg.robot_radius_m)
    for row in range(grid.height):
        for col in range(grid.width):
            edge_distance = min(row + 0.5, col + 0.5,
                                grid.height - row - 0.5, grid.width - col - 0.5)
            if edge_distance * grid.resolution < msg.robot_radius_m:
                grid.occupancy[grid.index(row, col)] = OCCUPIED
    return grid


class PlannerNode(Node):
    """Keep a world-coordinate route and publish only changes to the command."""

    def __init__(self):
        super().__init__("planner_node")
        self.path_pub = self.create_publisher(Path, "/planned_path", 10)
        self.grid_sub = self.create_subscription(
            GridSnapshot, "/grid_feed", self.on_grid,
            QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                       durability=DurabilityPolicy.VOLATILE, depth=1))
        self.path_xy = None  # None = never planned; [] = stopped without a route.
        self.plan_count = 0
        self.replan_count = 0
        self.last_replan_stamp = None
        self._last_status_stamp = None

    def on_grid(self, msg: GridSnapshot) -> None:
        grid = planning_grid(msg)
        rover_xy = (msg.rover_x, msg.rover_y)
        goal_xy = (msg.goal_x, msg.goal_y)
        needed, reason = self.needs_replan(grid, rover_xy)
        if needed:
            points = self.plan(grid, rover_xy, goal_xy)
            if points != self.path_xy:
                if points:
                    self.plan_count += 1
                    if self.path_xy:
                        self.replan_count += 1
                        self.last_replan_stamp = msg.header.stamp
                self.path_xy = points
                self.publish_path(points, msg.header.stamp)
                self.get_logger().info(f"t={msg.header.stamp:.1f}s: {reason}; "
                                       f"{'route' if points else 'stop: no route'}")
                self._last_status_stamp = None
        self.print_status(msg.header.stamp)

    def needs_replan(self, grid: Grid, rover_xy) -> tuple:
        """Initial integration: issue one route; dynamic replanning follows."""
        return self.path_xy is None, "initial plan"

    def plan(self, grid: Grid, rover_xy, goal_xy):
        """Search in cells, return cell centres in world metres (or [] to stop)."""
        cells = astar(grid, grid.world_to_cell(*rover_xy),
                      grid.world_to_cell(*goal_xy), unknown_is_free=True)
        return [] if cells is None else [grid.cell_to_world(*cell) for cell in cells]

    def publish_path(self, points_xy, stamp: float) -> None:
        self.path_pub.publish(make_path_msg(points_xy, stamp))

    def print_status(self, stamp: float) -> None:
        if self._last_status_stamp is not None and stamp - self._last_status_stamp < 1.0 - 1e-9:
            return
        elapsed = ("n/a" if self.last_replan_stamp is None else
                   f"{stamp - self.last_replan_stamp:.1f}s")
        self.get_logger().info(
            f"t={stamp:.1f}s path={path_length_m(self.path_xy or []):.2f}m "
            f"replans={self.replan_count} since_last_replan={elapsed}")
        self._last_status_stamp = stamp
