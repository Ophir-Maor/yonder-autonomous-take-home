# Validation record

All commands ran from the repository root with the existing Python 3.13.15
`.venv` on Darwin 25.3.0 arm64. `-B` suppresses bytecode files and does not alter
algorithm behaviour. Scenario metrics are simulated time, not wall time.
The provided 49-test/48-error baseline was supplied by the user, not rerun here.

## Commands and outcomes

| Command | Observed result |
| --- | --- |
| `.venv/bin/python -B -m unittest tests.test_grid_utils -v` | 17 passed |
| `.venv/bin/python -B -m unittest tests.test_search -v` | 18 passed; suite 0.182 s on first run |
| `.venv/bin/python -B -m unittest tests.test_replan -v` | 14 passed |
| `.venv/bin/python -B -m unittest tests.test_additional -v` | 5, then 6, finally all 10 added tests passed as coverage grew |
| `.venv/bin/python -B -m unittest -v` | 49, then 58, finally all 59 tests passed as tests were added (final suite 0.391 s) |
| `.venv/bin/python -B sim/launch.py --scenario open` | REACHED, 121 ticks, 1 plan, 0 replans, 0 blocked, 0 needless |
| `.venv/bin/python -B sim/launch.py --scenario wall` | REACHED, 136 ticks, 19 plans, 18 replans, 0 blocked, 0 needless |
| `.venv/bin/python -B sim/launch.py --scenario popup` | REACHED, 129 ticks, 3 plans, 2 replans, 0 blocked, 0 needless |
| `.venv/bin/python -B sim/launch.py --scenario goal-blocked` | REACHED, 167 ticks, 5 plans, 3 replans, 1 stop, 1 recovery, 0 blocked, 0 needless |
| `.venv/bin/python -B tools/validate.py --random-only --seeds 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23` | All 20 passed |
| `.venv/bin/python -B tools/validate.py --random-only --seeds 42 99 100 223 999 2026 12345 123456` | All 8 passed |
| `.venv/bin/python -B tools/experiments.py` | Expected ablation outcomes below |
| `MPLCONFIGDIR=/tmp/yonder-matplotlib .venv/bin/python -B sim/launch.py --scenario wall --save-png /tmp/yonder-wall.png` | Same wall metrics; PNG saved and visually inspected |

## Ad hoc heuristic investigation

Two inline `.venv/bin/python -B -` experiments used `unittest.mock.patch` to
substitute Manhattan distance without changing files. The supplied search
fixtures 223 and 199 both returned cost 8.242641 under both heuristics. A scan
of synthetic 8x8 grids (20% obstacles, seeds starting at zero) found seed 19:
octile 11.071068 versus Manhattan 11.656854. The fixture and comparison are now
reproducible via `tools/experiments.py`.

## Deliberate ablations

| Policy | Scenario | Outcome |
| --- | --- | --- |
| Unknown blocked | open | STALLED, 150 ticks, 0 plans, 0 blocked |
| No obstacle inflation or wall margin | wall | STALLED, 207 ticks, 150 blocked, 17 plans, 16 replans |

These runs intentionally disable required behaviour. They are not claimed as
successful production runs.

## Additional random results

Every row reached the goal; all blocked and needless counts were zero; node
replan counters matched the scoreboard. There were no stop/recovery events.

