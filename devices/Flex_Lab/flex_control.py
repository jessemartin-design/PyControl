#!/usr/bin/env python3
"""
Lean Opentrons Flex control layer for demo choreography.

Humans or a PAI can drive the Flex over Wi-Fi using simple CLI commands
or by importing FlexClient from another Python process.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.json"
EXAMPLE_CONFIG = ROOT / "config.example.json"
SIGNALS_DIR = ROOT / "signals"
TERMINAL_STATUSES = {"succeeded", "failed", "stopped"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_config(config: dict[str, Any], path: Path = DEFAULT_CONFIG) -> None:
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def ensure_config(path: Path = DEFAULT_CONFIG) -> Path:
    """Create config.json from the example file when missing."""
    if path.is_file():
        return path
    if not EXAMPLE_CONFIG.is_file():
        raise FlexError(f"Missing {path} and {EXAMPLE_CONFIG}")
    path.write_text(EXAMPLE_CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _local_ipv4() -> Optional[str]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return None


def _probe_flex(ip: str, port: int = 31950, timeout_s: float = 0.35) -> Optional[dict[str, Any]]:
    try:
        response = requests.get(
            f"http://{ip}:{port}/health",
            headers={"Opentrons-Version": "*"},
            timeout=timeout_s,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("robot_model") or data.get("name"):
            return {"ip": ip, "port": port, "health": data}
    except (requests.RequestException, ValueError):
        return None
    return None


def discover_flex_hosts(
    port: int = 31950,
    *,
    max_workers: int = 64,
) -> list[dict[str, Any]]:
    """
    Best-effort LAN scan for Opentrons robot HTTP APIs on the local /24.

    Manual IP entry remains the reliable default; discovery can miss robots on
    locked-down Wi-Fi or different subnets.
    """
    local_ip = _local_ipv4()
    if not local_ip or local_ip.startswith("127."):
        raise FlexError("Could not determine local IPv4 address for discovery")

    prefix = ".".join(local_ip.split(".")[:3])
    candidates = [f"{prefix}.{i}" for i in range(1, 255)]
    found: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_probe_flex, ip, port): ip for ip in candidates}
        for future in as_completed(futures):
            hit = future.result()
            if hit:
                found.append(hit)
    found.sort(key=lambda item: item["ip"])
    return found


def emit_event(kind: str, **payload: Any) -> None:
    """Print one JSON event line for humans, PAI, or log collectors."""
    event = {"ts": utc_now(), "event": kind, **payload}
    print(json.dumps(event), flush=True)


class FlexError(RuntimeError):
    """Raised when the robot API returns an error or is unreachable."""


class FlexClient:
    """Thin wrapper around the Opentrons robot HTTP API (port 31950)."""

    def __init__(
        self,
        host: str,
        port: int = 31950,
        version_header: str = "*",
        timeout_s: float = 30.0,
        poll_interval_s: float = 2.0,
    ) -> None:
        self.base_url = f"http://{host}:{port}"
        self.timeout_s = timeout_s
        self.poll_interval_s = poll_interval_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Opentrons-Version": str(version_header),
                "Accept": "application/json",
            }
        )

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "FlexClient":
        return cls(
            host=config["robot_ip"],
            port=int(config.get("robot_port", 31950)),
            version_header=str(config.get("opentrons_version_header", "*")),
            timeout_s=float(config.get("request_timeout_s", 30)),
            poll_interval_s=float(config.get("poll_interval_s", 2.0)),
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        expected: tuple[int, ...] = (200, 201),
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method,
                url,
                json=json_body,
                files=files,
                timeout=self.timeout_s,
            )
        except requests.RequestException as exc:
            raise FlexError(f"Could not reach Flex at {url}: {exc}") from exc

        if response.status_code not in expected:
            detail = response.text.strip()
            raise FlexError(
                f"{method} {path} failed ({response.status_code}): {detail}"
            )

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    # --- health / status -------------------------------------------------

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def instruments(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/instruments")
        return payload.get("data", [])

    def deck_configuration(self) -> dict[str, Any]:
        payload = self._request("GET", "/deck_configuration")
        return payload.get("data", {})

    def status_summary(self) -> dict[str, Any]:
        health = self.health()
        runs = self.list_runs(page_length=1)
        current = runs[0] if runs else None
        return {
            "reachable": True,
            "name": health.get("name"),
            "robot_model": health.get("robot_model"),
            "api_version": health.get("api_version"),
            "system_version": health.get("system_version"),
            "serial": health.get("robot_serial"),
            "instruments": self.instruments(),
            "current_run": (
                {
                    "id": current.get("id"),
                    "status": current.get("status"),
                    "protocolId": current.get("protocolId"),
                }
                if current
                else None
            ),
        }

    # --- deck helpers ----------------------------------------------------

    @staticmethod
    def deck_slots() -> list[str]:
        """Flex deck slots available for standard labware."""
        return [
            "A1", "A2", "A3",
            "B1", "B2", "B3",
            "C1", "C2", "C3",
            "D1", "D2", "D3",
        ]

    def describe_deck(self) -> dict[str, Any]:
        config = self.deck_configuration()
        fixtures = config.get("cutoutFixtures", [])
        slots = {}
        for item in fixtures:
            cutout = item.get("cutoutId", "")
            slot = cutout.replace("cutout", "") if cutout.startswith("cutout") else cutout
            slots[slot] = item.get("cutoutFixtureId")
        return {"slots": slots, "available_slots": self.deck_slots(), "raw": config}

    # --- protocols -------------------------------------------------------

    def list_protocols(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/protocols")
        return payload.get("data", [])

    def find_protocol(self, name_or_id: str) -> dict[str, Any]:
        protocols = self.list_protocols()
        for protocol in protocols:
            if protocol.get("id") == name_or_id:
                return protocol
            meta_name = (protocol.get("metadata") or {}).get("protocolName", "")
            files = protocol.get("files") or []
            file_names = [f.get("name", "") for f in files]
            if name_or_id == meta_name or name_or_id in file_names:
                return protocol
        raise FlexError(f"No protocol found matching '{name_or_id}'")

    def upload_protocol(self, file_path: Path) -> dict[str, Any]:
        path = Path(file_path)
        if not path.is_file():
            raise FlexError(f"Protocol file not found: {path}")
        with path.open("rb") as handle:
            payload = self._request(
                "POST",
                "/protocols",
                files={"files": (path.name, handle, "text/x-python")},
            )
        return payload.get("data", payload)

    # --- runs ------------------------------------------------------------

    def list_runs(self, page_length: int = 20) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/runs?pageLength={page_length}")
        return payload.get("data", [])

    def get_run(self, run_id: str) -> dict[str, Any]:
        payload = self._request("GET", f"/runs/{run_id}")
        return payload.get("data", payload)

    def create_run(
        self,
        protocol_id: str,
        run_time_parameters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"data": {"protocolId": protocol_id}}
        if run_time_parameters:
            body["data"]["runTimeParameterValues"] = run_time_parameters
        payload = self._request("POST", "/runs", json_body=body)
        return payload.get("data", payload)

    def run_action(self, run_id: str, action_type: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/runs/{run_id}/actions",
            json_body={"data": {"actionType": action_type}},
        )
        return payload.get("data", payload)

    def play(self, run_id: str) -> dict[str, Any]:
        return self.run_action(run_id, "play")

    def pause(self, run_id: str) -> dict[str, Any]:
        return self.run_action(run_id, "pause")

    def stop(self, run_id: str) -> dict[str, Any]:
        return self.run_action(run_id, "stop")

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout_s: Optional[float] = None,
        interactive: bool = True,
    ) -> dict[str, Any]:
        """
        Poll until the run finishes.

        When interactive=True (default for human terminals):
        - If the Flex pauses (e.g. protocol note / Confirm & resume), prompt to
          resume via API play, keep waiting, or stop the run.
        - Ctrl+C asks whether to stop the Flex run as well (terminal cancel alone
          does not stop the robot).
        """
        started = time.time()
        last_status: Optional[str] = None
        pause_prompt_pending = True

        while True:
            try:
                run = self.get_run(run_id)
                status = run.get("status")
                if status != last_status:
                    emit_event("run_status", run_id=run_id, status=status)
                    last_status = status
                    if status == "paused":
                        pause_prompt_pending = True

                if status in TERMINAL_STATUSES:
                    return run

                if (
                    status == "paused"
                    and interactive
                    and pause_prompt_pending
                    and sys.stdin.isatty()
                ):
                    emit_event(
                        "run_paused_prompt",
                        run_id=run_id,
                        hint="Protocol may be waiting for Confirm & resume",
                    )
                    print(
                        "\nFlex run is PAUSED "
                        "(often a note / Confirm & resume step).\n"
                        "  y = resume from this terminal (same as Confirm & resume)\n"
                        "  n = keep waiting (you can still use the touchscreen)\n"
                        "  s = stop the run on the Flex\n",
                        file=sys.stderr,
                        flush=True,
                    )
                    choice = input("Resume paused Flex run? [y/n/s]: ").strip().lower()
                    if choice in {"y", "yes"}:
                        self.play(run_id)
                        emit_event("run_resumed", run_id=run_id, via="terminal")
                        pause_prompt_pending = False
                    elif choice in {"s", "stop"}:
                        self.stop(run_id)
                        emit_event("run_stop", run_id=run_id, via="terminal_pause_prompt")
                        pause_prompt_pending = False
                    else:
                        # User will use touchscreen or decide later; don't spam.
                        pause_prompt_pending = False
                        emit_event("run_pause_deferred", run_id=run_id)

                if timeout_s is not None and (time.time() - started) > timeout_s:
                    raise FlexError(
                        f"Timed out after {timeout_s}s waiting for run {run_id} "
                        f"(last status: {status})"
                    )
                time.sleep(self.poll_interval_s)
            except KeyboardInterrupt:
                if interactive and sys.stdin.isatty():
                    print(
                        "\nTerminal canceled. The Flex may still be running.",
                        file=sys.stderr,
                        flush=True,
                    )
                    stop_choice = input(
                        f"Also STOP run {run_id} on the Flex? [y/N]: "
                    ).strip().lower()
                    if stop_choice in {"y", "yes"}:
                        try:
                            self.stop(run_id)
                            emit_event(
                                "run_stop",
                                run_id=run_id,
                                via="terminal_keyboard_interrupt",
                            )
                        except FlexError as exc:
                            emit_event("error", message=str(exc))
                raise

    def run_protocol(
        self,
        name_or_id: str,
        *,
        params: Optional[dict[str, Any]] = None,
        wait: bool = True,
        timeout_s: Optional[float] = None,
        interactive: bool = True,
    ) -> dict[str, Any]:
        protocol = self.find_protocol(name_or_id)
        protocol_id = protocol["id"]
        emit_event(
            "protocol_selected",
            protocol_id=protocol_id,
            protocol_name=(protocol.get("metadata") or {}).get("protocolName"),
        )

        run = self.create_run(protocol_id, run_time_parameters=params)
        run_id = run["id"]
        emit_event("run_created", run_id=run_id, protocol_id=protocol_id, params=params or {})

        self.play(run_id)
        emit_event("run_started", run_id=run_id)

        if not wait:
            return run

        try:
            final = self.wait_for_run(
                run_id, timeout_s=timeout_s, interactive=interactive
            )
        except KeyboardInterrupt:
            emit_event("interrupted", run_id=run_id)
            raise
        emit_event(
            "run_finished",
            run_id=run_id,
            status=final.get("status"),
            ok=final.get("status") == "succeeded",
        )
        return final


# --- choreography signals ------------------------------------------------


def signal_path(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    return SIGNALS_DIR / f"{safe}.json"


def emit_signal(name: str, payload: Optional[dict[str, Any]] = None) -> Path:
    path = signal_path(name)
    data = {
        "name": name,
        "ts": utc_now(),
        "payload": payload or {},
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    emit_event("signal_emitted", name=name, path=str(path), payload=payload or {})
    return path


def wait_for_signal(
    name: str,
    *,
    timeout_s: Optional[float] = None,
    poll_interval_s: float = 0.5,
    clear: bool = True,
) -> dict[str, Any]:
    path = signal_path(name)
    started = time.time()
    emit_event("signal_waiting", name=name, path=str(path))
    while True:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if clear:
                path.unlink(missing_ok=True)
            emit_event("signal_received", name=name, payload=data.get("payload", {}))
            return data
        if timeout_s is not None and (time.time() - started) > timeout_s:
            raise FlexError(f"Timed out waiting for signal '{name}'")
        time.sleep(poll_interval_s)


def clear_signal(name: str) -> bool:
    path = signal_path(name)
    if path.is_file():
        path.unlink()
        emit_event("signal_cleared", name=name)
        return True
    return False


# --- CLI -----------------------------------------------------------------


def parse_params(items: list[str]) -> dict[str, Any]:
    """Parse KEY=VALUE pairs. Numbers become int/float when possible."""
    params: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Parameter must look like KEY=VALUE, got: {item}")
        key, raw = item.split("=", 1)
        if raw.lower() in {"true", "false"}:
            params[key] = raw.lower() == "true"
            continue
        try:
            params[key] = int(raw)
            continue
        except ValueError:
            pass
        try:
            params[key] = float(raw)
            continue
        except ValueError:
            pass
        params[key] = raw
    return params


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control an Opentrons Flex over Wi-Fi for demo choreography.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to config.json (default: ./config.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="Check that the Flex is reachable")
    sub.add_parser("status", help="Show robot health, instruments, and current run")
    sub.add_parser("deck", help="Show deck fixture map and available slots")
    sub.add_parser("protocols", help="List protocols stored on the Flex")
    sub.add_parser("runs", help="List recent runs")

    discover = sub.add_parser(
        "discover",
        help="Scan the local subnet for Opentrons robots (optional; manual IP is default)",
    )
    discover.add_argument(
        "--save",
        action="store_true",
        help="If exactly one robot is found, save its IP into config.json",
    )
    discover.add_argument(
        "--set-ip",
        default=None,
        help="Write this IP into config.json without scanning",
    )

    upload = sub.add_parser("upload", help="Upload a protocol file to the Flex")
    upload.add_argument("file", help="Path to a .py protocol file")

    run = sub.add_parser("run", help="Create and start a run from a stored protocol")
    run.add_argument("protocol", help="Protocol id, protocolName, or file name")
    run.add_argument(
        "--param",
        action="append",
        default=[],
        help="Runtime parameter KEY=VALUE (repeatable)",
    )
    run.add_argument(
        "--no-wait",
        action="store_true",
        help="Return immediately after play (do not wait for completion)",
    )
    run.add_argument("--timeout", type=float, default=None, help="Seconds to wait")
    run.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not ask about pause resume / Ctrl+C stop (for automation)",
    )

    play = sub.add_parser("play", help="Play / resume a run")
    play.add_argument("run_id")

    pause = sub.add_parser("pause", help="Pause a run")
    pause.add_argument("run_id")

    stop = sub.add_parser("stop", help="Stop a run")
    stop.add_argument("run_id")

    wait = sub.add_parser("wait", help="Poll a run until it finishes")
    wait.add_argument("run_id")
    wait.add_argument("--timeout", type=float, default=None)
    wait.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not ask about pause resume / Ctrl+C stop",
    )

    transfer = sub.add_parser(
        "transfer",
        help="Upload demo_transfer.py if needed, then run a parameterized transfer",
    )
    transfer.add_argument("--plate-slot", default="C2")
    transfer.add_argument("--tiprack-slot", default="B2")
    transfer.add_argument("--source", default="A1", help="Source well, e.g. A1")
    transfer.add_argument("--dest", default="B1", help="Destination well, e.g. B1")
    transfer.add_argument("--volume", type=float, default=10.0, help="Volume in uL")
    transfer.add_argument("--no-wait", action="store_true")
    transfer.add_argument("--timeout", type=float, default=None)
    transfer.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not ask about pause resume / Ctrl+C stop (for automation)",
    )
    transfer.add_argument(
        "--protocol-file",
        default=str(ROOT / "protocols" / "demo_transfer.py"),
        help="Local protocol file to upload/use",
    )

    signal = sub.add_parser("signal", help="Emit or wait for choreography signals")
    signal_sub = signal.add_subparsers(dest="signal_command", required=True)

    sig_emit = signal_sub.add_parser("emit", help="Write a named signal file")
    sig_emit.add_argument("name")
    sig_emit.add_argument(
        "--payload",
        action="append",
        default=[],
        help="Optional KEY=VALUE payload fields",
    )

    sig_wait = signal_sub.add_parser("wait", help="Block until a named signal appears")
    sig_wait.add_argument("name")
    sig_wait.add_argument("--timeout", type=float, default=None)
    sig_wait.add_argument(
        "--keep",
        action="store_true",
        help="Do not delete the signal file after reading it",
    )

    sig_clear = signal_sub.add_parser("clear", help="Delete a named signal file")
    sig_clear.add_argument("name")

    return parser


def get_client(args: argparse.Namespace) -> FlexClient:
    config = load_config(Path(args.config))
    return FlexClient.from_config(config)


def cmd_ping(client: FlexClient) -> int:
    health = client.health()
    emit_event(
        "ping_ok",
        name=health.get("name"),
        robot_model=health.get("robot_model"),
        api_version=health.get("api_version"),
    )
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    ensure_config(Path(args.config))
    config = load_config(Path(args.config))
    port = int(config.get("robot_port", 31950))

    if args.set_ip:
        config["robot_ip"] = args.set_ip
        save_config(config, Path(args.config))
        emit_event("config_ip_saved", robot_ip=args.set_ip, config=str(args.config))
        return 0

    emit_event("discover_started", port=port)
    found = discover_flex_hosts(port=port)
    robots = [
        {
            "ip": item["ip"],
            "name": (item.get("health") or {}).get("name"),
            "robot_model": (item.get("health") or {}).get("robot_model"),
            "serial": (item.get("health") or {}).get("robot_serial"),
        }
        for item in found
    ]
    emit_event("discover_finished", count=len(robots), robots=robots)

    if args.save and len(robots) == 1:
        config["robot_ip"] = robots[0]["ip"]
        save_config(config, Path(args.config))
        emit_event("config_ip_saved", robot_ip=robots[0]["ip"], config=str(args.config))
    elif args.save and len(robots) != 1:
        emit_event(
            "discover_save_skipped",
            reason="Need exactly one robot to auto-save; use --set-ip instead",
            count=len(robots),
        )
        return 1
    return 0


def cmd_status(client: FlexClient) -> int:
    emit_event("status", **client.status_summary())
    return 0


def cmd_deck(client: FlexClient) -> int:
    emit_event("deck", **client.describe_deck())
    return 0


def cmd_protocols(client: FlexClient) -> int:
    protocols = []
    for item in client.list_protocols():
        protocols.append(
            {
                "id": item.get("id"),
                "name": (item.get("metadata") or {}).get("protocolName"),
                "files": [f.get("name") for f in item.get("files") or []],
                "kind": item.get("protocolKind"),
                "createdAt": item.get("createdAt"),
            }
        )
    emit_event("protocols", count=len(protocols), protocols=protocols)
    return 0


def cmd_runs(client: FlexClient) -> int:
    runs = []
    for item in client.list_runs():
        runs.append(
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "current": item.get("current"),
                "protocolId": item.get("protocolId"),
                "createdAt": item.get("createdAt"),
            }
        )
    emit_event("runs", count=len(runs), runs=runs)
    return 0


def cmd_upload(client: FlexClient, args: argparse.Namespace) -> int:
    data = client.upload_protocol(Path(args.file))
    emit_event(
        "protocol_uploaded",
        protocol_id=data.get("id"),
        name=(data.get("metadata") or {}).get("protocolName"),
        file=args.file,
    )
    return 0


def cmd_run(client: FlexClient, args: argparse.Namespace) -> int:
    params = parse_params(args.param)
    try:
        result = client.run_protocol(
            args.protocol,
            params=params or None,
            wait=not args.no_wait,
            timeout_s=args.timeout,
            interactive=not args.no_prompt,
        )
    except KeyboardInterrupt:
        return 130
    if args.no_wait:
        emit_event("run_queued", run_id=result.get("id"), status=result.get("status"))
    return 0 if result.get("status") in {None, "idle", "running", "succeeded"} or args.no_wait else 1


def cmd_play(client: FlexClient, args: argparse.Namespace) -> int:
    client.play(args.run_id)
    emit_event("run_play", run_id=args.run_id)
    return 0


def cmd_pause(client: FlexClient, args: argparse.Namespace) -> int:
    client.pause(args.run_id)
    emit_event("run_pause", run_id=args.run_id)
    return 0


def cmd_stop(client: FlexClient, args: argparse.Namespace) -> int:
    client.stop(args.run_id)
    emit_event("run_stop", run_id=args.run_id)
    return 0


def cmd_wait(client: FlexClient, args: argparse.Namespace) -> int:
    try:
        final = client.wait_for_run(
            args.run_id,
            timeout_s=args.timeout,
            interactive=not args.no_prompt,
        )
    except KeyboardInterrupt:
        return 130
    ok = final.get("status") == "succeeded"
    emit_event("run_finished", run_id=args.run_id, status=final.get("status"), ok=ok)
    return 0 if ok else 1


def ensure_demo_protocol(client: FlexClient, protocol_file: Path) -> str:
    """Return protocol id for Flex Lab Demo Transfer, uploading if missing."""
    try:
        existing = client.find_protocol("Flex Lab Demo Transfer")
        return existing["id"]
    except FlexError:
        data = client.upload_protocol(protocol_file)
        emit_event(
            "protocol_uploaded",
            protocol_id=data.get("id"),
            name=(data.get("metadata") or {}).get("protocolName"),
            file=str(protocol_file),
        )
        return data["id"]


def cmd_transfer(client: FlexClient, args: argparse.Namespace) -> int:
    protocol_id = ensure_demo_protocol(client, Path(args.protocol_file))
    params = {
        "plate_slot": args.plate_slot,
        "tiprack_slot": args.tiprack_slot,
        "source_well": args.source,
        "dest_well": args.dest,
        "volume_ul": args.volume,
    }
    emit_event("transfer_requested", **params)
    try:
        result = client.run_protocol(
            protocol_id,
            params=params,
            wait=not args.no_wait,
            timeout_s=args.timeout,
            interactive=not args.no_prompt,
        )
    except KeyboardInterrupt:
        return 130
    if args.no_wait:
        return 0
    return 0 if result.get("status") == "succeeded" else 1


def cmd_signal(args: argparse.Namespace) -> int:
    if args.signal_command == "emit":
        emit_signal(args.name, parse_params(args.payload) or None)
        return 0
    if args.signal_command == "wait":
        wait_for_signal(
            args.name,
            timeout_s=args.timeout,
            clear=not args.keep,
        )
        return 0
    if args.signal_command == "clear":
        clear_signal(args.name)
        return 0
    raise SystemExit(f"Unknown signal command: {args.signal_command}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "signal":
            return cmd_signal(args)

        if args.command == "discover":
            return cmd_discover(args)

        client = get_client(args)
        if args.command == "ping":
            return cmd_ping(client)
        if args.command == "status":
            return cmd_status(client)
        if args.command == "deck":
            return cmd_deck(client)
        if args.command == "protocols":
            return cmd_protocols(client)
        if args.command == "runs":
            return cmd_runs(client)
        if args.command == "upload":
            return cmd_upload(client, args)
        if args.command == "run":
            return cmd_run(client, args)
        if args.command == "play":
            return cmd_play(client, args)
        if args.command == "pause":
            return cmd_pause(client, args)
        if args.command == "stop":
            return cmd_stop(client, args)
        if args.command == "wait":
            return cmd_wait(client, args)
        if args.command == "transfer":
            return cmd_transfer(client, args)
        parser.error(f"Unknown command: {args.command}")
        return 2
    except FlexError as exc:
        emit_event("error", message=str(exc))
        return 1
    except KeyboardInterrupt:
        emit_event("interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
