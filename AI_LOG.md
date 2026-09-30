# AI Usage Log

I used Codex as an AI-assisted development tool throughout this assessment. My goal was to use it to accelerate implementation and experimentation while keeping the work grounded in the assignment's requirements and observable simulator behavior.

I began by having Codex analyze the starter repository without making changes. I used that analysis to understand the system architecture, identify important contracts and edge cases, and establish an incremental development plan covering grid utilities, A* search, replanning, planner integration, scenario testing, and documentation.

I then used Codex to carry out substantial parts of the implementation within that workflow. I gave it explicit constraints to preserve the provided simulator and tests, work incrementally, test each stage independently, maintain meaningful commit history, record incorrect assumptions and corrections, and avoid handling final submission. I treated passing tests and simulator behavior as the source of truth rather than assuming generated code was correct.

After the implementation was completed, I independently ran the complete test suite and required simulator scenarios, reviewed the repository and commit history, and verified the public repository before submission.

The sections below document where AI contributed, how its output was validated, and where testing caused assumptions or approaches to be revised.

## 1. Repository Analysis and Planning

**Task:** Analyze the starter repository and explain its architecture, contracts, implementation order, and likely pitfalls without modifying files.

This analysis helped identify the separation between grid utilities, search, replanning helpers, and planner-node integration. It also surfaced several implementation details that became important later, including:

- world `(x, y)` versus grid `(row, col)` coordinate conventions
- optimistic traversal of unknown space
- keeping arena-boundary clearance separate from generic obstacle inflation
- diagonal movement and corner-cutting constraints
- QoS compatibility between the grid feed and planner
- distinguishing replanning from stop/recovery behavior
- validating only the remaining route rather than reacting to irrelevant changes behind the rover

No implementation changes were made during this stage.

**Baseline verification:** The initial repository produced 49 tests with 48 expected errors because the starter functions were intentionally unimplemented.

## 2. Grid Utilities

**Implemented with Codex:** World-to-cell conversion using flooring, cell-to-world conversion using cell centers, and non-mutating obstacle inflation.

A key design choice was keeping arena-edge clearance outside the generic inflation helper. This allowed the helper to satisfy its general tested contract while the planner could separately apply the physical clearance needed for safe navigation.

**Verification:** All 17 `tests.test_grid_utils` tests passed.

## 3. A* Search

**Implemented with Codex:** A heap-based A* search with:

- octile-distance heuristic
- eight-connected movement
- cardinal cost `1`
- diagonal cost `sqrt(2)`
- best-known cost tracking
- parent-based path reconstruction
- configurable traversal of unknown cells
- occupied-start escape
- diagonal corner-cut prevention

Octile distance was selected because it matches the geometry of an eight-connected grid more closely than Manhattan distance while remaining admissible for the movement model.

**Verification:** All 18 `tests.test_search` tests passed, including the optimality and 150x150 performance tests.

Because Git identity was not configured in the environment, Codex used `Codex <codex@localhost>` for its implementation commits rather than inventing my identity. I left those commits intact so the repository history accurately reflects the AI-assisted workflow.

## 4. Replanning Helpers

**Implemented with Codex:** Nearest-waypoint selection with lower-index tie breaking and validation of the remaining route against newly occupied or out-of-bounds cells.

Unknown cells remain valid because Part 1 requires the planner to navigate beyond the currently observed region.

The helper functions intentionally follow the provided waypoint-based contract. Additional diagonal-clearance checks are handled during planner integration where more route context is available.

**Verification:** All 14 `tests.test_replan` tests passed.

## 5. Initial Planner Integration

The helper components were then integrated into the planner node.

**Implemented with Codex:**

- best-effort grid-feed subscription
- reliable path publication
- explicit arena-boundary clearance
- optimistic traversal of unknown terrain
- cell-center waypoints
- simulated-time monitoring
- initial route generation

The first target was intentionally the simplest scenario: `open`. This provided an integration check without introducing dynamic replanning behavior.

**Verification:** All 49 provided tests passed.

The `open` scenario reached the goal in 121 ticks with:

- 1 initial plan
- 0 replans
- 0 blocked ticks
- 0 needless replans

This established a working baseline before adding dynamic behavior.

## 6. Dynamic Replanning

Before running `boulders`, I preserved a prediction of **3 replans** based on the expectation that each major newly discovered obstacle would require approximately one meaningful route revision.

That prediction was committed before observing the scenario result.

**Implemented with Codex:**

- validation of the remaining route
- diagonal-side clearance checks
- replanning only when the active route becomes invalid
- empty-path stop commands when no safe route exists
- recovery planning when relevant planning inputs change
- suppression of identical path publications

### Prediction vs. observation

The `boulders` scenario actually required **11 replans**, not 3.

It reached the goal in 127 ticks with:

- 12 total nonempty plans
- 11 replans
- 0 blocked ticks
- 0 needless replans

