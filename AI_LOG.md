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
