"""ReflexOS CLI.

    python -m reflexos demo      # run the offline agent-training demo (no hardware)
    python -m reflexos server    # run the robot MCP server (see reflexos.server for flags)
"""

from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]
    command = args[0] if args else "demo"

    if command == "demo":
        from .demo import main as demo_main

        demo_main()
    elif command == "server":
        # Hand the remaining args to the server's own parser.
        sys.argv = [sys.argv[0]] + args[1:]
        from .server import main as server_main

        server_main()
    else:
        print(__doc__)
        if command not in ("-h", "--help", "help"):
            sys.exit(2)


if __name__ == "__main__":
    main()
