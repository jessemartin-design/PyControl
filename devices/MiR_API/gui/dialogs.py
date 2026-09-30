"""Small Tk dialogs for the MiR GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def ask_keep_or_stop_charging(parent: tk.Misc, kind: str) -> bool:
    """
    Ask whether to abort charging / docking.

    kind: \"charging\" or \"about_to_charge\"
    Returns True to stop charging, False to keep charging.
    """
    if kind == "charging":
        headline = "MiR is charging"
    else:
        headline = "MiR is about to charge"

    result = {"stop": False}

    dialog = tk.Toplevel(parent)
    dialog.title("Charging")
    dialog.transient(parent)
    dialog.resizable(False, False)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=headline, font=("", 12, "bold")).pack(anchor="w")
    ttk.Label(
        frame,
        text="Do you want to stop charging?",
        wraplength=360,
        justify="left",
    ).pack(anchor="w", pady=(8, 16))

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x")

    def keep() -> None:
        result["stop"] = False
        dialog.destroy()

    def stop() -> None:
        result["stop"] = True
        dialog.destroy()

    ttk.Button(buttons, text="Keep Charging", command=keep).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Stop Charging", command=stop).pack(side="left")

    dialog.protocol("WM_DELETE_WINDOW", keep)
    dialog.bind("<Escape>", lambda _event: keep())

    # Center over parent when possible.
    dialog.update_idletasks()
    try:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        dw = dialog.winfo_width()
        dh = dialog.winfo_height()
        dialog.geometry(f"+{px + max(0, (pw - dw) // 2)}+{py + max(0, (ph - dh) // 2)}")
    except tk.TclError:
        pass

    parent.wait_window(dialog)
    return bool(result["stop"])
