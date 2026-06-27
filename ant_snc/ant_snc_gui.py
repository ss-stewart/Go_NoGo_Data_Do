#!/usr/bin/env python3
"""
Part 3/3: ANT/SNC Data Processing GUI
Owner: Hinton, Ph.D Laboratory
Version 1.0

Runs the ANT/SNC cleaner and analyzer without using terminal commands.

Usage:
    python3 ant_snc/ant_snc_gui.py
"""

import contextlib
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from run_ant_snc_pipeline import run_pipeline

class QueueWriter:
    """Redirect printed pipeline messages into the GUI log box."""
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue

    def write(self, message: str) -> None:
        if message.strip():
            self.log_queue.put(("log", message))

    def flush(self) -> None:
        pass

class AntSNCGui(tk.Tk):
    """GUI wrapper for the ANT/SNC processing pipeline."""
    def __init__(self) -> None:
        super().__init__()
        self.title("ANT/SNC Data Processing Tool")
        self.geometry("760x520")
        self.minsize(700, 460)
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.abspath("ant_snc_output"))
        self.status_text = tk.StringVar(value="Ready.")
        self.log_queue: queue.Queue = queue.Queue()
        self._build_layout()
        self.after(100, self._poll_log_queue)

    def _build_layout(self) -> None:
        padding = {"padx": 12, "pady": 8}
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)
        title_label = ttk.Label(
            main_frame,
            text="ANT/SNC Data Processing Tool",
            font=("TkDefaultFont", 16, "bold"),
        )
        title_label.pack(anchor="w", pady=(0, 10))
        instructions = (
            "Select the raw ANT/SNC data folder, choose an output folder, "
            "then run the pipeline."
        )
        ttk.Label(main_frame, text=instructions, wraplength=720).pack(anchor="w")
        input_frame = ttk.LabelFrame(main_frame, text="1. Raw ANT/SNC data folder")
        input_frame.pack(fill="x", **padding)

        ttk.Entry(input_frame, textvariable=self.input_dir).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 6),
            pady=8,
        )
        ttk.Button(
            input_frame,
            text="Browse...",
            command=self.choose_input_folder,
        ).pack(side="right", padx=(0, 8), pady=8)

        output_frame = ttk.LabelFrame(main_frame, text="2. Output folder")
        output_frame.pack(fill="x", **padding)

        ttk.Entry(output_frame, textvariable=self.output_dir).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 6),
            pady=8,
        )
        ttk.Button(
            output_frame,
            text="Browse...",
            command=self.choose_output_folder,
        ).pack(side="right", padx=(0, 8), pady=8)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", **padding)

        self.run_button = ttk.Button(
            button_frame,
            text="Run ANT/SNC Pipeline",
            command=self.run_pipeline_from_gui,
        )
        self.run_button.pack(side="left")

        ttk.Label(button_frame, textvariable=self.status_text).pack(
            side="left",
            padx=(16, 0),
        )
        log_frame = ttk.LabelFrame(main_frame, text="Processing log")
        log_frame.pack(fill="both", expand=True, **padding)
        self.log_box = tk.Text(log_frame, height=12, wrap="word")
        self.log_box.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)
        self.log_box.configure(yscrollcommand=scrollbar.set)

    def choose_input_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose raw ANT/SNC data folder")
        if folder:
            self.input_dir.set(folder)

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_dir.set(folder)

    def run_pipeline_from_gui(self) -> None:
        input_dir = self.input_dir.get().strip()
        output_dir = self.output_dir.get().strip()

        if not input_dir:
            messagebox.showerror("Missing input folder", "Choose a raw data folder.")
            return
        if not output_dir:
            messagebox.showerror("Missing output folder", "Choose an output folder.")
            return
        if not os.path.isdir(input_dir):
            messagebox.showerror(
                "Invalid input folder",
                "The selected raw data folder does not exist.",
            )
            return

        self.run_button.configure(state="disabled")
        self.status_text.set("Running...")
        self.log_box.delete("1.0", tk.END)
        self._log("Starting ANT/SNC pipeline...\n")

        worker = threading.Thread(
            target=self._pipeline_worker,
            args=(input_dir, output_dir),
            daemon=True,
        )
        worker.start()

    def _pipeline_worker(self, input_dir: str, output_dir: str) -> None:
        try:
            writer = QueueWriter(self.log_queue)
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                run_pipeline(input_dir, output_dir)
            self.log_queue.put(("done", output_dir))
        except Exception as exc:
            self.log_queue.put(("error", str(exc)))

    def _poll_log_queue(self) -> None:
        try:
            while True:
                event_type, payload = self.log_queue.get_nowait()
                if event_type == "log":
                    self._log(payload)
                elif event_type == "done":
                    self.status_text.set("Complete.")
                    self.run_button.configure(state="normal")
                    messagebox.showinfo(
                        "Pipeline complete",
                        f"ANT/SNC processing is complete.\n\nOutput folder:\n{payload}",
                    )
                elif event_type == "error":
                    self.status_text.set("Error.")
                    self.run_button.configure(state="normal")
                    messagebox.showerror("Pipeline error", payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    def _log(self, message: str) -> None:
        self.log_box.insert(tk.END, message)
        self.log_box.see(tk.END)

def main() -> None:
    app = AntSNCGui()
    app.mainloop()

if __name__ == "__main__":
    main()
