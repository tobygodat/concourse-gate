"""Command line entry point: `python -m concourse_sync digest | crowding | clear`."""

import argparse
import sys
from pathlib import Path

import httpx

from concourse_sync.client import ConcourseError, connect
from concourse_sync.config import CONCOURSE_URL
from concourse_sync.crowding import check_crowding, clear_stale_gate_alerts
from concourse_sync.digest import build_shift_digest


def build_parser() -> argparse.ArgumentParser:
    """Define the digest, crowding and clear subcommands."""
    parser = argparse.ArgumentParser(prog="concourse_sync", description="Concourse Gate sync worker.")
    parser.add_argument("--url", default=CONCOURSE_URL, help="Concourse API base URL")
    commands = parser.add_subparsers(dest="command", required=True)

    digest = commands.add_parser("digest", help="print an end-of-shift markdown digest")
    digest.add_argument("--out", type=Path, help="write the digest to this file instead of stdout")

    crowding = commands.add_parser("crowding", help="raise alerts for venues near capacity")
    crowding.add_argument("--threshold", type=float, default=0.9, help="occupancy fraction that triggers an alert")

    clear = commands.add_parser("clear", help="resolve gate-sync alerts for venues back under threshold")
    clear.add_argument("--threshold", type=float, default=0.9, help="occupancy fraction still considered crowded")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one subcommand against Concourse and report the outcome."""
    args = build_parser().parse_args(argv)
    try:
        with connect(args.url) as client:
            if args.command == "digest":
                text = build_shift_digest(client)
                if args.out:
                    args.out.write_text(text, encoding="utf-8")
                    print(f"Wrote digest to {args.out}")
                else:
                    print(text, end="")
            elif args.command == "crowding":
                raised = check_crowding(client, threshold=args.threshold)
                for alert in raised:
                    print(f"raised {alert['id']} [{alert['severity']}] {alert['title']}")
                print(f"{len(raised)} crowding alert(s) raised")
            else:
                resolved = clear_stale_gate_alerts(client, threshold=args.threshold)
                for alert in resolved:
                    print(f"resolved {alert['id']} {alert['title']}")
                print(f"{len(resolved)} gate-sync alert(s) resolved")
    except ConcourseError as error:
        print(error, file=sys.stderr)
        return 1
    except httpx.HTTPError as error:
        print(f"Could not reach Concourse at {args.url}: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
