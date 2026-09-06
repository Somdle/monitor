# Verification — 2026-09-06

## Automated checks

- `python -m pytest --basetemp=.tmp/pytest`: 27 passed.
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
