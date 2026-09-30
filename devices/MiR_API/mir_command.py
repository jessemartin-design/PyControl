#!/usr/bin/env python3
"""Send GoToPosition / RunMission commands to the MiR over its REST API."""

from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mir.client import MirClient, MirError, NamedItem, format_status, load_dotenv
from mir.parser import COMMANDS, ParsedCommand, help_text, parse_line, resolve_value


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    load_dotenv(str(ROOT / ".env"))
    if args.host:
        import os

        os.environ["MIR_HOST"] = args.host
    if args.base_url:
        import os

        os.environ["MIR_API_BASE"] = args.base_url

    try:
        _ensure_credentials()
        client = MirClient.from_env(
            host_override=args.host,
            base_url_override=args.base_url,
        )
        status = client.connect()
    except MirError as exc:
        print(f"Could not connect: {exc}", file=sys.stderr)
        return 1

    _print_banner(client, status)

    if args.command:
        return _run_line(client, " ".join(args.command))

    print("Type a command, or Help. Ctrl-C or Quit to exit.")
    while True:
        try:
            line = input(f"{_prompt_name(status)}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        code = _run_line(client, line)
        if code == 130:
            return 0
        try:
            status = client.get_status()
        except MirError:
            pass


def _run_line(client: MirClient, line: str) -> int:
    parsed = parse_line(line)
    try:
        return _dispatch(client, parsed)
    except MirError as exc:
        print(f"Error: {exc}")
        return 1
    except KeyboardInterrupt:
        print()
        return 130


def _dispatch(client: MirClient, parsed: ParsedCommand) -> int:
    if parsed.verb is None:
        if parsed.alternatives:
            return _disambiguate_command(client, parsed)
        print(f"Unknown command {parsed.raw!r}.")
        print()
        print(help_text())
        return 2

    spec = parsed.spec
    assert spec is not None

    if spec.name == "Quit":
        return 130
    if spec.name == "Help":
        print(help_text())
        return 0
    if spec.name == "Status":
        print(format_status(client.get_status()))
        return 0
    if spec.name == "ListPositions":
        return _print_catalog("Positions stored on the robot", client.get_positions())
    if spec.name == "ListMissions":
        return _print_catalog("Missions stored on the robot", client.get_missions())

    if parsed.needs_correction:
        return _correct_and_run(client, parsed)

    if spec.needs_value and not parsed.argument:
        return _prompt_missing_value(client, spec.name)

    return _execute(client, spec.name, parsed.argument)


def _correct_and_run(client: MirClient, parsed: ParsedCommand) -> int:
    spec = parsed.spec
    assert spec is not None
    print(f"Did you mean {spec.name}?")
    print(f"  (you typed: {parsed.raw})")
    print()

    items = _catalog(client, spec.catalog)
    if not items:
        print(f"No {spec.value_label}s are stored on the robot.")
        return 1

    default = None
    if parsed.argument:
        match, _ = resolve_value(parsed.argument, [item.name for item in items])
        default = match or parsed.argument

    chosen = _choose_item(items, spec.value_label, default=default)
    if chosen is None:
        print("Cancelled.")
        return 2
    return _execute(client, spec.name, chosen.name)


def _prompt_missing_value(client: MirClient, verb: str) -> int:
    spec = COMMANDS[verb]
    print(f"{verb} needs a {spec.value_label} name.")
    print()
    items = _catalog(client, spec.catalog)
    if not items:
        print(f"No {spec.value_label}s are stored on the robot.")
        return 1
    chosen = _choose_item(items, spec.value_label)
    if chosen is None:
        print("Cancelled.")
        return 2
    return _execute(client, verb, chosen.name)


def _disambiguate_command(client: MirClient, parsed: ParsedCommand) -> int:
    print(f"Not sure which command you meant by {parsed.raw!r}.")
    options = parsed.alternatives
    for index, name in enumerate(options, start=1):
        spec = COMMANDS[name]
        print(f"  {index}. {name}  — {spec.description}")
    try:
        raw = input("Choose a command number (Enter to cancel): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 2
    if not raw:
        print("Cancelled.")
        return 2
    if raw.isdigit() and 1 <= int(raw) <= len(options):
        verb = options[int(raw) - 1]
    else:
        match = next((name for name in options if name.casefold() == raw.casefold()), None)
        if not match:
            print("Cancelled.")
            return 2
        verb = match
    rewritten = ParsedCommand(
        raw=parsed.raw,
        verb=verb,
        kind="alias",
        argument=parsed.argument,
        confidence=0.8,
    )
    return _dispatch(client, rewritten)


def _execute(client: MirClient, verb: str, argument: str | None) -> int:
    if verb == "GoToPosition":
        return _execute_named(
            client,
            verb=verb,
            argument=argument or "",
            items=client.get_positions(),
            runner=lambda name, items: client.go_to_position_by_name(
                name,
                positions=items,
                map_id=client.get_status().get("map_id"),
            ),
            noun="position",
        )
    if verb == "RunMission":
        return _execute_named(
            client,
            verb=verb,
            argument=argument or "",
            items=client.get_missions(),
            runner=lambda name, items: client.run_mission_by_name(name, missions=items),
            noun="mission",
        )
    print(f"Unhandled command {verb}.")
    return 1


def _execute_named(
    client: MirClient,
    *,
    verb: str,
    argument: str,
    items: list[NamedItem],
    runner,
    noun: str,
) -> int:
    if not items:
        print(f"No {noun}s are stored on the robot.")
        return 1

    match, suggestions = resolve_value(argument, [item.name for item in items])
    if match is None:
        print(f"No {noun} named {argument!r}.")
        if suggestions:
            print(f"Did you mean one of these {noun}s?")
        chosen = _choose_item(
            [item for item in items if item.name in suggestions] or items,
            noun,
        )
        if chosen is None:
            print("Cancelled.")
            return 2
        match = chosen.name

    status = client.get_status()
    mission_text = (status.get("mission_text") or "").lower()
    if "charg" in mission_text:
        print("Note: the robot is charging. Queueing this usually makes it leave the charger.")
    print(f"{verb} {match} …")
    result = runner(match, items)
    queue_id = result.get("id") or result.get("guid") or "?"
    state = result.get("state") or result.get("state_text") or "queued"
    print(f"Queued ({state}, id {queue_id}).")
    print(format_status(client.get_status()))
    return 0


def _catalog(client: MirClient, name: str | None) -> list[NamedItem]:
    if name == "positions":
        return client.get_positions()
    if name == "missions":
        return client.get_missions()
    return []


def _choose_item(
    items: list[NamedItem],
    noun: str,
    default: str | None = None,
) -> NamedItem | None:
    if not items:
        return None
    print(f"{noun.capitalize()}s stored on the robot:")
    for index, item in enumerate(items, start=1):
        marker = ""
        if default and item.name.casefold() == default.casefold():
            marker = "  ← matches what you typed"
        print(f"  {index}. {item.name}{marker}")
    print()
    hint = f", or Enter for {default}" if default else ", or Enter to cancel"
    try:
        raw = input(f"Choose a {noun} (number or name{hint}): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not raw:
        if default:
            match, _ = resolve_value(default, [item.name for item in items])
            return next((item for item in items if item.name == match), None)
        return None
    if raw.isdigit() and 1 <= int(raw) <= len(items):
        return items[int(raw) - 1]
    match, _ = resolve_value(raw, [item.name for item in items])
    if match:
        return next(item for item in items if item.name == match)
    print(f"'{raw}' is not a known {noun}.")
    return None


def _print_catalog(title: str, items: list[NamedItem]) -> int:
    print(f"{title}:")
    if not items:
        print("  (none)")
        return 0
    for index, item in enumerate(items, start=1):
        print(f"  {index}. {item.name}")
    return 0


def _print_banner(client: MirClient, status: dict) -> None:
    product = client.product or status.get("robot_model") or "MiR"
    version = client.robot_version or "unknown software"
    api = client.api_version or "unknown API"
    print(f"Connected to {status.get('robot_name', client.host)} ({product})")
    print(f"API {client.base_url}  [{version}, {api}]")
    print(format_status(status))
    print()


def _prompt_name(status: dict) -> str:
    return str(status.get("robot_name") or "MiR")


def _ensure_credentials() -> None:
    import os

    if os.environ.get("MIR_USERNAME") and os.environ.get("MIR_PASSWORD"):
        return
    print("MiR UI login is required for positions, missions, and commands.")
    if not os.environ.get("MIR_USERNAME"):
        os.environ["MIR_USERNAME"] = input("Username: ").strip()
    if not os.environ.get("MIR_PASSWORD"):
        os.environ["MIR_PASSWORD"] = getpass("Password: ")


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send GoToPosition and RunMission commands to a MiR robot.",
        epilog="With no command, starts an interactive console.",
    )
    parser.add_argument("--host", help="Robot IP or hostname (default: MIR_HOST or 10.14.19.160)")
    parser.add_argument("--base-url", help="Full API base, e.g. http://10.14.19.160/api/v2.0.0")
    parser.add_argument("command", nargs="*", help='Command to run once, e.g. "GoToPosition Station2"')
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
