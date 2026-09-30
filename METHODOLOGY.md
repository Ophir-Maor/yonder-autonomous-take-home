# Methodology

## How to run

Tested with Python 3.13.15 on macOS (Darwin 25.3.0, Apple Silicon).
The implementation uses the standard library. NumPy and Matplotlib are needed
only for images. Run from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
python sim/launch.py --scenario open
python sim/launch.py --all
python tools/validate.py --seeds 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 42 99 100 223 999 2026 12345 123456
python tools/experiments.py
python sim/launch.py --scenario wall --save-png /tmp/yonder-wall.png
```

On Windows use `.venv\Scripts\activate` and a local output image filename.
For a live window use `python sim/launch.py --scenario popup --visualize`.
If Matplotlib cannot write its cache, set `MPLCONFIGDIR` to a writable temporary
directory. No ROS installation or external services are required.

`tools/validate.py` fails with a nonzero exit code if any selected run fails to
reach the goal, has blocked ticks, has needless replans, or disagrees with the
node's replan counter. The supplied launcher prints results but does not enforce
those assertions. `tools/experiments.py` intentionally runs inferior policies;
its stalled scenarios demonstrate failures, not expected normal behaviour.

## Thought process and architecture

Codex performed this implementation, testing, and write-up under the user's
explicit autonomous request. The user should review and understand the choices
before submission; this document does not claim independent human authorship.

- Keep coordinate maths, search, and waypoint validation in pure Python. The
  node connects the sensor snapshot to those helpers and publishes world points.
- Floor relative world coordinates; return cell centres; keep `(row, col)` and
  `(x, y)` visibly distinct. Honour each message's origin, dimensions, resolution,
  and planning radius rather than assuming the demonstration arena.
- Use heap-based A* with octile distance. Its estimate is exact in an empty
  eight-connected grid and consistent with cardinal/diagonal costs. Track best
  costs, skip obsolete heap entries, and reconstruct through parent pointers.
- Permit escape from an occupied start, but do not enter occupied neighbours.
  For an in-bounds start equal to goal return the one-cell path even if occupied:
  no movement is needed. This resolves an ambiguity in the starter contracts.
- Inflate occupied cells into a copied grid using a square neighbourhood rounded
  outward. Apply arena-edge exclusions separately in the node, preserving the
  generic inflation contract. Both planning and validation use this prepared grid.
- Unknown means unexplored, not blocked. Without optimistic traversal, the
  initial goal is unreachable and the stationary rover never sees more terrain.
  Part 1 ignores confidence, including confidence-only changes.
- Preserve a safe route even when a newly observed route might be shorter. Check
  the remaining waypoints and the side cells of remaining diagonal steps.
  This catches changes to diagonal clearance even if endpoints remain free.
- Distinguish never planned (`None`), stopped (`[]`), and active route. Publish an
  empty command immediately on route failure; then retry when the effective
  blocked map, grid geometry, start cell, or goal changes. Unknown-to-free and
  confidence-only changes do not cause redundant no-route searches.
- Count nonempty-to-nonempty publications as replans; stop and recovery are
  separate events. Suppress identical commands. Display total published route
  length (not remaining distance), with elapsed replan time from sensor stamps.
- Validate helper contracts before integration; supplement supplied tests with
  message-level checks and independent Dijkstra comparisons on 40 small maps.
  Scenario validation includes temporary goal blockage and obstacles behind the
  rover, and a reproducible batch driver checks unseen-style random worlds.
- Controlled ablations show the cost of unsafe choices: treating unknown as
  blocked stalls `open`; disabling all clearance stalls `wall`; Manhattan
  distance returns a longer path on an explicit 8x8 fixture. See README results.

## Limitations and next steps

- This is the required clean-sensor Part 1 solution. No confidence filter,
  weighted-cost search, Theta*, or Webots integration is implemented. No claim
  is made about reliable operation with `--noise`.
- Square, rounded inflation is conservative and can reject narrow passages.
  Centre-based grid inflation is an approximation to continuous disc clearance,
  especially for other resolutions/radii; it is not a general geometry proof.
- Nearest-waypoint progress is the specified approximation, appropriate for these
  dense A* paths. It is not a robust tracker for looping or self-crossing routes.
  Segment checks support adjacent grid steps, not arbitrary long shortcuts.
- An occupied-start exception allows search to leave an inflated cell; it cannot
  guarantee safe escape from every physically overlapping obstacle arrangement.
- The provided world has a fixed goal and grid geometry. No active-route goal
  retargeting or general rolling-map controller is implemented; no-route retries
  do include changed goal/geometry in their search inputs.
- Replanning only when invalidated sacrifices global optimality as knowledge
  improves. Partially revealed obstacles can legitimately cause several replans.
- Failure caching retries on any effective blocked-map change, even an unrelated
  one. A reachability-aware change filter could reduce work on larger grids.
- Test results cover the recorded deterministic cases and seeds, not all possible
  worlds. A clean sensor and these event rules provide time to react; a generic
  obstacle appearing directly underneath the rover would require other handling.

See the README write-up for measured outcomes and AI_LOG.md for the work record.

A clean tracked export of code commit `1293852` was also tested from a separate
`/tmp` directory with the existing `.venv` interpreter and no `PYTHONPATH`:
59 tests passed, all eight `--all` rows matched, and the ablation script reproduced
its documented results. Dependencies were reused, not reinstalled in this check.
