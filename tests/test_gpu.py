import subprocess
from types import SimpleNamespace

import pytest

from monitor35.gpu import NvidiaSampler


def test_gpu_values_and_bounded_hidden_read_only_query(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "nvidia-smi.exe")
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout="NVIDIA GeForce RTX 4070 SUPER, 72, 62\n")

    monkeypatch.setattr("subprocess.run", run)
    sampler = NvidiaSampler()
    value = sampler.sample(10)
    assert (value.percent, value.temperature) == (72, 62)
    assert value.name == "NVIDIA GeForce RTX 4070 SUPER"
    assert sampler.sample(10.1) == value
    assert len(calls) == 1
    assert calls[0][1]["timeout"] == 0.7
    assert calls[0][1]["creationflags"] == subprocess.CREATE_NO_WINDOW
    assert calls[0][0][1:] == [
        "--id=0",
        "--query-gpu=name,utilization.gpu,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]


@pytest.mark.parametrize("response", ["broken", "RTX, nan, 62", "RTX, 101, 62"])
def test_invalid_gpu_values_are_unavailable_and_retry(monkeypatch, response):
    monkeypatch.setattr("shutil.which", lambda _: "nvidia-smi.exe")
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: SimpleNamespace(stdout=response))
    sampler = NvidiaSampler()
    assert sampler.sample(1).warning
    assert sampler.sample(1).percent is None
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: SimpleNamespace(stdout="RTX, 5, 30"))
    assert sampler.sample(15).percent is None
    assert sampler.sample(16).percent == 5


def test_gpu_timeout_discards_stale_values_and_recovers(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "nvidia-smi.exe")
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: SimpleNamespace(stdout="RTX, 5, 30"))
    sampler = NvidiaSampler()
    assert sampler.sample(1).percent == 5

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 0.7)

    monkeypatch.setattr("subprocess.run", timeout)
    failed = sampler.sample(2)
    assert failed.percent is None and failed.temperature is None and failed.warning
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: SimpleNamespace(stdout="RTX, 6, N/A"))
    recovered = sampler.sample(17)
    assert recovered.percent == 6 and recovered.temperature is None


def test_absent_gpu_tool_does_not_launch_a_process(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)

    def unexpected(*args, **kwargs):
        pytest.fail("An unavailable executable must not be launched")

    monkeypatch.setattr("subprocess.run", unexpected)
    assert NvidiaSampler().sample(1).warning
