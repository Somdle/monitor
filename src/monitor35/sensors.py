"""System sampling, counter baselines and bounded time history; used only by the worker."""

import logging
import time
from collections import deque
from dataclasses import dataclass, replace

import psutil

from monitor35.cpu_temperature import CpuTemperature
from monitor35.gpu import GpuSample, NvidiaSampler

logger = logging.getLogger(__name__)
HISTORY_SECONDS = 60


@dataclass(frozen=True)
class Point:
    at: float
    cpu: float
    memory: float
    read: float | None
    write: float | None
    receive: float | None
    send: float | None
    gpu: float | None = None


@dataclass(frozen=True)
class Telemetry:
    at: float = 0
    cpu: float | None = None
    memory_percent: float | None = None
    memory_used: int = 0
    memory_total: int = 0
    cpu_temperature: float | None = None
    gpu: GpuSample = GpuSample()
    read: float | None = None
    write: float | None = None
    receive: float | None = None
    send: float | None = None
    received_total: int = 0
    sent_total: int = 0
    interface: str = ""
    interfaces: tuple[str, ...] = ()
    history: tuple[Point, ...] = ()
    warnings: tuple[str, ...] = ()


class Sampler:
    def __init__(self):
        self.previous_at: float | None = None
        self.disk_previous: dict[str, tuple[int, int]] = {}
        self.net_previous: tuple[int, int] | None = None
        self.interface = ""
        self.received_total = self.sent_total = 0
        self.history: deque[Point] = deque(maxlen=120)
        self.previous_warnings: tuple[str, ...] = ()
        self.gpu = NvidiaSampler()
        psutil.cpu_percent()
        self.cpu_temperature = CpuTemperature()

    def sample(self, requested_interface: str = "") -> Telemetry:
        now = time.monotonic()
        elapsed = now - self.previous_at if self.previous_at is not None else 0
        valid_interval = 0 < elapsed <= 5
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        warnings = []
        gpu = self.gpu.sample(now)
        if gpu.warning:
            warnings.append(gpu.warning)
        cpu_temperature, cpu_warning = self.cpu_temperature.sample()
        if cpu_warning:
            warnings.append(cpu_warning)
        try:
            disks = psutil.disk_io_counters(perdisk=True, nowrap=False) or {}
        except OSError:
            disks = {}  # The unavailable counter warning below is published to the UI.
        disk_current = {
            name: (value.read_bytes, value.write_bytes) for name, value in disks.items()
        }
        read = write = None
        if disks and valid_interval and disk_current.keys() == self.disk_previous.keys():
            deltas = [
                (value[0] - self.disk_previous[name][0], value[1] - self.disk_previous[name][1])
                for name, value in disk_current.items()
            ]
            if all(r >= 0 and w >= 0 for r, w in deltas):
                read = sum(r for r, _ in deltas) / elapsed
                write = sum(w for _, w in deltas) / elapsed
        if not disks:
            warnings.append("디스크 I/O 계수를 사용할 수 없습니다.")
        self.disk_previous = disk_current
        interfaces = psutil.net_io_counters(pernic=True, nowrap=False)
        stats = psutil.net_if_stats()
        active = {
            name: value
            for name, value in interfaces.items()
            if name in stats and stats[name].isup and "loopback" not in name.lower()
        }
        selected = requested_interface
        if not selected:
            if self.interface in active:
                selected = self.interface
            elif active:
                selected = max(
                    active, key=lambda name: active[name].bytes_recv + active[name].bytes_sent
                )
        changed = selected != self.interface
        if changed:
            self.net_previous = None
            self.received_total = self.sent_total = 0
            self.history = deque(
                (replace(point, receive=None, send=None) for point in self.history), maxlen=120
            )
        self.interface = selected
        receive = send = None
        counter = active.get(selected)
        if counter is not None:
            current = (counter.bytes_recv, counter.bytes_sent)
            if valid_interval and self.net_previous is not None:
                rx, tx = current[0] - self.net_previous[0], current[1] - self.net_previous[1]
                if rx >= 0 and tx >= 0:
                    receive, send = rx / elapsed, tx / elapsed
                    self.received_total += rx
                    self.sent_total += tx
            self.net_previous = current
        else:
            self.net_previous = None
            warnings.append(
                "선택한 네트워크 연결이 끊겼습니다." if selected else "활성 네트워크가 없습니다."
            )
        # A resume/stalled sampling interval must not invent rates or bridge the graph.
        if elapsed > 5 or elapsed < 0:
            self.history.clear()
        self.previous_at = now
        self.history.append(
            Point(now, cpu, memory.percent, read, write, receive, send, gpu.percent)
        )
        while self.history and self.history[0].at < now - HISTORY_SECONDS:
            self.history.popleft()
        warning_tuple = tuple(warnings)
        if warning_tuple != self.previous_warnings:
            logger.warning("sensor_availability_changed", extra={"warnings": warning_tuple})
            self.previous_warnings = warning_tuple
        return Telemetry(
            at=now,
            cpu=cpu,
            memory_percent=memory.percent,
            memory_used=memory.total - memory.available,
            memory_total=memory.total,
            cpu_temperature=cpu_temperature,
            gpu=gpu,
            read=read,
            write=write,
            receive=receive,
            send=send,
            received_total=self.received_total,
            sent_total=self.sent_total,
            interface=selected,
            interfaces=tuple(sorted(active)),
            history=tuple(self.history),
            warnings=warning_tuple,
        )

    def close(self):
        self.cpu_temperature.close()
