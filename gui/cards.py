"""CardBuilderMixin - all UI card and step-row construction for BuildApp.

This mixin references ``self.*`` attributes defined on the host class
(``BuildApp``), including step_vars, _fonts, _section_switches, etc.
"""

from __future__ import annotations
import customtkinter as ctk
import os


from gui.widgets import card, section_label, segmented_button
from core.constants import DEFAULT_GMAIL_RECIPIENTS, StepDef
from gui.theme import COLORS, RADIUS, PAD
from helpers.version import read_version


class CardBuilderMixin:
    """Extracted card-building methods mixed into BuildApp."""

    def _track(self, widget):
        """Register an interactive widget for pipeline lock/unlock."""
        self._lockable_widgets.append(widget)
        return widget

    # ── Info card ─────────────────────────────────────────────────────────────

    def _build_info_card(self, row: int):
        frame = card(self.config_scroll, row=row, column=0, sticky="ew", pady=(0, 12))
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        section_label(frame, "App Info", self._fonts["section"]).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=PAD["lg"], pady=(PAD["md"], PAD["sm"]),
        )

        version, build = read_version()

        ctk.CTkLabel(frame, text="Version:").grid(
            row=1, column=0, padx=(PAD["lg"], PAD["sm"]), pady=(0, PAD["sm"]), sticky="e",
        )
        self.version_var = ctk.StringVar(value=version)
        self._track(ctk.CTkEntry(
            frame, textvariable=self.version_var, corner_radius=RADIUS["input"], border_width=1,
        )).grid(row=1, column=1, padx=(0, PAD["sm"]), pady=(0, PAD["sm"]), sticky="ew")

        ctk.CTkLabel(frame, text="Build:").grid(
            row=1, column=2, padx=(PAD["sm"], PAD["sm"]), pady=(0, PAD["sm"]), sticky="e",
        )
        self.build_var = ctk.StringVar(value=build)
        self._track(ctk.CTkEntry(
            frame, textvariable=self.build_var, corner_radius=RADIUS["input"], border_width=1,
        )).grid(row=1, column=3, padx=(0, PAD["lg"]), pady=(0, PAD["sm"]), sticky="ew")

        ctk.CTkLabel(frame, text="Commit Msg:").grid(
            row=2, column=0, padx=(PAD["lg"], PAD["sm"]), pady=(0, PAD["lg"]), sticky="e",
        )
        self.commit_msg_var = ctk.StringVar(value="pre-release cleanup")
        self._track(ctk.CTkEntry(
            frame, textvariable=self.commit_msg_var, corner_radius=RADIUS["input"], border_width=1,
        )).grid(row=2, column=1, columnspan=3, padx=(0, PAD["lg"]), pady=(0, PAD["lg"]), sticky="ew")

    # ── Common card ───────────────────────────────────────────────────────────

    def _build_common_card(self, row: int) -> int:
        c = card(self.config_scroll, row=row, column=0, sticky="ew", pady=(0, 12))
        c.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(c, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], 5))
        section_label(header, "Common", self._fonts["section"]).grid(row=0, column=0, sticky="w")

        self._add_step_row(c, "clean", "Flutter Clean", "Remove build cache", False, "common", 1)
        self._build_pub_row(c, 2)
        return row + 1

    def _build_pub_row(self, parent: ctk.CTkFrame, grid_row: int):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=PAD["sm"])
        row_frame.grid_columnconfigure(1, weight=1)

        var = ctk.BooleanVar(value=False)
        self.step_vars["pub_get"] = var
        switch = ctk.CTkSwitch(
            row_frame, progress_color=COLORS["accent"],
            text="Dependencies", font=self._fonts["body"], variable=var,
        )
        switch.grid(row=0, column=0, sticky="w")
        self._section_switches.setdefault("common", []).append(switch)

        self._track(segmented_button(
            row_frame, values=["pub get", "pub upgrade"],
            variable=self._pub_mode, font=self._fonts["body_sm"],
        )).grid(row=0, column=1, padx=PAD["sm"])

        self._add_status_widgets(row_frame, "pub_get", column=2)

    # ── Generic section card (unified for Git, Android, iOS, Post-Build) ─────

    def _build_section_card(
        self,
        title: str,
        steps: list[StepDef],
        section_key: str,
        *,
        row: int,
        enable_var: ctk.BooleanVar | None = None,
        shorebird_var: ctk.BooleanVar | None = None,
        shorebird_mode_var: ctk.StringVar | None = None,
    ) -> int:
        c = card(self.config_scroll, row=row, column=0, sticky="ew", pady=(0, 12))
        c.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(c, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=(PAD["md"], 5))
        header.grid_columnconfigure(0, weight=1)

        section_label(header, title, self._fonts["section"]).grid(row=0, column=0, sticky="w")

        col = 1
        if shorebird_var is not None:
            col = self._add_shorebird_controls(header, section_key, shorebird_var, shorebird_mode_var, col)

        if enable_var is not None:
            self._section_enable_vars[section_key] = enable_var
            self._track(ctk.CTkSwitch(
                header, variable=enable_var, text="Enabled",
                font=self._fonts["body_sm"], progress_color=COLORS["accent"],
                command=lambda sk=section_key: self._on_section_toggle(sk),
            )).grid(row=0, column=col, sticky="e")

        self._build_step_rows(c, steps, section_key)
        return row + 1

    def _add_shorebird_controls(
        self, header: ctk.CTkFrame, section_key: str,
        shorebird_var: ctk.BooleanVar, mode_var: ctk.StringVar | None,
        start_col: int,
    ) -> int:
        col = start_col
        mode_seg: ctk.CTkSegmentedButton | None = None

        if mode_var is not None:
            mode_seg = segmented_button(
                header, values=["Release", "Patch"],
                variable=mode_var, font=self._fonts["body_sm"],
                command=lambda _=None, sk=section_key: self._on_shorebird_mode_changed(sk),
            )
            mode_seg.grid(row=0, column=col, sticky="e", padx=(0, PAD["sm"]))
            self._sb_mode_widgets[section_key] = mode_seg
            col += 1

        cb = ctk.CTkCheckBox(
            header, variable=shorebird_var, text="Shorebird",
            font=self._fonts["body_sm"], checkbox_width=18, checkbox_height=18,
            corner_radius=4, border_width=2,
            command=lambda sk=section_key, sv=shorebird_var: self._on_shorebird_toggle(sk, sv),
        )
        cb.grid(row=0, column=col, sticky="e", padx=(0, PAD["md"]))
        self._sb_checkboxes[section_key] = cb
        col += 1

        if not self._shorebird_ok:
            shorebird_var.set(False)
            cb.configure(state="disabled")
            hint = ctk.CTkLabel(
                header, text="(not installed)",
                font=self._fonts["body_sm"], text_color=COLORS["danger"],
            )
            hint.grid(row=0, column=col, sticky="e", padx=(0, PAD["sm"]))
            self._sb_hint_labels[section_key] = hint
            col += 1

        if mode_seg is not None:
            mode_seg.configure(state="normal" if shorebird_var.get() else "disabled")

        return col

    # ── Step row helpers (unified: handles optional platform checkboxes) ──────

    def _build_step_rows(
        self, parent: ctk.CTkFrame, steps: list[StepDef], section_key: str,
    ):
        for i, (key, label, desc, default_on) in enumerate(steps, start=1):
            self._add_step_row(parent, key, label, desc, default_on, section_key, i)

    def _add_step_row(
        self,
        parent: ctk.CTkFrame,
        key: str, label: str, desc: str,
        default_on: bool, section_key: str, grid_row: int,
    ) -> ctk.CTkSwitch:
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=PAD["lg"], pady=PAD["sm"])
        row_frame.grid_columnconfigure(1, weight=1)

        var = ctk.BooleanVar(value=default_on)
        self.step_vars[key] = var
        switch = ctk.CTkSwitch(
            row_frame, progress_color=COLORS["accent"],
            text=f"{label}  —  {desc}", font=self._fonts["body"], variable=var,
        )
        switch.grid(row=0, column=0, sticky="w")
        self.step_switches[key] = switch
        self._section_switches.setdefault(section_key, []).append(switch)

        status_col = 1
        if key == "shutdown":
            self._track(segmented_button(
                row_frame, values=["Shutdown", "Sleep"],
                variable=self._power_mode, font=self._fonts["body_sm"],
            )).grid(row=0, column=status_col, padx=PAD["sm"])
            status_col += 1
            qcb = self._track(ctk.CTkCheckBox(
                row_frame,
                text="Quit app after countdown",
                variable=self._quit_after_power,
                font=self._fonts["body_sm"],
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=4,
                border_width=2,
            ))
            qcb.grid(row=0, column=status_col, padx=(0, PAD["sm"]), sticky="w")
            self._post_sub_widgets.append(qcb)
            status_col += 1

        self._add_status_widgets(row_frame, key, column=status_col)
        return switch

    def _add_status_widgets(self, parent: ctk.CTkFrame, key: str, column: int):
        pb = ctk.CTkProgressBar(
            parent, progress_color=COLORS["accent"],
            mode="indeterminate", width=100, height=8,
        )
        pb.grid(row=0, column=column, sticky="e", padx=PAD["sm"])
        pb.grid_remove()
        self.step_progress_bars[key] = pb

        lbl = ctk.CTkLabel(
            parent, text_color=COLORS["text_dim"],
            font=self._fonts["mono_sm"], text="-",
        )
        lbl.grid(row=0, column=column + 1, sticky="e")
        self.step_status_labels[key] = lbl

    # ── Distribution card ─────────────────────────────────────────────────────

    def _build_dist_card(self, row: int):
        frame = card(self.config_scroll, row=row, column=0, sticky="ew", pady=(0, 12))
        frame.grid_columnconfigure(0, weight=1)

        section_label(frame, "Distribution", self._fonts["section"]).grid(
            row=0, column=0, sticky="w", padx=PAD["lg"], pady=(PAD["md"], 5),
        )
        ctk.CTkLabel(
            frame, text="Recipient Emails (comma-separated):",
            font=self._fonts["body_sm"], text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=PAD["lg"], pady=(0, PAD["sm"]))

        default_recipients = (
            os.environ.get("DISTRIBUTION_EMAILS", "").strip() or ", ".join(DEFAULT_GMAIL_RECIPIENTS)
        )
        self.recipients_var = ctk.StringVar(value=default_recipients)
        self._track(ctk.CTkEntry(
            frame, textvariable=self.recipients_var,
            corner_radius=RADIUS["input"], border_width=1,
        )).grid(row=2, column=0, sticky="ew", padx=PAD["lg"], pady=(0, PAD["lg"]))
