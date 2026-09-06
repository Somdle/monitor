"""Desktop preview and layout editor. The worker exclusively owns serial access."""

import logging
import queue
import tkinter as tk
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, ttk

from PIL import ImageTk

from monitor35.power import PowerListener
from monitor35.render import render
from monitor35.runtime import MonitorWorker
from monitor35.sensors import Telemetry
from monitor35.theme import CARD_HEIGHT, CARD_WIDTH, HEIGHT, WIDTH, Theme, load_theme, save_theme

logger = logging.getLogger(__name__)
NAMES = {"cpu": "CPU", "memory": "메모리", "disk": "디스크", "network": "네트워크"}


class MonitorApp:
    def __init__(self, root: tk.Tk, theme: Theme, theme_path: Path, connect: bool = False):
        self.root, self.theme, self.theme_path = root, theme, theme_path
        self.saved_theme = theme
        self.history: list[Theme] = []
        self.selected = 0
        self.values = Telemetry()
        self.drag_origin: tuple[int, int] | None = None
        self.drag_theme = theme
        self.closing = False
        self.last_state = "미리보기"
        self.worker = MonitorWorker(theme)
        root.title("Monitor35 · 화면 편집")
        root.geometry("980x820")
        root.minsize(900, 800)
        root.configure(bg="#eef2f6")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2f6")
        style.configure("TLabel", background="#eef2f6", font=("맑은 고딕", 10))
        style.configure("TButton", padding=(12, 8), font=("맑은 고딕", 10))
        style.configure("Title.TLabel", font=("맑은 고딕", 22, "bold"))
        shell = ttk.Frame(root, padding=26)
        shell.pack(fill="both", expand=True)
        header = ttk.Frame(shell)
        header.pack(fill="x")
        ttk.Label(header, text="Monitor35", style="Title.TLabel").pack(side="left")
        self.connect_button = ttk.Button(header, text="화면 연결", command=self.toggle_connection)
        self.connect_button.pack(side="right")
        self.reconnect_button = ttk.Button(
            header, text="다시 연결", command=self.reconnect, state="disabled"
        )
        self.reconnect_button.pack(side="right", padx=8)
        ttk.Label(
            shell, text="3.5인치 화면 · 항목을 드래그하거나 오른쪽에서 위치를 조절하세요."
        ).pack(anchor="w", pady=(6, 22))
        content = ttk.Frame(shell)
        content.pack(fill="both", expand=True)
        preview = ttk.Frame(content)
        preview.pack(side="left", anchor="n")
        ttk.Label(preview, text="화면 미리보기  /  480 × 320").pack(anchor="w", pady=(0, 10))
        self.canvas = tk.Canvas(
            preview, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="#101923", takefocus=True
        )
        self.canvas.pack()
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")
        self.outline = self.canvas.create_rectangle(0, 0, 0, 0, outline="#ffffff", dash=(4, 3))
        self.canvas.bind("<ButtonPress-1>", self.begin_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        ttk.Label(
            preview,
            text="연결 후 편집 내용이 실제 화면에도 반영됩니다.\n"
            "차트: 최근 60초 · 디스크 용량: 2개씩 6초 순환\n"
            "네트워크 누적: 앱/어댑터 시작 이후 측정분 (절전 제외)",
        ).pack(anchor="w", pady=12)
        volume_table = ttk.Frame(preview)
        volume_table.pack(fill="x")
        self.volumes = ttk.Treeview(
            volume_table, columns=("drive", "used", "total"), show="headings", height=4
        )
        for key, label, width in (
            ("drive", "볼륨", 100),
            ("used", "사용 (GiB)", 170),
            ("total", "전체 (GiB)", 170),
        ):
            self.volumes.heading(key, text=label)
            self.volumes.column(key, width=width, stretch=True)
        volume_scroll = ttk.Scrollbar(volume_table, orient="vertical", command=self.volumes.yview)
        self.volumes.configure(yscrollcommand=volume_scroll.set)
        volume_scroll.pack(side="right", fill="y")
        self.volumes.pack(side="left", fill="both", expand=True)
        panel = ttk.Frame(content, padding=(24, 0, 0, 0))
        panel.pack(side="left", fill="both", expand=True)
        ttk.Label(panel, text="선택 항목").pack(anchor="w")
        self.selection = ttk.Combobox(
            panel, values=[NAMES[w.metric] for w in theme.widgets], state="readonly"
        )
        self.selection.pack(fill="x", pady=(5, 12))
        self.selection.current(0)
        self.selection.bind("<<ComboboxSelected>>", self.select)
        self.fields: dict[str, tk.StringVar] = {}
        for key, label, maximum in (
            ("x", "가로 위치", WIDTH - CARD_WIDTH),
            ("y", "세로 위치", HEIGHT - CARD_HEIGHT),
            ("size", "사용률 글자 크기", 28),
        ):
            row = ttk.Frame(panel)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label).pack(side="left")
            value = tk.StringVar()
            self.fields[key] = value
            spinbox = ttk.Spinbox(
                row, from_=16 if key == "size" else 0, to=maximum, textvariable=value, width=9
            )
            spinbox.pack(side="right")
            if key == "size":
                self.size_input = spinbox
        ttk.Button(panel, text="위치 · 크기 적용", command=self.apply_fields).pack(fill="x", pady=8)
        ttk.Button(panel, text="차트 색상 선택", command=self.choose_color).pack(fill="x")
        ttk.Label(panel, text="네트워크 어댑터").pack(anchor="w", pady=(12, 4))
        self.network = ttk.Combobox(panel, state="readonly")
        self.network.pack(fill="x")
        self.network.bind("<<ComboboxSelected>>", self.apply_network)
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=(16, 5))
        ttk.Label(row, text="화면 밝기 (0~50)").pack(side="left")
        self.brightness = tk.StringVar(value=str(theme.brightness))
        ttk.Spinbox(row, from_=0, to=50, textvariable=self.brightness, width=6).pack(side="right")
        ttk.Button(panel, text="밝기 적용", command=self.apply_brightness).pack(fill="x")
        self.rotation = tk.BooleanVar(value=theme.rotate_180)
        self.rotation_button = ttk.Checkbutton(
            panel, text="실제 화면 180° 회전", variable=self.rotation, command=self.apply_rotation
        )
        self.rotation_button.pack(anchor="w", pady=(10, 0))
        self.reset = tk.BooleanVar(value=theme.reset_on_connect)
        ttk.Checkbutton(
            panel, text="재연결 시 장치 초기화", variable=self.reset, command=self.apply_reset
        ).pack(anchor="w", pady=10)
        actions = ttk.Frame(shell)
        actions.pack(fill="x", pady=(12, 8))
        ttk.Button(actions, text="테마 저장", command=self.save).pack(side="left")
        self.undo_button = ttk.Button(
            actions, text="실행 취소", command=self.undo, state="disabled"
        )
        self.undo_button.pack(side="left", padx=8)
        ttk.Button(actions, text="저장본 불러오기", command=self.reload).pack(side="left")
        self.notice = tk.StringVar(value="미리보기 준비 완료. 기존 UsbMonitor 종료 후 연결하세요.")
        ttk.Label(shell, textvariable=self.notice, wraplength=880).pack(anchor="w", pady=5)
        self.status = tk.StringVar(value="센서 준비 중…")
        ttk.Label(shell, textvariable=self.status, wraplength=880).pack(anchor="w")
        self.load_fields()
        self.draw()
        root.update_idletasks()
        root.report_callback_exception = self.callback_error
        self.power = PowerListener(
            root.winfo_id(), self.worker.request_suspend, self.worker.request_resume
        )
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Control-s>", lambda _: self.save())
        root.bind("<Control-z>", lambda _: self.undo())
        if connect:
            self.toggle_connection()
        self.worker.start()
        root.after(100, self.poll)

    def callback_error(self, error_type, value, traceback):
        logger.error("ui_action_failed", exc_info=(error_type, value, traceback))
        self.notice.set(f"작업 실패 · 입력을 확인하고 다시 시도해 주세요: {value}")

    def load_fields(self):
        widget = self.theme.widgets[self.selected]
        for key, value in self.fields.items():
            value.set(str(getattr(widget, key)))
        self.brightness.set(str(self.theme.brightness))
        self.reset.set(self.theme.reset_on_connect)
        self.rotation.set(self.theme.rotate_180)
        self.size_input.configure(
            state="normal" if widget.metric in ("cpu", "memory") else "disabled"
        )
        self.selection.configure(values=[NAMES[w.metric] for w in self.theme.widgets])
        interfaces = tuple(dict.fromkeys((self.theme.network_interface,) + self.values.interfaces))
        self.network.configure(values=["자동 선택"] + [name for name in interfaces if name])
        self.network.set(self.theme.network_interface or "자동 선택")

    def draw(self):
        self.photo = ImageTk.PhotoImage(render(self.theme, self.values))
        self.canvas.itemconfigure(self.image_id, image=self.photo)
        widget = self.theme.widgets[self.selected]
        x0, y0 = widget.x, widget.y
        x1, y1 = widget.x + CARD_WIDTH - 1, widget.y + CARD_HEIGHT - 1
        self.canvas.coords(self.outline, x0, y0, x1, y1)

    def changed(self, theme: Theme, remember: bool = True):
        if theme == self.theme:
            return
        if remember:
            self.history = (self.history + [self.theme])[-100:]
        self.theme = theme
        self.worker.set_theme(theme)
        self.undo_button.configure(state="normal" if self.history else "disabled")
        self.notice.set("변경됨 · 저장하면 다음 실행에도 유지됩니다.")
        self.load_fields()
        self.draw()

    def select(self, _event=None):
        self.selected = self.selection.current()
        self.load_fields()
        self.draw()

    def begin_drag(self, event):
        self.canvas.focus_set()
        x, y = event.x, event.y
        for index in reversed(range(len(self.theme.widgets))):
            widget = self.theme.widgets[index]
            if widget.x <= x < widget.x + CARD_WIDTH and widget.y <= y < widget.y + CARD_HEIGHT:
                self.selected = index
                self.selection.current(index)
                self.drag_origin = (x - widget.x, y - widget.y)
                self.drag_theme = self.theme
                self.load_fields()
                self.draw()
                break

    def drag(self, event):
        if self.drag_origin is None:
            return
        widgets = list(self.theme.widgets)
        x, y = event.x, event.y
        widgets[self.selected] = replace(
            widgets[self.selected],
            x=max(0, min(WIDTH - CARD_WIDTH, x - self.drag_origin[0])),
            y=max(0, min(HEIGHT - CARD_HEIGHT, y - self.drag_origin[1])),
        )
        self.changed(replace(self.theme, widgets=tuple(widgets)), remember=False)

    def end_drag(self, _event):
        if self.drag_origin is not None and self.drag_theme != self.theme:
            self.history = (self.history + [self.drag_theme])[-100:]
            self.undo_button.configure(state="normal")
        self.drag_origin = None

    def apply_fields(self):
        try:
            widgets = list(self.theme.widgets)
            widgets[self.selected] = replace(
                widgets[self.selected],
                x=int(self.fields["x"].get()),
                y=int(self.fields["y"].get()),
                size=int(self.fields["size"].get()),
            )
            self.changed(replace(self.theme, widgets=tuple(widgets)))
        except ValueError as exc:
            self.notice.set(f"입력을 확인해 주세요: {exc}")

    def choose_color(self):
        color = colorchooser.askcolor(
            self.theme.widgets[self.selected].color, title="글자 색상", parent=self.root
        )[1]
        if color:
            widgets = list(self.theme.widgets)
            widgets[self.selected] = replace(widgets[self.selected], color=color)
            self.changed(replace(self.theme, widgets=tuple(widgets)))

    def apply_brightness(self):
        try:
            self.changed(replace(self.theme, brightness=int(self.brightness.get())))
        except ValueError as exc:
            self.notice.set(f"밝기를 확인해 주세요: {exc}")

    def apply_reset(self):
        self.changed(replace(self.theme, reset_on_connect=self.reset.get()))

    def apply_rotation(self):
        self.changed(replace(self.theme, rotate_180=self.rotation.get()))

    def apply_network(self, _event=None):
        name = self.network.get()
        self.changed(replace(self.theme, network_interface="" if name == "자동 선택" else name))

    def save(self) -> bool:
        try:
            save_theme(self.theme_path, self.theme)
            self.saved_theme = self.theme
            self.notice.set(f"저장 완료 · {self.theme_path.name}")
            return True
        except (OSError, ValueError) as exc:
            logger.exception("theme_save_failed")
            self.notice.set(f"저장 실패 · 경로와 권한을 확인해 주세요: {exc}")
            return False

    def reload(self):
        try:
            theme = load_theme(self.theme_path)
            self.changed(theme)
            self.saved_theme = theme
            self.notice.set("저장본을 불러왔습니다. 실행 취소로 이전 편집을 복원할 수 있습니다.")
        except (OSError, ValueError) as exc:
            self.notice.set(f"불러오기 실패 · 파일을 확인해 주세요: {exc}")

    def undo(self):
        if self.history:
            self.changed(self.history.pop(), remember=False)
            self.notice.set("이전 편집으로 되돌렸습니다.")

    def toggle_connection(self):
        if self.worker.enabled.is_set():
            self.worker.enabled.clear()
            self.connect_button.configure(text="화면 연결")
            self.reconnect_button.configure(state="disabled")
            self.notice.set("전송 중지 요청됨 · 현재 전송이 끝나면 포트를 닫습니다.")
        else:
            self.worker.request_reconnect()
            self.worker.enabled.set()
            self.connect_button.configure(text="연결 해제")
            self.reconnect_button.configure(state="normal")
            self.notice.set("장치 연결 중… 초기화에 수 초 걸릴 수 있습니다.")

    def reconnect(self):
        self.worker.request_reconnect()
        self.notice.set("재연결 요청됨 · 장치를 다시 찾아 화면 전체를 보냅니다.")

    def poll(self):
        if self.closing:
            return
        try:
            snapshot = self.worker.snapshots.get_nowait()
        except queue.Empty:
            snapshot = None
        if snapshot:
            interfaces_changed = self.values.interfaces != snapshot.values.interfaces
            self.values = snapshot.values
            if interfaces_changed:
                interfaces = tuple(
                    dict.fromkeys((self.theme.network_interface,) + self.values.interfaces)
                )
                self.network.configure(values=["자동 선택"] + [name for name in interfaces if name])
            previous_view = self.volumes.yview()
            self.volumes.delete(*self.volumes.get_children())
            for volume in self.values.volumes:
                self.volumes.insert(
                    "",
                    "end",
                    values=(
                        volume.name,
                        f"{volume.used / 1024**3:.1f}" if volume.used is not None else "읽기 실패",
                        f"{volume.total / 1024**3:.1f}" if volume.total is not None else "--",
                    ),
                )
            self.volumes.yview_moveto(previous_view[0])
            status = snapshot.status
            if status.state != self.last_state:
                if status.state == "전송 중":
                    self.notice.set("장치 연결 완료 · 편집 내용이 실제 화면에 반영됩니다.")
                elif status.state == "재연결 대기":
                    self.notice.set(
                        "연결이 끊겼습니다. 장치와 포트 점유를 확인하세요. 자동 재시도 중입니다."
                    )
                elif status.state == "미리보기":
                    self.notice.set("연결 해제 완료 · 미리보기 편집을 계속할 수 있습니다.")
                self.last_state = status.state
            if status.state != "오류":
                self.draw()
            sent = (
                datetime.fromtimestamp(status.last_sent).strftime("%H:%M:%S")
                if (status.last_sent is not None)
                else "없음"
            )
            self.status.set(
                f"{status.state} · 전송 {status.frames} · 연결 {status.connections} · "
                f"실패 {status.failures} · 최근 전송 {sent}\n{status.detail} "
                + " ".join(self.values.warnings)
            )
            if status.state == "오류":
                self.connect_button.configure(state="disabled")
                self.reconnect_button.configure(state="disabled")
                self.notice.set("작업이 중지됐습니다. 로그를 확인하고 앱을 다시 실행해 주세요.")
        self.root.after(100, self.poll)

    def close(self):
        if self.theme != self.saved_theme and not self.save():
            return
        self.closing = True
        self.worker.request_stop()
        self.notice.set("화면 전송을 마치고 종료 중…")
        self.connect_button.configure(state="disabled")
        self.reconnect_button.configure(state="disabled")
        self.finish_close()

    def finish_close(self):
        if self.worker.is_alive():
            self.root.after(100, self.finish_close)
        else:
            self.power.close()
            self.root.destroy()
