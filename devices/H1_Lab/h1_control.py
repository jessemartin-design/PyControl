#!/usr/bin/env python3
"""Minimal Synergy H1 command script (tray, status, absorbance)."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat
from typing import Any

from pylabrobot.plate_reading import PlateReader
from pylabrobot.plate_reading.agilent import SynergyH1Backend
from pylabrobot.resources import Cor_Axy_96_wellplate_500uL_Ub


DEFAULT_DEVICE_ID = "22040106"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
DEFAULT_RESULTS_DIR = "results"
PLATE_RESOURCE_NAME = "Cor_Axy_96_wellplate_500uL_Ub"
ROW_LABELS = "ABCDEFGH"


def load_config(config_path: Path) -> dict[str, Any]:
  """Return settings from config.json, or {} if the file does not exist."""
  if not config_path.exists():
    return {}
  return json.loads(config_path.read_text(encoding="utf-8"))


def save_device_id(config_path: Path, device_id: str) -> None:
  """Write ftdi_device_id into config.json, creating it from config.example.json if needed."""
  config = load_config(config_path)
  if not config:
    example_path = PROJECT_ROOT / "config.example.json"
    config = load_config(example_path)
  config["ftdi_device_id"] = device_id
  config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
  print(f"Saved ftdi_device_id={device_id} to {config_path}")


def _as_text(value: object) -> str:
  if isinstance(value, bytes):
    return value.decode("utf-8", errors="replace")
  return str(value)


def list_ftdi_devices() -> list[tuple[str, str, str]]:
  """Return (manufacturer, description, serial) for each FTDI device on USB."""
  from pylibftdi import Driver

  return [
    (_as_text(maker), _as_text(description), _as_text(serial))
    for maker, description, serial in Driver().list_devices()
  ]


def run_discover(config_path: Path, set_device_id: str | None, save: bool) -> int:
  if set_device_id:
    save_device_id(config_path, set_device_id)
    return 0

  devices = list_ftdi_devices()
  if not devices:
    print("No FTDI USB devices found. Check the H1 is powered on and the USB cable is connected.")
    return 1
  print("FTDI USB devices found:")
  for maker, description, serial in devices:
    print(f"  {maker}:{description}:{serial}")

  if save:
    if len(devices) != 1:
      print("Not saving: found more than one device. Re-run with --set-device-id <serial>.")
      return 1
    save_device_id(config_path, devices[0][2])
  return 0


def load_dotenv_file(dotenv_path: Path) -> None:
  """Load simple KEY=VALUE pairs from a local .env file into os.environ."""
  if not dotenv_path.exists():
    return

  for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip("'").strip('"')
    if key and key not in os.environ:
      os.environ[key] = value


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Control a BioTek Synergy H1 from Terminal (tray, status, absorbance)."
  )
  parser.add_argument(
    "command",
    choices=["open", "close", "cycle", "status", "absorbance", "discover"],
    help="Command to run on the H1. 'discover' lists FTDI USB devices (no H1 connection).",
  )
  parser.add_argument(
    "--set-device-id",
    default=None,
    help="For discover only: save this FTDI serial as ftdi_device_id in config.json.",
  )
  parser.add_argument(
    "--save",
    action="store_true",
    help="For discover only: save the serial if exactly one FTDI device is found.",
  )
  parser.add_argument(
    "--config",
    default=None,
    help=f"Path to settings file (default: {DEFAULT_CONFIG_PATH.name} in the device folder).",
  )
  parser.add_argument(
    "--device-id",
    default=None,
    help=(
      "FTDI device serial to use. Precedence: this flag, then H1_FTDIDEVICE_ID "
      "environment variable, then ftdi_device_id in config.json, then legacy .env, "
      f"then {DEFAULT_DEVICE_ID}."
    ),
  )
  parser.add_argument(
    "--wavelength",
    type=int,
    default=None,
    help="Absorbance wavelength in nanometers (required for absorbance).",
  )
  parser.add_argument(
    "--repeats",
    type=int,
    default=1,
    help=(
      "For absorbance only: number of back-to-back full-plate reads with the "
      "tray left closed between reads (default: 1)."
    ),
  )
  parser.add_argument(
    "--output",
    default=None,
    help=(
      "Optional base path for absorbance result files (.csv + matching .json). "
      "Defaults to results/h1_absorbance_<wavelength>nm_result.csv in the device folder "
      "(results_dir in config.json). "
      "With --repeats > 1, writes one pair per repeat using _repNN before the suffix, "
      "plus a _summary.json."
    ),
  )
  parser.add_argument(
    "--no-prompt",
    action="store_true",
    help=(
      "For absorbance only: skip the Terminal plate-load prompt. "
      "Use when a GUI or caller has already confirmed the plate is ready."
    ),
  )
  parser.add_argument(
    "--already-loaded",
    action="store_true",
    help=(
      "For absorbance only: assume the plate is already on the open tray. "
      "Skips the load open/prompt and goes straight to close → read → reopen. "
      "Implies --no-prompt."
    ),
  )
  return parser.parse_args()


def _utc_now() -> str:
  return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _matrix_shape(data: object) -> tuple[int, int] | None:
  if not isinstance(data, list) or not data:
    return None
  if not all(isinstance(row, list) for row in data):
    return None
  rows = len(data)
  cols = len(data[0]) if data else 0
  if cols == 0 or any(len(row) != cols for row in data):
    return None
  return rows, cols


def _normalize_output_base(path: Path) -> Path:
  """Treat --output as a stem path; force .csv as the spreadsheet companion suffix."""
  if path.suffix.lower() in {".csv", ".json", ".txt"}:
    return path.with_suffix(".csv")
  return path.with_suffix(".csv") if path.suffix == "" else path


def _repeat_output_path(base_path: Path, repeat_index: int, repeats: int) -> Path:
  if repeats <= 1:
    return base_path
  return base_path.with_name(f"{base_path.stem}_rep{repeat_index:02d}{base_path.suffix}")


def _json_path_for(csv_path: Path) -> Path:
  return csv_path.with_suffix(".json")


def _delta_stats(matrices: list[list[list[float]]]) -> dict[str, Any] | None:
  shapes = [_matrix_shape(m) for m in matrices]
  if any(s is None for s in shapes) or len(set(shapes)) != 1:
    return None
  assert shapes[0] is not None
  rows, cols = shapes[0]
  abs_deltas: list[float] = []
  for r in range(rows):
    for c in range(cols):
      values = [float(matrices[i][r][c]) for i in range(len(matrices))]
      abs_deltas.append(max(values) - min(values))
  sorted_deltas = sorted(abs_deltas)
  return {
    "shape": [rows, cols],
    "repeats_compared": len(matrices),
    "per_well_max_minus_min": {
      "min": min(abs_deltas),
      "median": sorted_deltas[len(sorted_deltas) // 2],
      "max": max(abs_deltas),
    },
  }


def _absorbance_record(
  *,
  data: list[list[float]],
  wavelength: int,
  device_id: str,
  repeat_index: int,
  repeats: int,
  utc: str,
) -> dict[str, Any]:
  shape = _matrix_shape(data)
  return {
    "schema": "h1_lab.absorbance_result.v1",
    "utc": utc,
    "device_id": device_id,
    "command": "absorbance",
    "wavelength_nm": wavelength,
    "plate": PLATE_RESOURCE_NAME,
    "repeat": repeat_index,
    "repeats": repeats,
    "shape": list(shape) if shape else None,
    "status": "ok",
    "values": data,
  }


def _write_csv_matrix(csv_path: Path, data: list[list[float]]) -> None:
  """Write plate grid CSV: header row,1..N then rows A,B,... with values."""
  shape = _matrix_shape(data)
  if shape is None:
    raise RuntimeError("Cannot write CSV: data is not a rectangular numeric matrix.")
  rows, cols = shape
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["row", *[str(c) for c in range(1, cols + 1)]])
    for r in range(rows):
      label = ROW_LABELS[r] if r < len(ROW_LABELS) else str(r + 1)
      writer.writerow([label, *[data[r][c] for c in range(cols)]])


def _write_absorbance_result(
  csv_path: Path,
  *,
  data: list[list[float]],
  wavelength: int,
  device_id: str,
  repeat_index: int,
  repeats: int,
) -> tuple[Path, Path]:
  utc = _utc_now()
  _write_csv_matrix(csv_path, data)

  json_path = _json_path_for(csv_path)
  record = _absorbance_record(
    data=data,
    wavelength=wavelength,
    device_id=device_id,
    repeat_index=repeat_index,
    repeats=repeats,
    utc=utc,
  )
  json_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
  return csv_path, json_path


def _write_repeat_summary(
  base_path: Path,
  *,
  wavelength: int,
  device_id: str,
  matrices: list[list[list[float]]],
  result_paths: list[Path],
  tray_final_state: str,
) -> Path:
  stats = _delta_stats(matrices)
  summary = {
    "schema": "h1_lab.absorbance_repeat_summary.v1",
    "utc": _utc_now(),
    "device_id": device_id,
    "command": "absorbance",
    "wavelength_nm": wavelength,
    "plate": PLATE_RESOURCE_NAME,
    "repeats": len(matrices),
    "status": "ok",
    "tray_final_state": tray_final_state,
    "read_complete": True,
    "repeatability": stats,
    "result_files": {
      "csv": [str(p.resolve()) for p in result_paths],
      "json": [str(_json_path_for(p).resolve()) for p in result_paths],
    },
  }
  summary_path = base_path.with_name(f"{base_path.stem}_summary.json")
  summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
  return summary_path


def _print_repeatability_summary(matrices: list[list[list[float]]]) -> None:
  stats = _delta_stats(matrices)
  if stats is None:
    print("Repeatability summary: could not compare (shape mismatch or non-matrix data).")
    return

  deltas = stats["per_well_max_minus_min"]
  rows, cols = stats["shape"]
  print("--- REPEATABILITY SUMMARY ---")
  print(f"Repeats compared: {stats['repeats_compared']}")
  print(f"Matrix shape: {rows} rows x {cols} columns")
  print(
    f"Per-well max-min delta: min={deltas['min']:.6f}, "
    f"median={deltas['median']:.6f}, "
    f"max={deltas['max']:.6f}"
  )
  print(
    "Note: this checks software/hardware repeatability on whatever plate is loaded; "
    "it is not a scientific assay validation."
  )
  print("--- END SUMMARY ---\n")


async def _safe_open_tray(plate_reader: PlateReader, reason: str) -> None:
  try:
    print(f"Attempting to open tray ({reason})...")
    await plate_reader.open()
    print("Tray opened.")
  except Exception as exc:
    print(f"WARNING: could not open tray during recovery: {type(exc).__name__}: {exc}")


async def run_h1_command(
  command: str,
  device_id: str,
  wavelength: int | None = None,
  output_path: Path | None = None,
  repeats: int = 1,
  prompt_for_plate: bool = True,
  already_loaded: bool = False,
  results_dir: Path = PROJECT_ROOT / DEFAULT_RESULTS_DIR,
) -> None:
  backend = SynergyH1Backend(device_id=device_id)
  plate_reader = PlateReader(
    name="synergy_h1",
    size_x=1,
    size_y=1,
    size_z=1,
    backend=backend,
  )
  setup_complete = False
  tray_may_hold_plate = False

  try:
    await plate_reader.setup()
    setup_complete = True

    if command == "open":
      print("Opening tray...")
      await plate_reader.open()
      print("Tray opened.")
      return

    if command == "close":
      print("Closing tray...")
      await plate_reader.close()
      print("Tray closed.")
      return

    if command == "cycle":
      print("Opening tray...")
      await plate_reader.open()
      print("Tray opened. Closing tray...")
      await plate_reader.close()
      print("Tray closed.")
      return

    if command == "status":
      firmware = await backend.get_firmware_version()
      serial = await backend.get_serial_number()
      temperature_c = await backend.get_current_temperature()
      print("Connected to Synergy H1.")
      print(f"Serial: {serial}")
      print(f"Firmware: {firmware}")
      print(f"Temperature (C): {temperature_c}")
      return

    if command == "absorbance":
      if wavelength is None:
        raise ValueError("--wavelength is required for the absorbance command.")
      if repeats < 1:
        raise ValueError("--repeats must be at least 1.")

      plate = Cor_Axy_96_wellplate_500uL_Ub(name="h1_plate")
      plate_reader.assign_child_resource(plate)
      print(f"Assigned plate resource: {PLATE_RESOURCE_NAME}")

      if already_loaded:
        print("Assuming plate is already on the open tray (--already-loaded).")
      else:
        print("Opening tray for plate load...")
        await plate_reader.open()
        if prompt_for_plate:
          input(
            "\nPlace the physical Axygen plate on the H1 tray, "
            "then press Enter to continue..."
          )
        else:
          print("Plate-load prompt skipped (--no-prompt).")

      print("Closing tray...")
      await plate_reader.close()
      tray_may_hold_plate = True

      if output_path is None:
        base_path = results_dir / f"h1_absorbance_{wavelength}nm_result.csv"
      else:
        base_path = _normalize_output_base(output_path)
      base_path.parent.mkdir(parents=True, exist_ok=True)

      matrices: list[list[list[float]]] = []
      result_paths: list[Path] = []

      for repeat_index in range(1, repeats + 1):
        print(
          f"Reading absorbance at {wavelength} nm "
          f"(full plate, repeat {repeat_index}/{repeats})..."
        )
        data = await plate_reader.read_absorbance(wavelength=wavelength)
        if _matrix_shape(data) is None:
          raise RuntimeError(
            "Absorbance returned data that is not an 8x12-style numeric matrix; "
            f"got type {type(data).__name__}."
          )
        matrices.append(data)

        formatted_data = pformat(data, width=120, sort_dicts=False)
        shape = _matrix_shape(data)
        print(f"\n--- ABSORBANCE RESULT (repeat {repeat_index}/{repeats}) ---")
        print(f"Python return type: {type(data)}")
        if shape is not None:
          print(f"Matrix shape: {shape[0]} rows x {shape[1]} columns")
        print(formatted_data)
        print("--- END RESULT ---\n")

        csv_path = _repeat_output_path(base_path, repeat_index, repeats)
        csv_path, json_path = _write_absorbance_result(
          csv_path,
          data=data,
          wavelength=wavelength,
          device_id=device_id,
          repeat_index=repeat_index,
          repeats=repeats,
        )
        result_paths.append(csv_path)
        print(f"CSV result saved to: {csv_path.resolve()}")
        print(f"JSON result saved to: {json_path.resolve()}")

      if repeats > 1:
        _print_repeatability_summary(matrices)

      await _safe_open_tray(plate_reader, "plate removal after successful read")
      tray_may_hold_plate = False

      if repeats > 1:
        summary_path = _write_repeat_summary(
          base_path,
          wavelength=wavelength,
          device_id=device_id,
          matrices=matrices,
          result_paths=result_paths,
          tray_final_state="open",
        )
        print(f"Repeat summary JSON saved to: {summary_path.resolve()}")

      print(
        "STATUS: command=absorbance read_complete=true tray_final_state=open"
      )
      print("Absorbance command complete.")
      return
  except Exception as exc:
    print(f"\nERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
    if setup_complete and tray_may_hold_plate:
      await _safe_open_tray(plate_reader, "error recovery so the plate is accessible")
      tray_may_hold_plate = False
    raise
  finally:
    if setup_complete:
      try:
        await plate_reader.stop()
      except Exception as exc:
        print(f"WARNING: could not stop connection cleanly: {type(exc).__name__}: {exc}")


def main() -> None:
  args = parse_args()
  config_path = Path(args.config).expanduser() if args.config else DEFAULT_CONFIG_PATH
  config = load_config(config_path)
  if not config:
    load_dotenv_file(PROJECT_ROOT / ".env")

  if args.command == "discover":
    raise SystemExit(run_discover(config_path, args.set_device_id, args.save))
  if args.set_device_id or args.save:
    raise SystemExit("error: --set-device-id and --save are only valid with the discover command")

  if args.command == "absorbance" and args.wavelength is None:
    raise SystemExit(
      "error: absorbance requires --wavelength <nm> "
      "(example: absorbance --wavelength 600)"
    )
  if args.command == "absorbance" and args.repeats < 1:
    raise SystemExit("error: --repeats must be at least 1")
  if args.command != "absorbance" and args.repeats != 1:
    raise SystemExit("error: --repeats is only valid with the absorbance command")
  if args.command != "absorbance" and args.no_prompt:
    raise SystemExit("error: --no-prompt is only valid with the absorbance command")
  if args.command != "absorbance" and args.already_loaded:
    raise SystemExit("error: --already-loaded is only valid with the absorbance command")

  device_id = str(
    args.device_id
    or os.getenv("H1_FTDIDEVICE_ID")
    or config.get("ftdi_device_id")
    or DEFAULT_DEVICE_ID
  )
  results_dir = Path(config.get("results_dir", DEFAULT_RESULTS_DIR)).expanduser()
  if not results_dir.is_absolute():
    results_dir = PROJECT_ROOT / results_dir
  output_path = Path(args.output).expanduser() if args.output else None
  already_loaded = bool(args.already_loaded)
  prompt_for_plate = not (args.no_prompt or already_loaded)
  try:
    asyncio.run(
      run_h1_command(
        args.command,
        device_id,
        wavelength=args.wavelength,
        output_path=output_path,
        repeats=args.repeats,
        prompt_for_plate=prompt_for_plate,
        already_loaded=already_loaded,
        results_dir=results_dir,
      )
    )
  except Exception:
    raise SystemExit(1) from None


if __name__ == "__main__":
  main()