The prediction underestimated how frequently incremental sensor observations would change the validity of the current route. A single physical obstacle can reveal multiple relevant occupied cells over time, and newly observed diagonal-clearance constraints can also invalidate the remaining path.

I kept the original prediction and its commit rather than modifying it after seeing the result.

The `wall` scenario reached the goal in 136 ticks with 18 replans, also with zero blocked ticks and zero needless replans.

## 7. Stop, Recovery, and Edge Cases

The next focus was behavior that cannot be handled by simply generating another nonempty path.

For an invalid route with no currently available replacement, the planner publishes an empty path so the rover stops rather than continuing to execute a stale unsafe command. Planning can resume when relevant traversability changes.

### Popup

`popup` reached the goal in 129 ticks with:

- 3 nonempty plans
- 2 replans
- 0 blocked ticks
- 0 needless replans

The obstacle introduced behind the rover did not trigger an unnecessary path publication.

### Goal-blocked

`goal-blocked` reached the goal in 167 ticks with:

- 5 nonempty plans
- 3 replans
- 0 blocked ticks
- 0 needless replans

The planner stopped when the goal became unreachable and recovered after the goal became available again.

## 8. Additional Testing

Beyond the 49 supplied tests, 10 additional tests were added to exercise integration behavior and edge cases that I wanted additional confidence in.

These tests cover:

- arena-boundary clearance
- fractional and non-cascading obstacle inflation
- unknown-space diagonal traversal
- `start == goal`
- A* optimality against Dijkstra across generated maps
- QoS and timestamps
- stop-once behavior
- retry suppression and recovery
- obstacles behind or away from the active route
- diagonal-side changes
- simulator recovery behavior

**Verification:** All 10 additional tests passed.

The final suite therefore contained **59 tests: 49 provided + 10 additional**, all passing.

## 9. Controlled Experiments

I also used Codex to run controlled experiments against several implementation assumptions rather than relying only on intuition.

### Unknown cells as blocked

Treating unknown cells as blocked caused the `open` scenario to stall without generating a usable route.

This confirmed that optimistic traversal of unknown terrain is necessary for the Part 1 environment because the goal initially lies outside the rover's observed region.

### Removing safety clearance

Removing the planner's clearance margin caused the `wall` scenario to accumulate **150 blocked ticks** and fail to make useful progress.

This reinforced the need to reason about the rover's physical footprint rather than treating obstacle cells as point obstacles.

### Manhattan vs. octile heuristic

The supplied optimality fixtures did not expose a difference between Manhattan and octile distance with the implementation's tie ordering.

Rather than treating that as proof that the heuristics were interchangeable, additional generated maps were tested. A synthetic case was found where:

- octile path cost: `11.071068`
- Manhattan path cost: `11.656854`

This provided an empirical example supporting the use of an admissible octile heuristic for eight-connected movement.

These deliberately inferior variants were used only as experiments and were not shipped as planner behavior.

## 10. Final Validation

The final implementation was validated across the complete supplied scenario set:

| Scenario | Result | Ticks | Blocked | Plans | Replans | Needless |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| open | REACHED | 121 | 0 | 1 | 0 | 0 |
| boulders | REACHED | 127 | 0 | 12 | 11 | 0 |
| wall | REACHED | 136 | 0 | 19 | 18 | 0 |
| popup | REACHED | 129 | 0 | 3 | 2 | 0 |
| goal-blocked | REACHED | 167 | 0 | 5 | 3 | 0 |
| random 1 | REACHED | 140 | 0 | 16 | 15 | 0 |
| random 2 | REACHED | 132 | 0 | 17 | 16 | 0 |
| random 3 | REACHED | 137 | 0 | 14 | 13 | 0 |

All eight scenarios reached the goal with **zero blocked ticks and zero needless replans**.

Additional validation across 31 fixed random seeds also completed successfully with the same safety conditions.

No provided simulator files or supplied tests were modified.

## 11. Known Limitations

The implementation intentionally focuses on the required Part 1 behavior rather than adding unnecessary complexity.

Current limitations include:

- conservative discrete obstacle inflation
- approximate waypoint-progress tracking
- a fixed active-route goal assumption
- no noisy-sensor strategy
- no any-angle path planning or Theta*
- no stretch-goal implementation

These were left as explicit limitations rather than adding unvalidated complexity after the required behavior was working reliably.

## 12. Final Review

After Codex completed the implementation, I independently performed the final verification before submission.

I:

- ran the complete 59-test suite and confirmed all tests passed
- ran `python sim/launch.py --all` and confirmed all eight scenarios reached their goals
- verified zero blocked ticks and zero needless replans across the required scenarios
- reviewed the repository status and incremental commit history
- confirmed the provided simulator and tests were unchanged
- verified the final GitHub repository was public and contained the complete commit history

Codex was used extensively to accelerate implementation, testing, and experimentation, but its output was treated as something to validate rather than assume correct. Incorrect predictions and unsuccessful experimental approaches have intentionally been retained in this log because they were part of the actual development process.
