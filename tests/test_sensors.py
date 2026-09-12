import subprocess
from types import SimpleNamespace as NS

import pytest

from monitor35.sensors import Sampler


@pytest.fixture
def system(monkeypatch):
    def missing_driver(*args):
        raise FileNotFoundError("PawnIO unavailable in test")

    monkeypatch.setattr("winreg.OpenKey", missing_driver)
    monkeypatch.setattr("shutil.which", lambda _: "nvidia-smi.exe")
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: NS(stdout="RTX, 60, 62"))
    state = NS(
        at=100.0,
        disks={"PhysicalDrive0": NS(read_bytes=1000, write_bytes=2000)},
        network={"Ethernet": NS(bytes_recv=10000, bytes_sent=20000)},
    )
    monkeypatch.setattr("monitor35.sensors.time.monotonic", lambda: state.at)
    monkeypatch.setattr("psutil.cpu_percent", lambda: 42.0)
    monkeypatch.setattr(
        "psutil.virtual_memory",
        lambda: NS(total=32 * 1024**3, available=12 * 1024**3, percent=62.5),
    )
    monkeypatch.setattr("psutil.disk_io_counters", lambda **kwargs: state.disks)
    monkeypatch.setattr("psutil.net_io_counters", lambda **kwargs: state.network)
    monkeypatch.setattr(
        "psutil.net_if_stats", lambda: {name: NS(isup=True) for name in state.network}
    )
    return state


def test_memory_capacity_and_elapsed_rates(system):
    system.disks["PhysicalDrive1"] = NS(read_bytes=2000, write_bytes=3000)
    system.network["Wi-Fi"] = NS(bytes_recv=30000, bytes_sent=40000)
    sampler = Sampler()
    first = sampler.sample()
    assert (first.memory_used, first.memory_total) == (20 * 1024**3, 32 * 1024**3)
    assert first.gpu.percent == first.history[-1].gpu == 60
    assert first.receive is None and first.read is None
    system.at += 2
    system.disks["PhysicalDrive1"].read_bytes += 4096
    system.disks["PhysicalDrive1"].write_bytes += 2048
    system.disks["PhysicalDrive0"].read_bytes += 2048
    system.disks["PhysicalDrive0"].write_bytes += 4096
    system.network["Ethernet"].bytes_recv += 6000
    system.network["Ethernet"].bytes_sent += 1000
    system.network["Wi-Fi"].bytes_recv += 2000
    system.network["Wi-Fi"].bytes_sent += 3000
    next_sample = sampler.sample()
    assert next_sample.interface == "Ethernet + Wi-Fi"
    assert (next_sample.read, next_sample.write) == (3072, 3072)
    assert (next_sample.receive, next_sample.send) == (4000, 2000)
    assert (next_sample.received_total, next_sample.sent_total) == (8000, 4000)
    point = next_sample.history[-1]
    assert (point.read, point.write, point.receive, point.send) == (3072, 3072, 4000, 2000)
    assert next_sample.minute_bytes("read") == 6144
    assert next_sample.minute_bytes("write") == 6144
    assert next_sample.minute_bytes("receive") == 8000
    assert next_sample.minute_bytes("send") == 4000
    assert len(first.history) == 1  # Previously published snapshots stay immutable.


def test_resume_and_counter_reset_do_not_invent_spikes(system):
    sampler = Sampler()
    sampler.sample()
    system.at += 30
    system.network["Ethernet"].bytes_recv += 10**9
    resumed = sampler.sample()
    assert resumed.receive is None and resumed.read is None
    assert resumed.received_total == 0
    assert len(resumed.history) == 1
    assert resumed.minute_bytes("receive") is None
    system.at += 1
    system.network["Ethernet"].bytes_recv = 0
    system.disks["PhysicalDrive0"].read_bytes = 0
    reset = sampler.sample()
    assert reset.receive is None and reset.read is None
    system.at += 1
    system.network["Ethernet"].bytes_recv = 1024
    assert sampler.sample().receive == 1024


