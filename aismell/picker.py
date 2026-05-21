"""Optional GUI file picker for aismell.

When the user runs `aismell` with no arguments and stdin is a TTY,
we try to open a native file picker. Falls back to printing a usage
message if no GUI is available (headless terminal, missing tk).

Uses tkinter from stdlib. No new deps.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Supported file types in the picker dialog.
FILETYPES = [
    ("All supported", "*.txt *.md *.docx *.pdf"),
    ("Plain text",    "*.txt *.md"),
    ("Word document", "*.docx"),
    ("PDF",           "*.pdf"),
    ("All files",     "*"),
]


def can_use_gui() -> bool:
    """Best-effort check before importing tkinter (which can be slow)."""
    if not sys.stdin.isatty():
        return False
    if os.environ.get("NO_GUI") == "1":
        return False
    if sys.platform.startswith("linux"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return False
    return True


def pick_file() -> Path | None:
    """Open a native file-picker dialog and return the chosen path."""
    if not can_use_gui():
        return None
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        chosen = filedialog.askopenfilename(
            title="aismell: pick a file to sniff",
            filetypes=FILETYPES,
        )
    finally:
        root.destroy()
    if not chosen:
        return None
    return Path(chosen)
