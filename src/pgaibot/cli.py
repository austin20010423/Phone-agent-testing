from __future__ import annotations

import argparse
import sys

from pgaibot.caller import CallRequest, UnsafeDestinationError, start_call
from pgaibot.config import ConfigError, load_settings
from pgaibot.recordings import RecordingError, download_recording


def main() -> int:
    parser = argparse.ArgumentParser(prog="pgaibot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    call_parser = subparsers.add_parser("call", help="Start one outbound test call")
    call_parser.add_argument("--scenario", required=True, help="Scenario key from scenarios.yaml")
    call_parser.add_argument("--to", default=None, help="Override destination; safety guard still applies")
    call_parser.add_argument("--dry-run", action="store_true", help="Validate and print without dialing")

    recording_parser = subparsers.add_parser(
        "download-recording",
        help="Download a completed Twilio call recording as mp3",
    )
    recording_parser.add_argument("artifact_id", help="Artifact id or Twilio CallSid")

    args = parser.parse_args()

    if args.command == "call":
        return _call(args)
    if args.command == "download-recording":
        return _download_recording(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _call(args: argparse.Namespace) -> int:
    try:
        settings = load_settings()
        request = CallRequest(
            scenario=args.scenario,
            to_number=args.to or settings.pg_test_number,
            dry_run=args.dry_run,
        )
        result = start_call(settings, request)
    except (ConfigError, UnsafeDestinationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    action = "Dry run call request" if result.dry_run else "Started call"
    print(action)
    print(f"  sid: {result.sid}")
    print(f"  from: {result.from_number}")
    print(f"  to: {result.to_number}")
    print(f"  instructions: {result.call_instructions}")
    print(f"  status: {result.status}")
    return 0


def _download_recording(args: argparse.Namespace) -> int:
    try:
        settings = load_settings()
        path = download_recording(settings, args.artifact_id)
    except (ConfigError, RecordingError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: failed to download recording: {exc}", file=sys.stderr)
        return 1

    print(f"Downloaded recording: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
