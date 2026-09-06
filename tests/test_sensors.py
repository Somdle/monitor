from types import SimpleNamespace as NS

import pytest

from monitor35.sensors import Sampler


@pytest.fixture
def system(monkeypatch):
    state = NS(
        at=100.0,
        disks={"PhysicalDrive0": NS(read_bytes=1000, write_bytes=2000)},
        network={"Ethernet": NS(bytes_recv=10000, bytes_sent=20000)},
        parts=[
            NS(mountpoint="C:\\", fstype="NTFS", opts="rw,fixed"),
            NS(mountpoint="D:\\", fstype="NTFS", opts="rw,fixed"),
        ],
        unavailable=set(),
    )
    monkeypatch.setattr("monitor35.sensors.time.monotonic", lambda: state.at)
    monkeypatch.setattr("psutil.cpu_percent", lambda: 42.0)
    monkeypatch.setattr(
        "psutil.virtual_memory",
        lambda: NS(total=32 * 1024**3, available=12 * 1024**3, percent=62.5),
    )
    monkeypatch.setattr("psutil.disk_partitions", lambda: state.parts)

    def usage(path):
        if path in state.unavailable:
            raise OSError("volume disconnected")
        return NS(used=100 * 1024**3, total=500 * 1024**3)

    monkeypatch.setattr("psutil.disk_usage", usage)
    monkeypatch.setattr("psutil.disk_io_counters", lambda **kwargs: state.disks)
    monkeypatch.setattr("psutil.net_io_counters", lambda **kwargs: state.network)
    monkeypatch.setattr(
        "psutil.net_if_stats", lambda: {name: NS(isup=True) for name in state.network}
    )
    return state


def test_all_volumes_memory_capacity_and_elapsed_rates(system):
    sampler = Sampler()
    first = sampler.sample()
    assert [volume.name for volume in first.volumes] == ["C:", "D:"]
    assert (first.memory_used, first.memory_total) == (20 * 1024**3, 32 * 1024**3)
    assert first.receive is None and first.read is None
    system.at += 2
    system.disks["PhysicalDrive0"].read_bytes += 2048
    system.disks["PhysicalDrive0"].write_bytes += 4096
    system.network["Ethernet"].bytes_recv += 6000
    system.network["Ethernet"].bytes_sent += 1000
    next_sample = sampler.sample()
    assert (next_sample.read, next_sample.write) == (1024, 2048)
    assert (next_sample.receive, next_sample.send) == (3000, 500)
    assert (next_sample.received_total, next_sample.sent_total) == (6000, 1000)
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
    system.at += 1
    system.network["Ethernet"].bytes_recv = 0
    system.disks["PhysicalDrive0"].read_bytes = 0
    reset = sampler.sample()
    assert reset.receive is None and reset.read is None
    system.at += 1
    system.network["Ethernet"].bytes_recv = 1024
    assert sampler.sample().receive == 1024


def test_hotplug_partial_failure_and_adapter_selection(system):
    sampler = Sampler()
    sampler.sample()
    system.at += 1
    system.unavailable.add("D:\\")
    system.parts.append(NS(mountpoint="E:\\", fstype="exFAT", opts="rw,fixed"))
    system.network["Wi-Fi"] = NS(bytes_recv=10**10, bytes_sent=100)
    system.disks["PhysicalDrive1"] = NS(read_bytes=10**12, write_bytes=0)
    sample = sampler.sample()
    assert sample.interface == "Ethernet"  # Auto choice stays stable while connected.
    assert [v.name for v in sample.volumes] == ["C:", "D:", "E:"]
    assert sample.volumes[1].used is None and sample.warnings
    assert sample.read is None
    system.at += 1
    switched = sampler.sample("Wi-Fi")
    assert switched.interface == "Wi-Fi"
    assert switched.receive is None and switched.received_total == 0
    del system.network["Wi-Fi"]
    system.at += 1
    offline = sampler.sample("Wi-Fi")
    assert offline.interface == "Wi-Fi" and offline.receive is None
    assert offline.warnings
    system.parts = []
    assert sampler.sample().volumes == ()


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
    assert sample.cpu == 42 and len(sample.volumes) == 2
    assert sample.warnings