| Seed | Ticks | Plans | Replans |
| --- | ---: | ---: | ---: |
| 4 | 134 | 7 | 6 |
| 5 | 132 | 12 | 11 |
| 6 | 130 | 10 | 9 |
| 7 | 140 | 11 | 10 |
| 8 | 136 | 15 | 14 |
| 9 | 141 | 9 | 8 |
| 10 | 133 | 10 | 9 |
| 11 | 135 | 16 | 15 |
| 12 | 131 | 7 | 6 |
| 13 | 129 | 11 | 10 |
| 14 | 147 | 23 | 22 |
| 15 | 137 | 15 | 14 |
| 16 | 134 | 7 | 6 |
| 17 | 138 | 17 | 16 |
| 18 | 131 | 18 | 17 |
| 19 | 134 | 6 | 5 |
| 20 | 145 | 16 | 15 |
| 21 | 134 | 9 | 8 |
| 22 | 129 | 14 | 13 |
| 23 | 132 | 15 | 14 |
| 42 | 130 | 10 | 9 |
| 99 | 132 | 8 | 7 |
| 100 | 130 | 16 | 15 |
| 223 | 137 | 15 | 14 |
| 999 | 133 | 16 | 15 |
| 2026 | 138 | 13 | 12 |
| 12345 | 134 | 9 | 8 |
| 123456 | 131 | 7 | 6 |

## Final combined checks

- `.venv/bin/python -B -m unittest tests.test_grid_utils tests.test_search tests.test_replan`:
  all 49 supplied tests passed before milestone commits.
- `.venv/bin/python -B sim/launch.py --scenario boulders`: first run after the
  separate prediction commit, REACHED in 127 ticks, 12 plans / 11 replans,
  zero blocked and zero needless. Predicted 3 replans; partial observations
  required more revisions than expected.
- `.venv/bin/python -B sim/launch.py --all`: all 8 rows reached, zero blocked
  and zero needless. The exact table is in the README.
- `.venv/bin/python -B tools/validate.py --seeds 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 42 99 100 223 999 2026 12345 123456`:
  PASS, 36 runs (five fixed + 31 random), all counters matched.
- `MPLCONFIGDIR=/tmp/yonder-matplotlib .venv/bin/python -B sim/launch.py --scenario boulders --save-png /tmp/yonder-boulders.png`:
  same boulders results, PNG saved and visually inspected.
- Before the initial-node commit, an inline `.venv/bin/python -B -` check loaded
  the staged initial-only node source into a temporary module and injected it
  into `make_sim` with a mock. It independently confirmed open reached in 121
  ticks with exactly one publication and zero blocked/replan/needless counts.

Temporary logs, CSV, font cache, and PNGs were stored under `/tmp`, not committed.
Repeated invocations of a command above retained the same scenario metrics.

| Scenario | Ticks | Simulated seconds | Distance (m) | Plans | Replans | Stops | Recoveries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| open | 121 | 24.2 | 36.30 | 1 | 0 | 0 | 0 |
| boulders | 127 | 25.4 | 38.10 | 12 | 11 | 0 | 0 |
| wall | 136 | 27.2 | 40.80 | 19 | 18 | 0 | 0 |
| popup | 129 | 25.8 | 38.70 | 3 | 2 | 0 | 0 |
| goal-blocked | 167 | 33.4 | 38.10 | 5 | 3 | 1 | 1 |
| random 1 | 140 | 28.0 | 42.00 | 16 | 15 | 0 | 0 |
| random 2 | 132 | 26.4 | 39.60 | 17 | 16 | 0 | 0 |
| random 3 | 137 | 27.4 | 41.10 | 14 | 13 | 0 | 0 |

## Clean export and integrity checks

A clean tracked export of commit `1293852` was created with `git archive` under
`/tmp/yonder-clean-2zyss1mr`. The existing `.venv` Python was invoked with that
export as its working directory and `PYTHONPATH` removed. No original working
copy's untracked files were copied. Dependency installation was not repeated.

Commands in that export (absolute interpreter path from the original `.venv`):

- `python -B -m unittest -v`: all 59 passed in 0.373 s.
- `python -B sim/launch.py --all`: all 8 rows reproduced the README table.
- `python -B tools/experiments.py`: reproduced the three documented ablations.

`git diff f596694 -- sim tests/test_grid_utils.py tests/test_search.py tests/test_replan.py tests/__init__.py`
was empty. `git diff --check` passed. No simulator/provided-test file changed;
there are no dependencies on generated images or temporary validation artifacts.
The final documentation commit follows this verified code commit and changes no
runtime code.
