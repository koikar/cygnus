"""CLI for the pick-and-place benchmark.

  python -m reflexos.benchmark serve [--transport http --http-port 8010]
  python -m reflexos.benchmark run --policy skilled --episodes 30
  python -m reflexos.benchmark compare --episodes 50 [--grasp-reliability 0.7]
"""

from __future__ import annotations

import argparse
import json
import sys

from .pickplace import EnvConfig
from .runner import run


def main() -> None:
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "compare"

    if cmd == "serve":
        from .server import main as serve_main

        sys.argv = [sys.argv[0]] + argv[1:]
        serve_main()
        return

    parser = argparse.ArgumentParser(prog="reflexos.benchmark")
    parser.add_argument("cmd", choices=["run", "compare"])
    parser.add_argument("--policy", default="skilled", choices=["blind", "skilled"])
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--grasp-reliability", type=float, default=1.0)
    parser.add_argument("--no-home-policy", action="store_true")
    args = parser.parse_args(argv)

    config = EnvConfig(grasp_reliability=args.grasp_reliability, require_home_between=not args.no_home_policy)

    if args.cmd == "run":
        card = run(args.policy, args.episodes, config)
        print(json.dumps(card, indent=2))
    else:  # compare
        blind = run("blind", args.episodes, config)
        skilled = run("skilled", args.episodes, config)
        print(json.dumps({"blind": blind, "skilled": skilled,
                          "success_delta": round(skilled["success_rate"] - blind["success_rate"], 3)}, indent=2))


if __name__ == "__main__":
    main()
