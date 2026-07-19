from __future__ import annotations

import sys
from typing import Sequence

from workprint import claude_local_summary, git_summary, web_investigate


COMMANDS = {
    "git-summary": git_summary.main,
    "claude-local-summary": claude_local_summary.main,
    "web-investigate": web_investigate.main,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Single-binary dispatcher for the Python bridge modules the web app's
    API routes invoke, so a packaged desktop build needs no system Python.

    Each subcommand forwards its remaining arguments unchanged to the
    matching module's own main(argv), which is otherwise identical to
    running `python3 -m workprint.<module>` directly (still how dev mode
    invokes these same modules; see lib/workprint-python-command.ts).
    """
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] not in COMMANDS:
        print(
            f"Usage: workprint-backend <{'|'.join(COMMANDS)}> [args...]",
            file=sys.stderr,
        )
        return 2

    command, rest = args[0], args[1:]
    return COMMANDS[command](rest)


if __name__ == "__main__":
    raise SystemExit(main())
