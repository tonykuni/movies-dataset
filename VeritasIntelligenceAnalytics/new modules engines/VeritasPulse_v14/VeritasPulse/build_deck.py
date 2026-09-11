#!/usr/bin/env python3
"""VeritasPulse — one-shot project deck builder.

Usage:
    python build_deck.py                 # uses bundled demo project
    python build_deck.py --db my.db --pid 1
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vpl.core import store
from vpl.ppt import generate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="output/veritaspulse.db")
    ap.add_argument("--pid", type=int, default=1)
    ap.add_argument("--out", default="output")
    args = ap.parse_args()

    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)
    store.init_db(args.db, seed=True)
    project = store.load_project(args.db, args.pid)
    deck = generate.build(project, args.out)
    dt = time.time() - t0
    print(f"[VPL] deck: {deck}")
    print(f"[VPL] project: {project['name']} ({project['code']})")
    print(f"[VPL] {len(project['tasks'])} tasks · {len(project['risks'])} risks · "
          f"{len(project['stakeholders'])} stakeholders")
    print(f"[VPL] generated in {dt:.2f}s")

if __name__ == "__main__":
    main()
