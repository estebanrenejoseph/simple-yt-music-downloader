#!/usr/bin/env python3
"""
gui.py — Graphical User Interface (CustomTkinter) for core.

Processing runs in a separate background thread to keep the main window responsive.
The worker thread communicates with the UI via a thread-safe queue (queue.Queue),
polled periodically by the main thread since Tkinter is not thread-safe.

Launched by symd.py (`symd` with no argument, or `symd --gui`), or directly:
  python3 gui.py

Dependencies: pip install customtkinter yt-dlp mutagen (+ ffmpeg)
"""

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

try:
    import customtkinter as ctk
except ImportError:
    sys.exit("Critical Error: The 'customtkinter' module is missing. Installation: pip install customtkinter")

from deps import missing_dependencies

# Available audio format options and local search depth choices for file auditing
FORMATS = ["best", "mp3", "flac", "m4a", "opus"]
DEPTHS = ["1", "2", "3", "4", "5"]

# Apply system theme appearance and default accent colors
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application window handling the graphical interface and worker thread orchestration."""

    def __init__(self) -> None:
        super().__init__()
        self.title("YT Music Downloader")
        self.geometry("800x720")
        self.minsize(660, 600)

        # Thread communication queues and worker management attributes
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.reporter = None

        # State variables bound to form inputs and configuration checkboxes
        music = Path.home() / "Music"
        self.link_var = tk.StringVar()
        self.dir_var = tk.StringVar(value=str(music if music.is_dir() else Path.home()))
        self.cookies_var = tk.StringVar()
        self.format_var = tk.StringVar(value="best")
        self.depth_var = tk.StringVar(value="1")
        self.sort_var = tk.BooleanVar(value=False)
        self.archive_var = tk.BooleanVar(value=False)
        self.export_var = tk.BooleanVar(value=False)

        # Initialize UI layout and start the event polling loop
        self._build()
        self._toggle_depth()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll)

    # --------------------------------------------------------------------------
    # Interface Construction
    # --------------------------------------------------------------------------

    def _build(self) -> None:
        """Constructs and arranges all UI widgets across the grid layout hierarchy."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)  # Log output box expands to fill remaining vertical space

        # Application header title label
        ctk.CTkLabel(
            self, text="YT Music Downloader", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

        # --- Settings Frame ---
        settings = ctk.CTkFrame(self)
        settings.grid(row=1, column=0, padx=20, pady=6, sticky="ew")
        settings.columnconfigure(1, weight=1)

        self._entry_row(settings, 0, "Link", self.link_var,
                        placeholder="https://music.youtube.com/playlist?list=...")
        self._entry_row(settings, 1, "Directory", self.dir_var, browse=self._browse_dir)
        self._entry_row(settings, 2, "Cookies", self.cookies_var,
                        browse=self._browse_cookies, placeholder="(optional) cookies.txt")

        # Format selector and search depth configuration row
        ctk.CTkLabel(settings, text="Format", anchor="w").grid(
            row=3, column=0, padx=(12, 8), pady=8, sticky="w")
        choices = ctk.CTkFrame(settings, fg_color="transparent")
        choices.grid(row=3, column=1, columnspan=2, padx=4, pady=8, sticky="w")
        ctk.CTkOptionMenu(choices, values=FORMATS, variable=self.format_var, width=110).pack(side="left")
        ctk.CTkLabel(choices, text="Search Depth").pack(side="left", padx=(24, 8))
        self.depth_menu = ctk.CTkOptionMenu(choices, values=DEPTHS, variable=self.depth_var, width=70)
        self.depth_menu.pack(side="left")

        # --- Options Frame ---
        options = ctk.CTkFrame(self)
        options.grid(row=2, column=0, padx=20, pady=6, sticky="ew")
        ctk.CTkCheckBox(options, text="Sort by artist",
                        variable=self.sort_var).pack(side="left", padx=14, pady=12)
        ctk.CTkCheckBox(options, text="Archive mode (.archive.txt)",
                        variable=self.archive_var).pack(side="left", padx=14, pady=12)
        ctk.CTkCheckBox(options, text="Export missing tracks",
                        variable=self.export_var, command=self._toggle_depth).pack(side="left", padx=14, pady=12)

        # --- Actions and Progress Frame ---
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, padx=20, pady=(6, 0), sticky="ew")
        actions.columnconfigure(2, weight=1)

        self.start_btn = ctk.CTkButton(actions, text="Start", width=110, command=self._start)
        self.start_btn.grid(row=0, column=0, pady=6)
        self.cancel_btn = ctk.CTkButton(
            actions, text="Cancel", width=110, state="disabled",
            fg_color="#b33a3a", hover_color="#8f2d2d", command=self._cancel)
        self.cancel_btn.grid(row=0, column=1, padx=8, pady=6)
        self.status = ctk.CTkLabel(actions, text="Ready", anchor="w")
        self.status.grid(row=0, column=2, padx=8, sticky="ew")

        self.progress = ctk.CTkProgressBar(actions)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, columnspan=3, pady=(0, 6), sticky="ew")

        # --- Logs Textbox Frame ---
        self.log_box = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log_box.grid(row=4, column=0, padx=20, pady=(6, 18), sticky="nsew")

    def _entry_row(self, parent: ctk.CTkFrame, row: int, label: str, var: tk.StringVar, browse: Callable[[], None] | None = None, placeholder: str = "") -> None:
        """Helper method to generate labeled entry rows with optional file browser buttons."""
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=row, column=0, padx=(12, 8), pady=8, sticky="w")
        entry = ctk.CTkEntry(parent, textvariable=var, placeholder_text=placeholder)
        if browse:
            entry.grid(row=row, column=1, padx=4, pady=8, sticky="ew")
            ctk.CTkButton(parent, text="Browse", width=90, command=browse).grid(
                row=row, column=2, padx=(4, 12), pady=8)
        else:
            entry.grid(row=row, column=1, columnspan=2, padx=(4, 12), pady=8, sticky="ew")

    # --------------------------------------------------------------------------
    # UI Action Handlers
    # --------------------------------------------------------------------------

    def _browse_dir(self) -> None:
        """Opens a directory selection dialog to update the target output path."""
        chosen = filedialog.askdirectory(initialdir=self.dir_var.get() or str(Path.home()))
        if chosen:
            self.dir_var.set(chosen)

    def _browse_cookies(self) -> None:
        """Opens a file dialog to select an authentication cookies text file."""
        chosen = filedialog.askopenfilename(
            title="Select cookies.txt file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if chosen:
            self.cookies_var.set(chosen)

    def _toggle_depth(self) -> None:
        """Enables or disables the search depth menu based on the export missing tracks checkbox state."""
        # Search depth is only relevant when performing an audit of missing tracks
        self.depth_menu.configure(state="normal" if self.export_var.get() else "disabled")

    def _set_running(self, running: bool) -> None:
        """Toggles interface control states and status labels depending on execution status."""
        self.start_btn.configure(state="disabled" if running else "normal")
        self.cancel_btn.configure(state="normal" if running else "disabled")
        if running:
            self.progress.set(0)
            self.status.configure(text="Starting...")
        else:
            self.status.configure(text="Ready")

    def _append_log(self, message: str) -> None:
        """Appends a new log message to the read-only scrolling textbox safely."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # --------------------------------------------------------------------------
    # Worker Thread Lifecycle (Start / Cancel)
    # --------------------------------------------------------------------------

    def _start(self) -> None:
        """Validates user inputs, instantiates execution configurations, and spawns the background worker thread."""
        from core import Options, Reporter, run

        link = self.link_var.get().strip()
        directory = self.dir_var.get().strip()
        cookies = self.cookies_var.get().strip()

        if not link:
            messagebox.showwarning("Missing Link", "Please paste a valid video or playlist link.")
            return
        if not directory:
            messagebox.showwarning("Missing Directory", "Please choose a target destination directory.")
            return

        opts = Options(
            link=link,
            dir=Path(directory).expanduser(),
            format=self.format_var.get(),
            depth=int(self.depth_var.get()),
            cookies=Path(cookies).expanduser() if cookies else None,
            archive=self.archive_var.get(),
            export=self.export_var.get(),
            sort=self.sort_var.get(),
        )

        self.reporter = Reporter(
            log=lambda msg: self.events.put(("log", msg)),
            progress=lambda fraction, text: self.events.put(("progress", fraction, text)),
        )
        self._append_log("─" * 40)
        self._set_running(True)

        self.worker = threading.Thread(target=self._work, args=(run, opts), daemon=True)
        self.worker.start()

    def _work(self, run: Callable, opts) -> None:
        """Executed inside the background worker thread; must never directly touch UI widgets."""
        try:
            run(opts, self.reporter)
        except Exception as exc:  # noqa: BLE001 — capture any unexpected runtime exception into logs
            self.events.put(("log", f"Error: {exc}"))
        finally:
            self.events.put(("done",))

    def _cancel(self) -> None:
        """Signals cancellation to the running core process via the active reporter instance."""
        if self.reporter:
            self.reporter.cancel()
            self.cancel_btn.configure(state="disabled")
            self.status.configure(text="Cancelling...")
            self._append_log("Cancellation requested...")

    def _on_close(self) -> None:
        """Handles graceful window destruction, prompting the user if a background task is running."""
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("Quit", "A download process is currently running. Exit anyway?"):
                return
            if self.reporter:
                self.reporter.cancel()
        self.destroy()

    # --------------------------------------------------------------------------
    # Event Queue Polling Loop (Main Thread)
    # --------------------------------------------------------------------------

    def _poll(self) -> None:
        """Periodically checks the thread-safe event queue to update UI components without blocking."""
        last_progress = None
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "log":
                    self._append_log(event[1])
                elif event[0] == "progress":
                    last_progress = event  # Only retain the latest progress update per polling cycle
                elif event[0] == "done":
                    self._set_running(False)
        except queue.Empty:
            pass

        if last_progress:
            _, fraction, text = last_progress
            self.progress.set(fraction)
            self.status.configure(text=text[:90] if text else "")

        self.after(100, self._poll)


def main() -> None:
    """Main entry point checking system dependencies before launching the graphical interface application."""
    problems = missing_dependencies()
    if problems:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", "\n\n".join(problems))
        sys.exit(1)

    App().mainloop()


if __name__ == "__main__":
    main()
