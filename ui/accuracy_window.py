"""
ui/accuracy_window.py
──────────────────────
Transparency table: shows whether each metric comes from a real hardware/OS
reading or a modeled estimate, and — for CPU/GPU — a checkbox to grant/revoke
permission to read real hardware counters. The Info column shows plain
factual detail for each row: detected CPU/TDP, GPU model, installed RAM,
network connection status, the active cost currency/rate, or the fixed
water/waste coefficient in use.

While the window is open, Status/Info/Permission for every row auto-refresh
on a timer (no manual action needed) so e.g. the Cost row picks up a
currency change made from the tray menu. Checking a CPU/GPU permission
checkbox applies immediately — granting (but not revoking) asks for
confirmation first, since it starts continuous hardware-counter reads. The
checkbox is disabled with an explanatory label when the underlying
mechanism isn't available on this platform/hardware at all (e.g. CPU
real-measurement requires Linux intel-rapl, so the checkbox is always
inert on Windows/macOS).

The "Boot backfill" row is expandable: clicking it reveals a small graph
with two visually distinct segments — a flat/dashed line for the frozen
boot-to-launch estimate, and a live Task-Manager-style scrolling strip
chart of real wattage sampled for as long as the row stays expanded. An
"Include" checkbox controls whether the frozen estimate counts toward the
totals shown elsewhere in the app. Closing the window collapses the row
and stops sampling, so reopening it always starts from a clean state
(never a frozen, no-longer-updating graph).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from collections import deque

import config
from tracker.engine import Engine

_LABELS = {
    "EN": {
        "title": "Accuracy",
        "col_metric": "Metric",
        "col_status": "Status",
        "col_permission": "Permission",
        "col_note": "Info",
        "measured": "Measured",
        "estimated": "Estimated",
        "grant": "Grant",
        "grant_cpu_unsupported": "Grant (Linux only)",
        "grant_gpu_unsupported": "Grant (needs NVIDIA + pynvml)",
        "include": "Include",
        "refresh": "Refresh",
        "close": "Close",
        "row_cpu": "CPU power",
        "row_gpu": "GPU power",
        "row_ram": "RAM power",
        "row_network": "Network",
        "row_cost": "Cost",
        "row_water": "Water",
        "row_waste": "Waste",
        "row_backfill": "Boot backfill",
        "graph_live": "Live (since opened)",
        "backfill_info": "{kwh:.3f} kWh over {dur:.1f}h — {cpu:.0f}% avg CPU measured, GPU excluded",
        "backfill_info_nocpu": "{kwh:.3f} kWh over {dur:.1f}h",
        "confirm_title": "Grant hardware read permission?",
        "confirm_cpu": (
            "EcoTracker will start reading real CPU package energy from "
            "Linux intel-rapl every second, instead of estimating it.\n\n"
            "Grant permission?"
        ),
        "confirm_gpu": (
            "EcoTracker will start reading real GPU power from NVIDIA "
            "pynvml every second, instead of estimating it.\n\n"
            "Grant permission?"
        ),
    },
    "KR": {
        "title": "정확도",
        "col_metric": "항목",
        "col_status": "상태",
        "col_permission": "권한",
        "col_note": "정보",
        "measured": "실측",
        "estimated": "추정",
        "grant": "권한 부여",
        "grant_cpu_unsupported": "권한 부여 (Linux 전용)",
        "grant_gpu_unsupported": "권한 부여 (NVIDIA+pynvml 필요)",
        "include": "포함",
        "refresh": "새로고침",
        "close": "닫기",
        "row_cpu": "CPU 전력",
        "row_gpu": "GPU 전력",
        "row_ram": "RAM 전력",
        "row_network": "네트워크",
        "row_cost": "전기 요금",
        "row_water": "수자원",
        "row_waste": "폐기물",
        "row_backfill": "부팅 후 backfill",
        "graph_live": "실시간 (연 이후)",
        "backfill_info": "{dur:.1f}시간 동안 {kwh:.3f} kWh — CPU 평균 {cpu:.0f}% 실측, GPU 제외",
        "backfill_info_nocpu": "{dur:.1f}시간 동안 {kwh:.3f} kWh",
        "confirm_title": "하드웨어 실측 권한을 부여할까요?",
        "confirm_cpu": (
            "권한을 켜면 추정 대신 Linux intel-rapl에서 실제 CPU 패키지 에너지를 "
            "매초 읽기 시작합니다.\n\n권한을 부여할까요?"
        ),
        "confirm_gpu": (
            "권한을 켜면 추정 대신 NVIDIA pynvml에서 실제 GPU 전력을 매초 읽기 "
            "시작합니다.\n\n권한을 부여할까요?"
        ),
    },
}

_ROW_ORDER = ["cpu", "gpu", "ram", "network", "cost", "water", "waste"]

_GRAPH_W = 360
_GRAPH_H = 70
_GRAPH_SPLIT = 0.35   # fraction of width reserved for the frozen backfill segment
_LIVE_MAXLEN = 60     # ~60s of live samples at 1s resolution, Task-Manager style
_AUTO_REFRESH_MS = 1000


class AccuracyWindow:
    """A singleton-style settings window. Call show() to open or focus it."""

    def __init__(self, root: tk.Tk, engine: Engine, language: str = "EN") -> None:
        self._root = root
        self._engine = engine
        self._language = language
        self._win: tk.Toplevel | None = None
        self._status_labels: dict[str, tk.Label] = {}
        self._note_labels: dict[str, tk.Label] = {}
        self._perm_vars: dict[str, tk.BooleanVar] = {}
        self._perm_checkbuttons: dict[str, tk.Checkbutton] = {}
        self._refresh_after_id: str | None = None

        # Backfill row state
        self._backfill_expanded: bool = False
        self._backfill_arrow_label: tk.Label | None = None
        self._backfill_note_label: tk.Label | None = None
        self._backfill_include_var: tk.BooleanVar | None = None
        self._backfill_detail_frame: tk.Frame | None = None
        self._backfill_canvas: tk.Canvas | None = None
        self._live_samples: deque[float] = deque(maxlen=_LIVE_MAXLEN)
        self._live_after_id: str | None = None

    def _t(self, key: str) -> str:
        return _LABELS.get(self._language, _LABELS["EN"]).get(key, key)

    def set_language(self, language: str) -> None:
        self._language = language
        if self._win is not None and self._win.winfo_exists():
            self._rebuild()

    # ── window lifecycle ─────────────────────────────────────────────────────

    def show(self) -> None:
        if self._win is not None and self._win.winfo_exists():
            self._win.deiconify()
            self._win.lift()
            self._refresh()
            self._start_auto_refresh()
            return
        self._build()

    def _build(self) -> None:
        win = tk.Toplevel(self._root)
        win.title(self._t("title"))
        win.configure(bg=config.COLOR_BG)
        win.resizable(False, False)
        win.wm_attributes("-topmost", True)
        self._win = win

        header_font = ("Segoe UI", 9, "bold")
        cell_font = ("Segoe UI", 9)

        headers = [
            self._t("col_metric"),
            self._t("col_status"),
            self._t("col_permission"),
            self._t("col_note"),
        ]
        for col, text in enumerate(headers):
            tk.Label(
                win, text=text, font=header_font,
                bg=config.COLOR_BG, fg=config.COLOR_TEXT,
                padx=8, pady=4,
            ).grid(row=0, column=col, sticky="w")

        self._status_labels.clear()
        self._note_labels.clear()
        self._perm_vars.clear()
        self._perm_checkbuttons.clear()

        row_i = 1
        for metric in _ROW_ORDER:
            tk.Label(
                win, text=self._t(f"row_{metric}"), font=cell_font,
                bg=config.COLOR_BG, fg=config.COLOR_TEXT, padx=8, pady=2, anchor="w",
            ).grid(row=row_i, column=0, sticky="w")

            status_lbl = tk.Label(win, text="…", font=cell_font,
                                   bg=config.COLOR_BG, fg=config.COLOR_DIM, padx=8, anchor="w")
            status_lbl.grid(row=row_i, column=1, sticky="w")
            self._status_labels[metric] = status_lbl

            if metric in ("cpu", "gpu"):
                var = tk.BooleanVar(value=False)
                self._perm_vars[metric] = var
                cb = tk.Checkbutton(
                    win, text=self._t("grant"), variable=var,
                    command=lambda m=metric: self._on_permission_toggle(m),
                    bg=config.COLOR_BG, fg=config.COLOR_TEXT,
                    selectcolor=config.COLOR_BG, activebackground=config.COLOR_BG,
                    disabledforeground=config.COLOR_DIM,
                    font=cell_font,
                )
                cb.grid(row=row_i, column=2, sticky="w")
                self._perm_checkbuttons[metric] = cb
            else:
                tk.Label(win, text="—", font=cell_font,
                          bg=config.COLOR_BG, fg=config.COLOR_DIM, padx=8).grid(row=row_i, column=2)

            note_lbl = tk.Label(win, text="", font=("Segoe UI", 8),
                                 bg=config.COLOR_BG, fg=config.COLOR_DIM, padx=8,
                                 anchor="w", wraplength=380, justify="left")
            note_lbl.grid(row=row_i, column=3, sticky="w")
            self._note_labels[metric] = note_lbl
            row_i += 1

        # ── Boot backfill row (expandable) ───────────────────────────────────
        backfill_row = row_i
        arrow_lbl = tk.Label(
            win, text="▸ " + self._t("row_backfill"), font=cell_font,
            bg=config.COLOR_BG, fg=config.COLOR_TEXT, padx=8, pady=2, anchor="w",
            cursor="hand2",
        )
        arrow_lbl.grid(row=backfill_row, column=0, sticky="w")
        arrow_lbl.bind("<Button-1>", lambda _e: self._toggle_backfill_expand())
        self._backfill_arrow_label = arrow_lbl

        # No Measured/Estimated label here — the row is inherently a frozen
        # estimate; the graph itself (once expanded) shows that visually.
        tk.Label(win, text="—", font=cell_font,
                 bg=config.COLOR_BG, fg=config.COLOR_DIM, padx=8, anchor="w"
                 ).grid(row=backfill_row, column=1, sticky="w")

        include_var = tk.BooleanVar(value=self._engine.include_backfill)
        self._backfill_include_var = include_var
        tk.Checkbutton(
            win, text=self._t("include"), variable=include_var,
            command=self._on_include_toggle,
            bg=config.COLOR_BG, fg=config.COLOR_TEXT,
            selectcolor=config.COLOR_BG, activebackground=config.COLOR_BG,
            font=cell_font,
        ).grid(row=backfill_row, column=2, sticky="w")

        backfill_note = tk.Label(win, text="", font=("Segoe UI", 8),
                                  bg=config.COLOR_BG, fg=config.COLOR_DIM, padx=8,
                                  anchor="w", wraplength=380, justify="left")
        backfill_note.grid(row=backfill_row, column=3, sticky="w")
        self._backfill_note_label = backfill_note
        row_i += 1

        # Expandable detail panel (graph), hidden by default
        detail_row = row_i
        detail_frame = tk.Frame(win, bg=config.COLOR_BG)
        detail_frame.grid(row=detail_row, column=0, columnspan=4, sticky="w", padx=8, pady=(0, 4))
        detail_frame.grid_remove()
        self._backfill_detail_frame = detail_frame

        canvas = tk.Canvas(detail_frame, width=_GRAPH_W, height=_GRAPH_H,
                            bg="#0b1220", highlightthickness=1, highlightbackground="#334155")
        canvas.pack()
        self._backfill_canvas = canvas
        row_i += 1

        btn_row = row_i
        btn_frame = tk.Frame(win, bg=config.COLOR_BG)
        btn_frame.grid(row=btn_row, column=0, columnspan=4, pady=8)

        refresh_btn = tk.Button(
            btn_frame, text=self._t("refresh"), command=self._refresh,
            bg="#1e293b", fg=config.COLOR_TEXT, activebackground="#334155",
            relief="flat", padx=12, pady=4,
        )
        refresh_btn.pack(side="left", padx=6)

        close_btn = tk.Button(
            btn_frame, text=self._t("close"), command=self._on_close,
            bg="#1e293b", fg=config.COLOR_TEXT, activebackground="#334155",
            relief="flat", padx=12, pady=4,
        )
        close_btn.pack(side="left", padx=6)

        win.protocol("WM_DELETE_WINDOW", self._on_close)

        self._refresh()
        self._start_auto_refresh()

    def _rebuild(self) -> None:
        self._stop_auto_refresh()
        self._collapse_backfill()
        if self._win is not None:
            self._win.destroy()
            self._win = None
        self.show()

    def _on_close(self) -> None:
        self._stop_auto_refresh()
        self._collapse_backfill()
        if self._win is not None:
            self._win.withdraw()

    # ── auto-refresh (Status/Info stay live without a manual click) ─────────

    def _start_auto_refresh(self) -> None:
        if self._refresh_after_id is not None:
            return
        self._auto_refresh_tick()

    def _stop_auto_refresh(self) -> None:
        if self._refresh_after_id is not None:
            self._root.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None

    def _auto_refresh_tick(self) -> None:
        self._refresh()
        self._refresh_after_id = self._root.after(_AUTO_REFRESH_MS, self._auto_refresh_tick)

    # ── permission checkboxes: immediate apply, confirm-on-grant ────────────

    def _on_permission_toggle(self, metric: str) -> None:
        var = self._perm_vars[metric]
        if var.get():  # just switched on -> confirm before actually granting
            body_key = "confirm_cpu" if metric == "cpu" else "confirm_gpu"
            granted = messagebox.askyesno(
                self._t("confirm_title"), self._t(body_key), parent=self._win,
            )
            if not granted:
                var.set(False)
                return
        self._engine.set_permission(metric, var.get())
        self._refresh()

    def _on_include_toggle(self) -> None:
        if self._backfill_include_var is not None:
            self._engine.set_include_backfill(self._backfill_include_var.get())
        self._refresh()

    # ── Boot backfill: expand/collapse + live graph ─────────────────────────

    def _toggle_backfill_expand(self) -> None:
        if self._backfill_expanded:
            self._collapse_backfill()
        else:
            self._backfill_expanded = True
            self._backfill_detail_frame.grid()
            self._backfill_arrow_label.config(text="▾ " + self._t("row_backfill"))
            self._live_samples.clear()
            self._start_live_sampling()

    def _collapse_backfill(self) -> None:
        """Reset the backfill row to its collapsed, non-sampling state."""
        self._backfill_expanded = False
        self._stop_live_sampling()
        if self._backfill_detail_frame is not None:
            self._backfill_detail_frame.grid_remove()
        if self._backfill_arrow_label is not None:
            self._backfill_arrow_label.config(text="▸ " + self._t("row_backfill"))

    def _start_live_sampling(self) -> None:
        if self._live_after_id is not None:
            return
        self._sample_live()

    def _stop_live_sampling(self) -> None:
        if self._live_after_id is not None:
            self._root.after_cancel(self._live_after_id)
            self._live_after_id = None

    def _sample_live(self) -> None:
        # Reads the wattage last computed by the Overlay's own tick() loop —
        # never ticks the engine itself, so this can't double-count energy.
        watts = self._engine.metrics()["watts"]
        self._live_samples.append(watts)
        self._draw_backfill_graph()
        self._live_after_id = self._root.after(1000, self._sample_live)

    def _draw_backfill_graph(self) -> None:
        canvas = self._backfill_canvas
        if canvas is None:
            return
        canvas.delete("all")
        W, H = _GRAPH_W, _GRAPH_H
        split_x = int(W * _GRAPH_SPLIT)

        report = self._engine.backfill_report()
        duration_h = report["duration_h"]
        avg_backfill_w = (report["kwh"] * 1000.0 / duration_h) if duration_h > 0 else 0.0

        live_samples = list(self._live_samples)
        max_w = max([avg_backfill_w] + live_samples + [10.0])

        def y_for(w: float) -> float:
            return H - 6 - (w / max_w) * (H - 14)

        # Frozen backfill segment: flat dashed line (dashed + dim vs. the
        # solid colored "Live" line to its right is contrast enough; no
        # caption needed here).
        y = y_for(avg_backfill_w)
        canvas.create_line(4, y, split_x - 4, y, fill=config.COLOR_DIM, width=2, dash=(4, 3))

        # Divider between the two segments
        canvas.create_line(split_x, 4, split_x, H - 4, fill="#334155", width=1)

        # Live strip chart: right-aligned, scrolls as new samples arrive
        if len(live_samples) >= 2:
            region_left = split_x + 4
            region_w = W - region_left - 4
            step = region_w / max(_LIVE_MAXLEN - 1, 1)
            start_i = _LIVE_MAXLEN - len(live_samples)
            coords = []
            for i, w in enumerate(live_samples):
                x = region_left + (start_i + i) * step
                coords.extend([x, y_for(w)])
            canvas.create_line(*coords, fill=config.COLOR_ELEC, width=2)
        canvas.create_text(W - 4, H - 3, text=self._t("graph_live"), anchor="se",
                            fill=config.COLOR_ELEC, font=("Segoe UI", 7))

    # ── data refresh ─────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._win is None or not self._win.winfo_exists():
            return
        report = {row["metric"]: row for row in self._engine.accuracy_report()}

        for metric in _ROW_ORDER:
            row = report.get(metric)
            if row is None:
                continue
            measured = row["measured"]
            status_text = self._t("measured") if measured else self._t("estimated")
            status_color = "#4ade80" if measured else config.COLOR_DIM
            self._status_labels[metric].config(text=status_text, fg=status_color)
            self._note_labels[metric].config(text=row["reason"])

            if metric in self._perm_vars:
                self._perm_vars[metric].set(row["permission_granted"])
                cb = self._perm_checkbuttons[metric]
                if row["permission_supported"]:
                    cb.config(state="normal", text=self._t("grant"))
                else:
                    cb.config(state="disabled", text=self._t(f"grant_{metric}_unsupported"))

        backfill = self._engine.backfill_report()
        if self._backfill_note_label is not None:
            if backfill["cpu_busy_pct"] is not None:
                text = self._t("backfill_info").format(
                    kwh=backfill["kwh"], dur=backfill["duration_h"], cpu=backfill["cpu_busy_pct"],
                )
            else:
                text = self._t("backfill_info_nocpu").format(
                    kwh=backfill["kwh"], dur=backfill["duration_h"],
                )
            self._backfill_note_label.config(text=text)
        if self._backfill_include_var is not None:
            self._backfill_include_var.set(backfill["include"])
        if self._backfill_expanded:
            self._draw_backfill_graph()
