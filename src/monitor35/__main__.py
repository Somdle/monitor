import argparse
import io
import json
import logging
import queue
import sys
import time
from dataclasses import asdict
from pathlib import Path

from monitor35.device import devices
from monitor35.instance import SingleInstance
from monitor35.logging_setup import configure
from monitor35.runtime import MonitorWorker
from monitor35.theme import default_theme, load_theme


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Turing 3.5 모니터 · 기본 실행은 미리보기")
    parser.add_argument("--devices", action="store_true", help="지원 장치 목록만 출력")
    parser.add_argument("--connect", action="store_true", help="시작 시 실기기 연결")
    parser.add_argument(
        "--background", action="store_true", help="트레이로 시작 (연결은 --connect)"
    )
    parser.add_argument("--smoke", type=int, metavar="SECONDS", help="UI 없이 지정 시간 실행")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    if args.devices:
        print(json.dumps(devices(), ensure_ascii=False, indent=2))
        return 0
    if args.smoke is not None and args.smoke < 1:
        parser.error("--smoke는 1초 이상이어야 합니다.")
    theme_path = args.data_dir / "theme.json"
    instance = None
    try:
        if args.smoke is None or args.connect:
            instance = SingleInstance()
            if not instance.owner:
                return 0
        configure(args.data_dir / "monitor.jsonl")
        theme = load_theme(theme_path) if theme_path.exists() else default_theme()
        if args.smoke is not None:
            worker = MonitorWorker(theme)
            if args.connect:
                worker.enabled.set()
            worker.start()
            deadline = time.monotonic() + args.smoke
            last = None
            failed = False
            try:
                while time.monotonic() < deadline:
                    try:
                        last = worker.snapshots.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    print(json.dumps(asdict(last.status), ensure_ascii=False), flush=True)
                    failed = failed or last.status.state == "오류"
            finally:
                worker.request_stop()
                worker.join(timeout=8)
            if worker.is_alive() or last is None or failed:
                return 1
            last.image.save(args.data_dir / "preview.png")
            return int(args.connect and last.status.state != "전송 중")
        import tkinter as tk

        from monitor35.app import MonitorApp

        root = tk.Tk()
        MonitorApp(root, theme, theme_path, args.connect, args.background, instance)
        root.mainloop()
        return 0
    except (OSError, ValueError) as exc:
        logging.exception("startup_failed")
        if sys.stderr is not None:
            print(f"시작 실패: {exc}", file=sys.stderr)
        else:
            from tkinter import messagebox

            messagebox.showerror("Monitor35 시작 실패", f"설정과 로그를 확인해 주세요.\n{exc}")
        return 1
    finally:
        if instance is not None:
            instance.close()


if __name__ == "__main__":
    raise SystemExit(main())
