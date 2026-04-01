"""Self-contained console output panel with coloured log tags."""

from __future__ import annotations

import customtkinter as ctk
import tkinter as tk

from helpers.platform_utils import is_macos
from gui.theme import COLORS, RADIUS, PAD
from gui.widgets import section_label


class ConsolePanel(ctk.CTkFrame):
    """Encapsulates the output textbox, clear button, and log-tag colouring."""

    _MAX_LINES = 5000
    _TRIM_BATCH = 500

    _TAG_RULES: list[tuple[str, tuple[str, ...]]] = [
        ("ok",   ("success", "succeeded", "done", "complete")),
        ("err",  ("error", "exception", "traceback", "failed")),
        ("warn", ("warn", "warning", "skip")),
    ]

    def __init__(self, parent: ctk.CTkFrame, fonts: dict):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._in_batch = False
        self.visible = False
        self._fonts = fonts
        self._build()

    @property
    def _tb(self) -> tk.Text:
        """Underlying tk.Text — centralized for easier migration if CTk internals change."""
        return self._textbox._textbox

    def _build(self):
        frame = ctk.CTkFrame(
            self, border_color=COLORS["console_border"],
            fg_color=COLORS["console_bg"], corner_radius=RADIUS["card"], border_width=1,
        )
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]))

        section_label(header, "Output", self._fonts["section"]).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, command=self.clear,
            hover_color=COLORS["hover"], font=self._fonts["body_sm"],
            text_color=COLORS["muted"], fg_color="transparent",
            corner_radius=6, text="Clear", height=26, width=60,
        ).grid(row=0, column=1, sticky="e", padx=(PAD["sm"], 0))

        self._textbox = ctk.CTkTextbox(
            frame, fg_color=COLORS["console_inner"],
            corner_radius=RADIUS["input"], text_color=COLORS["text"],
            font=self._fonts["mono"], border_spacing=10,
            state="disabled", wrap="word",
        )
        self._textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._tb.bind("<MouseWheel>", self._on_mousewheel)

        for tag, color in [
            ("ok", COLORS["success"]), ("err", COLORS["error"]),
            ("warn", COLORS["warn"]), ("info", COLORS["text"]),
            ("cmd", COLORS["cmd"]),   ("step", COLORS["accent"]),
        ]:
            self._tb.tag_config(tag, foreground=color)

    def _on_mousewheel(self, event) -> str:
        delta = -event.delta if is_macos() else int(-event.delta / 120)
        self._tb.yview_scroll(delta, "units")
        return "break"

    def _classify(self, text: str) -> str:
        if text.startswith(">>"):
            return "cmd"
        lower = text.lower()
        for tag, keywords in self._TAG_RULES:
            if any(k in lower for k in keywords):
                return tag
        return "info"

    def classify(self, text: str) -> str:
        """Public classifier used by queue draining code."""
        return self._classify(text)

    def _should_scroll(self) -> bool:
        """Auto-scroll only when the Console tab is visible and user hasn't scrolled up."""
        return self.visible and self._tb.yview()[1] >= 0.99

    def begin_batch(self):
        """Enter batch mode — keeps textbox writable to avoid per-line state toggles."""
        if not self._in_batch:
            self._auto_scroll = self._should_scroll()
            self._textbox.configure(state="normal")
            self._in_batch = True

    def end_batch(self):
        """Leave batch mode — trims excess lines, disables textbox, conditionally scrolls."""
        if not self._in_batch:
            return
        self._in_batch = False
        line_count = int(self._tb.index("end-1c").split(".")[0])
        if line_count > self._MAX_LINES:
            self._tb.delete("1.0", f"{self._TRIM_BATCH}.0")
        self._textbox.configure(state="disabled")
        if self._auto_scroll:
            self._textbox.see(tk.END)

    def _insert(self, text: str, tag: str):
        if not self._in_batch:
            scroll = self._should_scroll()
            self._textbox.configure(state="normal")
        self._tb.insert(tk.END, text, tag)
        if not self._in_batch:
            line_count = int(self._tb.index("end-1c").split(".")[0])
            if line_count > self._MAX_LINES:
                self._tb.delete("1.0", f"{self._TRIM_BATCH}.0")
            self._textbox.configure(state="disabled")
            if scroll:
                self._textbox.see(tk.END)

    def append(self, text: str):
        self._insert(text, self.classify(text))

    def append_tagged(self, text: str, tag: str):
        self._insert(text, tag)

    def batch_insert(self, items: list[tuple[str, str]]):
        """Insert multiple (text, tag) pairs, coalescing consecutive same-tag entries."""
        if not items:
            return
        tb = self._tb
        coalesced: list[tuple[str, str]] = []
        for text, tag in items:
            if coalesced and coalesced[-1][1] == tag:
                coalesced[-1] = (coalesced[-1][0] + text, tag)
            else:
                coalesced.append((text, tag))
        for text, tag in coalesced:
            tb.insert(tk.END, text, tag)

    def clear(self):
        self._textbox.configure(state="normal")
        self._textbox.delete(1.0, tk.END)
        self._textbox.configure(state="disabled")
