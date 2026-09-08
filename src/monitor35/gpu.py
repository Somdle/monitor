"""Bounded, read-only NVIDIA driver query. No GPU settings or driver installation."""

import csv
import math
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GpuSample:
    name: str = ""
    percent: float | None = None
    temperature: float | None = None
    warning: str = ""


class NvidiaSampler:
    def __init__(self):
        self.executable = shutil.which("nvidia-smi")
        self.retry_at = 0.0
        self.latest = GpuSample(warning="NVIDIA 센서 도구를 찾을 수 없습니다.")

    def sample(self, now: float) -> GpuSample:
        if now < self.retry_at:
            return self.latest
        if self.executable is None:
            self.executable = shutil.which("nvidia-smi")
        if self.executable is None:
            self.retry_at = now + 15
            return self.latest
        try:
            result = subprocess.run(
                [
                    self.executable,
                    "--id=0",
                    "--query-gpu=name,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=0.7,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            rows = list(csv.reader(result.stdout.strip().splitlines()))
            if len(rows) != 1 or len(rows[0]) != 3:
                raise ValueError("Unexpected NVIDIA sensor response")
            name, *raw = (field.strip() for field in rows[0])
            numbers: list[float | None] = []
            for field in raw:
                if field in {"N/A", "[N/A]", "[Not Supported]", "Not Supported"}:
                    numbers.append(None)
                else:
                    value = float(field)
                    if not math.isfinite(value) or value < 0:
                        raise ValueError("Invalid NVIDIA sensor number")
                    numbers.append(value)
            if numbers[0] is not None and numbers[0] > 100:
                raise ValueError("Invalid GPU utilization")
            self.latest = GpuSample(name, numbers[0], numbers[1])
            self.retry_at = now + 1
        except (OSError, subprocess.SubprocessError, ValueError):
            self.latest = GpuSample(warning="GPU 센서 조회 실패 · 15초 후 재시도합니다.")
            self.retry_at = now + 15
        return self.latest
