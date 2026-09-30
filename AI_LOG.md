# AI Usage Log

This implementation and its documentation were produced by Codex under the
user's explicit autonomous `/goal` request. The user supplied the assignment,
an untouched baseline, and constraints; human review is still pending. Entries
describe AI work, not work claimed to have been done manually by the user.

## 1. Repository familiarisation

**Asked:** Read the entire starter repository and explain architecture, contracts,
implementation order, and pitfalls without modifying files.

**Kept:** Separation of grid/search/replan helpers from node plumbing; explicit
unknown-space traversal; separate arena-edge clearance; stop/recovery semantics.

**Verification:** Read all source, tests, README, and simulator scoring. No
scenarios were run during this read-only stage. The user reported the initial
49-test baseline with 48 expected errors.

**Corrections:** The rover's comment that any publisher QoS works is contradicted
by its reliable subscription and the bus compatibility check. Use reliable path
publication and best-effort grid subscription.

## 2. Autonomous implementation: grid utilities

**Asked:** Complete the full assessment autonomously, with incremental commits,
tests, scenario validation, honest documentation, and no submission.

**Implemented:** Floor-based coordinate conversion, cell centres, and copied
square obstacle inflation rounded outward to whole cells. Arena edges are kept
out of generic inflation to preserve its tested contract.

**Verification:** `.venv/bin/python -B -m unittest tests.test_grid_utils -v`:
17 tests passed. No implementation failures found in this stage.

**Tool correction:** An initial patch attempted delete/add on the same file;
the patch tool rejected it without changes. Replaced it with an update patch.

## 3. A* search

**Implemented:** Octile distance, heap frontier, best-cost updates, parent
reconstruction, occupied-start escape, unknown-space policy, and both-side
checks for diagonals. In-bounds start==goal returns a singleton even if blocked.

**Verified:** `.venv/bin/python -B -m unittest tests.test_search -v`: 18 passed,
including optimality and the 150x150 speed test (first whole suite: 0.182 s).

**History:** Git identity was absent. After requesting a preferred identity and
continuing independent work, Codex used explicit per-command author/committer
`Codex <codex@localhost>` to avoid inventing human attribution. No user Git
identity settings were changed. Grid and initial-node snapshots had been staged
at their milestones; separate component commits preserve those actual stages.

## 4. Replan helpers

**Implemented:** Nearest waypoint with lower-index ties; remaining-waypoint
validation rejects occupied/outside cells but accepts unknown cells. Kept the
provided waypoint contract; diagonal side checks belong in node integration.

**Verified:** `.venv/bin/python -B -m unittest tests.test_replan -v`: 14 passed.
No implementation failures were found in the helper stages.

## 5. Initial node integration

**Implemented:** Best-effort feed subscription, reliable path publication,
separate boundary margin, optimistic unknown-space traversal, cell-centre
waypoints, and simulated-time monitoring. This commit is the staged initial-only
node snapshot; dynamic behaviour was developed in the working tree afterward.

**Verified:** All 49 supplied tests passed. `open` reached in 121 ticks (24.2 s),
with one publication, one plan, zero replans, zero blocked ticks, zero needless
replans. Additional message and boundary tests were developed separately.

## 6. Dynamic replanning and prediction result

**Implemented:** Remaining-waypoint and diagonal-side invalidation, empty stop
commands, and recovery searches only when effective search inputs change.
Identical commands are suppressed; stop/recovery do not increment replans.

**Verified:** `wall` reached in 136 ticks with 18 replans, zero blocked and zero
needless. The first `boulders` run, after separate prediction commit `3cfb6f2`,
reached in 127 ticks with 12 plans / 11 replans, zero blocked and zero needless.
The prediction was written before wall/popup development, and committed before
any boulders execution. Other scenarios were exercised while identity was pending.

**AI mistake corrected by observation:** The prediction of 3 replans assumed
roughly one revision per later boulder. Actual replans occurred at ticks
1, 2, 9, 20, 23, 24, 50, 51, 76, 77, 78. Even the partly visible first boulder
required revisions as additional cells became known; diagonal side clearance
also changed. No scenario-specific fix was needed: all revisions were justified
by the scoreboard. Preserve the original prediction rather than rewriting it.

## 7. Stop/recovery and added edge tests

**Verified:** `popup` reached in 129 ticks, 3 plans / 2 replans; the rock behind
at tick 81 did not cause a publication. `goal-blocked` reached in 167 ticks,
5 nonempty plans / 3 replans; stop at tick 104, recovery at tick 144 (8 seconds).
Both had zero blocked and needless ticks. Ten new tests cover boundaries,
fractional non-cascading inflation, unknown diagonal policy, start==goal,
Dijkstra optimality on 40 maps, QoS/stamps, stop-once/retry suppression/recovery,
obstacles behind/off-route, diagonal-side changes, and actual simulator recovery.
`.venv/bin/python -B -m unittest tests.test_additional -v`: all 10 passed.
The production implementation needed no additional correction for these cases.
