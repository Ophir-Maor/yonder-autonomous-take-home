"""Reproducible scenario checks; simulator truth stays outside planner code."""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sim  # Makes the provided simulator's imports available.
from sim.launch import make_sim
import rclpy_lite as rclpy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, nargs='*', default=[1, 2, 3])
    parser.add_argument('--random-only', action='store_true')
    args = parser.parse_args()
    cases = [] if args.random_only else [(s, 0) for s in
                                         ('open', 'boulders', 'wall', 'popup', 'goal-blocked')]
    cases += [('random', seed) for seed in args.seeds]
    print('scenario,seed,result,ticks,seconds,distance_m,plans,replans,stops,recoveries,blocked,needless')
    failed = []
    logging.disable(logging.INFO)
    try:
        for name, seed in cases:
            run = make_sim(name, seed, False)
            try:
                run.run()
                score = run.score
                stops = sum(e.kind == 'stop' for e in score.events)
                recoveries = sum(e.kind == 'recovery' for e in score.events)
                print(f'{name},{seed},{run.outcome},{run.tick},{run.tick * 0.2:.1f},'
                      f'{run.rover.distance_driven:.2f},{score.plans},{score.replans},'
                      f'{stops},{recoveries},{run.rover.blocked_ticks},{score.needless}')
                if (run.outcome != 'REACHED' or run.rover.blocked_ticks or score.needless
                        or run.node.replan_count != score.replans):
                    failed.append((name, seed))
            finally:
                if run.node is not None:
                    run.node.destroy_node()
                rclpy.shutdown()
    finally:
        logging.disable(logging.NOTSET)
    if failed:
        print(f'FAILED: {failed}', file=sys.stderr)
        return 1
    print(f'PASS: {len(cases)} scenarios', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
