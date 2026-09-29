#!/usr/bin/env python3
"""Thin GUI for proven Synergy H1 commands via h1_control.py (no direct hardware access)."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent
H1_CONTROL = PROJECT_ROOT / "h1_control.py"


def _venv_python() -> Path:
  if os.name == "nt":
    candidate = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
  else:
    candidate = PROJECT_ROOT / ".venv" / "bin" / "python3"
  return candidate if candidate.exists() else Path(sys.executable)


PYTHON = _venv_python()


class H1ControlGUI:
  def __init__(self, root: tk.Tk) -> None:
    self.root = root
    self.root.title("H1 Lab — Synergy H1")
    self.root.minsize(640, 480)

    self._busy = False
    self._output_queue: queue.Queue[object] = queue.Queue()

    self._build()
    self._poll_output_queue()

  def _build(self) -> None:
    frame = ttk.Frame(self.root, padding=12)
    frame.grid(row=0, column=0, sticky="nsew")
    self.root.columnconfigure(0, weight=1)
    self.root.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1)

    ttk.Label(
      frame,
      text="H1 Lab — Synergy H1 controls",
      font=("Helvetica", 16, "bold"),
    ).grid(row=0, column=0, sticky="w", pady=(0, 8))

    ttk.Label(
      frame,
      text="Buttons call h1_control.py. The GUI does not talk to the instrument directly.",
      wraplength=580,
    ).grid(row=1, column=0, sticky="w", pady=(0, 12))

    controls = ttk.Frame(frame)
    controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    controls.columnconfigure(5, weight=1)

    self.open_btn = ttk.Button(controls, text="Open tray", command=self._on_open)
    self.open_btn.grid(row=0, column=0, padx=(0, 6))
    self.close_btn = ttk.Button(controls, text="Close tray", command=self._on_close)
    self.close_btn.grid(row=0, column=1, padx=(0, 6))
    self.status_btn = ttk.Button(controls, text="Status", command=self._on_status)
    self.status_btn.grid(row=0, column=2, padx=(0, 6))

    ttk.Label(controls, text="Wavelength (nm):").grid(row=0, column=3, padx=(12, 4))
    self.wavelength_var = tk.StringVar(value="600")
    self.wavelength_entry = ttk.Entry(controls, textvariable=self.wavelength_var, width=6)
    self.wavelength_entry.grid(row=0, column=4, padx=(0, 6))

    self.absorbance_btn = ttk.Button(
      controls, text="Absorbance", command=self._on_absorbance
    )
    self.absorbance_btn.grid(row=0, column=5, sticky="w")

    output_frame = ttk.LabelFrame(frame, text="Output", padding=8)
    output_frame.grid(row=3, column=0, sticky="nsew")
    output_frame.columnconfigure(0, weight=1)
    output_frame.rowconfigure(0, weight=1)

    self.output = tk.Text(output_frame, wrap="word", height=20, state="disabled")
    self.output.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    self.output.configure(yscrollcommand=scrollbar.set)

    self.status_var = tk.StringVar(value="Ready.")
    ttk.Label(frame, textvariable=self.status_var).grid(
      row=4, column=0, sticky="w", pady=(8, 0)
    )

  def _append_output(self, text: str) -> None:
    self.output.configure(state="normal")
    self.output.insert("end", text)
    self.output.see("end")
    self.output.configure(state="disabled")

  def _set_busy(self, busy: bool) -> None:
    self._busy = busy
    state = "disabled" if busy else "normal"
    for widget in (
      self.open_btn,
      self.close_btn,
      self.status_btn,
      self.absorbance_btn,
      self.wavelength_entry,
    ):
      widget.configure(state=state)
    self.status_var.set("Running command…" if busy else "Ready.")

  def _on_open(self) -> None:
    self._run_command(["open"])

  def _on_close(self) -> None:
    self._run_command(["close"])

  def _on_status(self) -> None:
    self._run_command(["status"])

  def _on_absorbance(self) -> None:
    raw = self.wavelength_var.get().strip()
    try:
      wavelength = int(raw)
    except ValueError:
      messagebox.showerror(
        "Invalid wavelength",
        "Enter wavelength as a whole number in nanometers (for example 600).",
      )
      return
    if wavelength <= 0:
      messagebox.showerror("Invalid wavelength", "Wavelength must be a positive number.")
      return

    proceed = messagebox.askokcancel(
      "Start absorbance",
      "This will:\n"
      "1. Open the tray\n"
      "2. Ask you to confirm after the plate is in place\n"
      "3. Close the tray, read, then open again\n\n"
      f"Wavelength: {wavelength} nm\n\n"
      "Click OK to open the tray.",
    )
    if not proceed:
      return

    self._run_command(
      ["open"],
      on_success=lambda: self._absorbance_after_open(wavelength),
    )

  def _absorbance_after_open(self, wavelength: int) -> None:
    ready = messagebox.askokcancel(
      "Plate ready?",
      "Place the Axygen plate on the open tray now.\n\n"
      "Click OK only when the plate is seated and you are ready to read.\n"
      "Click Cancel to stop without reading (tray will stay open).",
    )
    if not ready:
      self._append_output("\n[Absorbance cancelled after tray open.]\n")
      return

    self._run_command(
      [
        "absorbance",
        "--wavelength",
        str(wavelength),
        "--already-loaded",
      ]
    )

  def _run_command(
    self,
    args: list[str],
    on_success: Callable[[], None] | None = None,
  ) -> None:
    if self._busy:
      return
    if not PYTHON.exists() or not H1_CONTROL.exists():
      messagebox.showerror(
        "Missing files",
        f"Expected:\n{PYTHON}\n{H1_CONTROL}",
      )
      return

    self._set_busy(True)
    self._append_output(f"\n$ {' '.join([PYTHON.name, H1_CONTROL.name, *args])}\n")

    thread = threading.Thread(
      target=self._worker,
      args=(args, on_success),
      daemon=True,
    )
    thread.start()

  def _worker(self, args: list[str], on_success: Callable[[], None] | None) -> None:
    exit_code = 1
    try:
      process = subprocess.Popen(
        [str(PYTHON), str(H1_CONTROL), *args],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
      )
      assert process.stdout is not None
      for line in process.stdout:
        self._output_queue.put(line)
      exit_code = process.wait()
      if exit_code == 0:
        self._output_queue.put("\n[Command finished successfully.]\n")
      else:
        self._output_queue.put(f"\n[Command failed with exit code {exit_code}.]\n")
    except Exception as exc:
      self._output_queue.put(f"\nERROR launching h1_control.py: {exc}\n")
    finally:
      self._output_queue.put(("__done__", exit_code, on_success))

  def _poll_output_queue(self) -> None:
    try:
      while True:
        item = self._output_queue.get_nowait()
        if isinstance(item, tuple) and item and item[0] == "__done__":
          _, exit_code, on_success = item
          self._set_busy(False)
          if exit_code == 0 and on_success is not None:
            self.root.after(0, on_success)
        else:
          self._append_output(str(item))
    except queue.Empty:
      pass
    self.root.after(100, self._poll_output_queue)


def main() -> None:
  root = tk.Tk()
  H1ControlGUI(root)
  root.mainloop()


if __name__ == "__main__":
  main()
