import subprocess
import sys
import uuid

from monitor35.instance import SingleInstance


def test_other_process_signals_owner_and_lock_releases():
    name = "Local\\Monitor35.Test." + uuid.uuid4().hex
    owner = SingleInstance(name)
    try:
        assert owner.owner
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                "from monitor35.instance import SingleInstance; "
                "import sys; s=SingleInstance(sys.argv[1]); print(s.owner); s.close()",
                name,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        assert child.returncode == 0, child.stderr
        assert child.stdout.strip() == "False"
        assert owner.activation_requested()
        assert not owner.activation_requested()
    finally:
        owner.close()
    replacement = SingleInstance(name)
    try:
        assert replacement.owner
    finally:
        replacement.close()


def test_crashed_owner_does_not_block_next_start():
    name = "Local\\Monitor35.Test." + uuid.uuid4().hex
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from monitor35.instance import SingleInstance; "
            "import sys; s=SingleInstance(sys.argv[1]); print(s.owner, flush=True); "
            "sys.stdin.readline()",
            name,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    holder = None
    try:
        assert child.stdout.readline().strip() == "True"
        holder = SingleInstance(name)
        assert not holder.owner
        child.terminate()
        child.wait(timeout=5)
        replacement = SingleInstance(name)
        try:
            assert replacement.owner
        finally:
            replacement.close()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        if holder is not None:
            holder.close()
        child.stdin.close()
        child.stdout.close()
