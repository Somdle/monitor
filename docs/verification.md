# Verification — 2026-09-06

## Automated checks

- `python -m pytest --basetemp=.tmp/pytest`: 30 passed.
- `python -m ruff check src tests`: passed.
- `python -m ruff format --check src tests`: passed.
- `python -m mypy src`: 10 source files passed.
- `python -m pip check`: no broken requirements.
- `python -m build --outdir .tmp/dist`: wheel and source distribution built.
- Local Markdown links: 10 documents passed before this report was added.

The automated tests include write timeout/partial write, COM number change,
retry pacing, resume gap, native WM_POWERBROADCAST callback delivery, full redraw,
changed-region rendering, sensor failure, latest-only mailbox, layout validation,
save/reload/undo and clean worker shutdown. Suspend tests verify SCREEN_OFF before
close, no frame transmission while suspended, restoration on resume and ignoring
the second Windows resume message for the same wake cycle.

## Desktop and physical device

- Desktop editor: drag changed CPU from (28,74) to (60,86); Ctrl+S persisted it.
- Fixed clipped status area; verified all controls and connection status remain visible.
- Final screenshot: `.tmp/verification/editor.jpg` (project-relative).
- Actual device: COM4, USB35INCHIPSV2.
- Initial device smoke correctly failed with access denied while UsbMonitor held the port.
- User approved stopping UsbMonitor. OS denied agent termination; user closed it manually.
- 30-second device smoke: exit 0, 26 transmissions, 0 failures.
- User confirmed the physical screen displays SYSTEM / 35 and updates the numbers.
- Updated GUI is running connected with no transmission errors observed.
- Actual PC sleep/resume: user confirmed automatic updates resume successfully.
- User found the LCD stayed on during sleep. Added suspend → SCREEN_OFF → close
  and suspended-worker gating. Physical sleep/off verification is pending for this fix.
- Physical USB unplug/replug and extended overnight operation: not tested.
- Screen-reader compatibility: not tested; Tk accessibility tree is limited.

## Structure Compliance — PASS

Checked the new-file diff (`.tmp/review.patch`) against architecture ownership.
No duplicate protocol encoder, settings model or reconnect policy. AST dependency
test enforces the directed imports. Serial/sensor work stays off the UI thread.
Display errors are surfaced and retried; unexpected worker/UI errors are logged
and shown. Tests replace only external serial/display boundaries.
No legacy compatibility layer, placeholder implementation or unrelated change.

Git status reports this directory is not a repository. Fetch/upstream/branch/diff
against an existing commit are not applicable. No Git initialization, commit,
branch change, remote write or automatic startup configuration was performed.

## Limits

Transmission success means an OS serial write completed, not an LCD acknowledgement.
The vendor app's original failure has not been reproduced and diagnosed internally.
The new application recovered in one real sleep/resume trial. Extended repetition
and the added screen-off behavior must be verified separately.

## Rotation update

Added optional Theme.rotate_180 (default false) and a desktop checkbox. The worker
rotates only the device output; rendering, preview snapshots, editor hit testing
and drag coordinates remain upright. Tests verify exact device pixels and upright
snapshots, persistence, old-theme loading, boolean validation, unchanged selection
bounds, drag direction, undo and checkbox reload.
Validation: Ruff lint/format, mypy, all 32 tests, package build and diff check passed.
Structure Compliance: PASS — existing Theme owns orientation, only runtime transforms
device output, no new helpers/schema/dependencies or error fallbacks. Obsolete editor
coordinate conversion was removed. Physical output for this correction has not been
visually rechecked on the connected LCD.
Tk test finalizers are collected on the main thread to prevent delayed cleanup
from blocking subsequent worker tests.
The existing application has unsaved user edits. Window input activation failed,
so it was not forcibly stopped and its live theme was not overwritten. User should
save and restart with start.cmd to use the new checkbox.

## Performance dashboard update — 2026-09-06

- Task Manager style four-card renderer replaces the decorative title and clock.
  CPU/memory use percent charts, disk/network use throughput charts, all spanning 60 seconds.
- Live sampling found C:, D:, E: formatted local volumes and three physical disk counters.
  Empty F:/G: media are excluded. Actual memory capacity and Ethernet traffic rendered
  successfully in `.tmp/dashboard-smoke/preview.png` during a real sensor smoke run.
- 41 tests cover elapsed-time rates, memory quantities, multiple volumes, hotplug,
  counter reset, unavailable disk counters, partial volume failure, adapter selection,
  bounded history, chart/paging pixels, v1 migration/backup, editor undo and output-only rotation.
- Ruff lint/format, mypy, pytest, package build and diff checks passed.
- Structure Compliance: PASS. New sensor shapes and rate state have a single owner in
  sensors; architecture import checks pass; renderer remains upright and serial recovery
  stays in session/device. No internal mocks or duplicate rate calculation paths were added.
  v1 is a one-way input migration with an explicit exit condition in decisions.md.
- Real Tk tests pass with one Tcl interpreter and separate windows. A separate review
  window launched, but Computer Use returned an incorrect foreground capture and then
  `failed to activate captured window`; full-window visual verification is unconfirmed.
  The Pillow output itself was visually inspected. No current LCD transmission/sleep
  test is claimed for this update. The user's running app and data were not replaced;
  save, close and restart with start.cmd to load the updated code.

## Large numeric readouts — 2026-09-06

Removed disk capacity sampling, the Volume shape, editor table and LCD pagination.
All physical disk R/W counters remain aggregated. Primary memory, R/W, network rate
and cumulative numbers use Widget.size (24px by default), matching CPU percentage.
Units and chart scales remain secondary. Saved v2 themes need no migration.
Live sensor smoke rendered `.tmp/large-numbers/preview.png`; the output was visually
inspected at native 480×320 size. Tests cover multi-disk R/W summation, persistent
non-paging output, editable R/W/network numeric size and existing recovery behavior.
Structure Compliance: PASS — removed unused shapes/UI/I/O, retained documented import
boundaries and one rate calculation owner. No additional dependency or fallback path.
LCD readability on the physical 3.5-inch panel still requires user confirmation.
Validation: all 42 tests, Ruff lint/format, mypy, package build and diff checks passed.