def test_disk_hotplug_and_adapter_selection(system):
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    system.network["Wi-Fi"] = NS(bytes_recv=10**10, bytes_sent=100)
    system.disks["PhysicalDrive1"] = NS(read_bytes=10**12, write_bytes=0)
    sample = sampler.sample()
    assert sample.interface == "Ethernet + Wi-Fi"
    assert sample.read is None and sample.receive is None
    assert sample.received_total == 0
    system.at += 1
    switched = sampler.sample("Wi-Fi")
    assert switched.interface == "Wi-Fi"
    assert switched.receive is None and switched.received_total == 0
    assert switched.minute_bytes("receive") is None
    system.at += 1
    system.network["Ethernet"].bytes_recv += 9999
    system.network["Wi-Fi"].bytes_recv += 300
    assert sampler.sample("Wi-Fi").receive == 300
    del system.network["Wi-Fi"]
    system.at += 1
    offline = sampler.sample("Wi-Fi")
    assert offline.interface == "Wi-Fi" and offline.receive is None
    assert offline.warnings


def test_aggregate_adapter_changes_rebaseline_and_preserve_measured_usage(system):
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    system.network["Ethernet"].bytes_recv += 100
    assert sampler.sample().received_total == 100
    system.at += 1
    system.network["Wi-Fi"] = NS(bytes_recv=10**10, bytes_sent=10**10)
    added = sampler.sample()
    assert added.receive is None and added.send is None
    assert added.received_total == added.minute_bytes("receive") == 100
    system.at += 2
    system.network["Ethernet"].bytes_recv += 200
    system.network["Wi-Fi"].bytes_recv += 400
    combined = sampler.sample()
    assert combined.receive == 300
    assert combined.received_total == combined.minute_bytes("receive") == 700
    system.at += 1
    del system.network["Wi-Fi"]
    removed = sampler.sample()
    assert removed.receive is None
    assert removed.received_total == 700
    system.at += 1
    system.network["Ethernet"].bytes_recv += 50
    assert sampler.sample().receive == 50


def test_individual_counter_reset_is_not_hidden_by_other_devices(system):
    system.network["Wi-Fi"] = NS(bytes_recv=100, bytes_sent=100)
    system.disks["PhysicalDrive1"] = NS(read_bytes=100, write_bytes=100)
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    system.network["Wi-Fi"].bytes_recv = 0
    system.network["Ethernet"].bytes_recv += 1000
    system.disks["PhysicalDrive1"].write_bytes = 0
    system.disks["PhysicalDrive0"].write_bytes += 1000
    reset = sampler.sample()
    assert reset.receive is None and reset.read is None
    assert reset.received_total == 0
    system.at += 1
    system.network["Wi-Fi"].bytes_recv += 60
    system.network["Ethernet"].bytes_recv += 40
    assert sampler.sample().receive == 100


def test_aggregation_excludes_down_and_loopback_adapters(system, monkeypatch):
    system.network["Wi-Fi"] = NS(bytes_recv=100, bytes_sent=100)
    system.network["Loopback Pseudo-Interface 1"] = NS(bytes_recv=100, bytes_sent=100)
    monkeypatch.setattr(
        "psutil.net_if_stats",
        lambda: {name: NS(isup=name != "Wi-Fi") for name in system.network},
    )
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    for counter in system.network.values():
        counter.bytes_recv += 100
    sample = sampler.sample()
    assert sample.interfaces == ("Ethernet",)
    assert sample.receive == 100
    system.at += 1
    system.network.clear()
    offline = sampler.sample()
    assert offline.receive is None and offline.send is None
    assert offline.interface == "" and offline.warnings


def test_time_history_is_bounded_to_last_minute(system):
    sampler = Sampler()
    for _ in range(200):
        sample = sampler.sample()
        system.at += 1
    assert len(sample.history) == 61
    assert sample.history[-1].at - sample.history[0].at == 60


def test_unavailable_disk_counters_leave_other_sensors_running(system, monkeypatch):
    def unavailable(**kwargs):
        raise OSError("disk counters unavailable")

    monkeypatch.setattr("psutil.disk_io_counters", unavailable)
    sample = Sampler().sample()
    assert sample.read is None and sample.write is None
    assert sample.cpu == 42
    assert sample.warnings


def test_gpu_timeout_does_not_stop_other_sampling(system, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 0.7)

    monkeypatch.setattr("subprocess.run", timeout)
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    sample = sampler.sample()
    assert sample.gpu.percent is None and sample.warnings
    assert sample.cpu == 42 and sample.memory_used == 20 * 1024**3
    assert sample.read == sample.write == sample.receive == sample.send == 0
