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

## Uniform charts and GPU — 2026-09-07

All four cards use the disk chart rectangle (10,84)-(219,132), with data above it.
CPU and GPU utilization appear together as requested; GPU temperature/current graphics
clock and CPU nominal clock are secondary labels. CPU temperature is explicitly unsupported.
Live RTX 4070 SUPER values were read through the installed NVIDIA driver tool and rendered
in `.tmp/unified-charts/preview.png`, visually inspected at native 480×320 resolution.
All 50 tests, Ruff lint/format, mypy, wheel/sdist build and diff checks passed.
New checks cover chart geometry, placement of data above graphs, GPU parsing/unavailable
fields, bounded hidden process execution, timeout, retry and continued core sampling.
Structure Compliance: PASS — GPU query/shape owned by gpu, history owned by sensors,
chart bounds owned by render. No duplicated chart paths, new dependency, driver setting
change or internal implementation mock. Existing theme and output-only rotation remain.
This update's physical LCD readability and real sleep/resume have not been revalidated.

## Fixed network Mbps — 2026-09-07

Network speed labels and chart scale now always use Mbps, converting bytes/s by
8/1,000,000 in the renderer. The chart minimum is 1 Mbps, with automatic power-of-two
Mbps ranges. Cumulative bytes and disk rate units remain unchanged. Live sensor output
was inspected in `.tmp/mbps/preview.png`. All 57 tests, lint and mypy passed.
Structure Compliance: PASS — one network formatter, unchanged sensor units/schema,
unchanged import boundaries, explicit low/high/unavailable value tests.

## Fixed disk Mbps — 2026-09-07

Disk R/W now shares the Mbps formatter and chart scaling with network throughput.
Removed the separate byte-rate format and network-only chart flag. All 58 tests passed,
including identical disk/network numeric and chart pixels for equal byte rates.
Structure Compliance: PASS — one rate conversion/formatting path; sensor byte counters,
cumulative quantities, theme format and dependencies are unchanged.

## Disk MB/s, network Mbps — 2026-09-07

Disk numbers/axes use decimal MB/s; network retains decimal Mbps. One rate formatter
and unit-divisor mapping own both conversions. A 1,000,000 B/s disk rate displays
1.00 MB/s; a 125,000 B/s network rate displays 1.00 Mbps. All 61 tests, lint and
mypy passed, including relative chart scaling and fixed-unit conversion checks.
Structure Compliance: PASS — no new dependencies/schema; byte counters stay unchanged.

## Memory percentage primary — 2026-09-07

Memory utilization is now the large primary value (Widget.size); used/total capacity
is secondary text above the unchanged bottom chart. Live preview was inspected in
`.tmp/memory-percent/preview.png`. All 62 tests, lint and mypy passed. The new pixel
test distinguishes percentage changes in the primary row from capacity changes below.
Structure Compliance: PASS — renderer-only behavior change; no new model/helper/I/O.

## Large CPU/GPU temperatures — 2026-09-07

Removed CPU/GPU clock data and queries; both temperature readouts use 22px. Live GPU
temperature and the CPU unavailable state were inspected in .tmp/cpu-temperature/preview.
67 tests, lint and mypy passed. CPU probe tests cover valid/invalid/unavailable values,
stale value rejection and owned-process shutdown. PowerShell source parses successfully.
Structure Compliance: PASS — CPU acquisition isolated in cpu_temperature; no sensor work
on the Tk thread, no new rate policy/schema, no board temperature substituted for CPU.
LibreHardwareMonitor 0.9.6 zip hash matches official release metadata. Its bundled PawnIO
installer has a valid namazso Authenticode signature and SHA-256
a3a46226c5e2824f4cdd42be0eecbabfc672c86f7889710f5ab1e6ad385b47a0.
CPU hardware measurement is pending explicit permission to install PawnIO; nothing has
yet installed the driver or changed system permissions.

## 2026-09-08 백그라운드 실행

- X/백그라운드로: 저장 후 withdraw; 센서/장치 worker와 power listener 유지.
- 실제 Windows 트레이로 숨김 중 센서 갱신, 다른 스레드의 메뉴 명령을 통한 복원, 자동 저장, 전체 종료를 검증했다.
- 트레이 생성 실패와 실행 중 트레이 소멸 시 창 유지/복원, 저장 실패 시 숨김 취소를 검증했다.
- pytest 70 passed, ruff check/format 및 mypy 통과. 무장치 2초 smoke 통과.
- 이번 변경의 USB 실기기 전송과 실제 절전/복귀는 재검증하지 않았다. CPU 온도 드라이버 설치는 승인 대기 상태다.
- Structure Compliance: PASS — 트레이 소유권 분리, app → tray 단방향 import, Tk 조작은 메인 스레드, 기존 worker 종료 경로 재사용.
- Structure Compliance: PASS — 실제 diff 검토, 중복 상태/헬퍼 및 순환 의존성 없음, 외부 오류 로깅과 접근 가능한 창 복원, 정상/실패 경로 행동 검증.

## 2026-09-08 전용 트레이 아이콘

- icon.app_icon의 단일 디자인을 트레이와 Tk 창에서 재사용. 남색/청록색 모니터와 흰 그래프, 투명 모서리.
- PNG 및 16/24/32/48/64/128/256px ICO를 배포 패키지에 포함하고 wheel 내부 확인.
- 전체 70 tests pass. iconphoto 문자열 핸들 타입 수정 후 desktop/architecture 6 tests 재검증 통과; ruff/format/mypy/build 통과.
- 아이콘 PNG 육안 확인. 기존 앱을 UI에서 정상 종료하고 --background --connect로 새 버전을 실행했다. COM4 device_opened 로그 확인.
- 숨겨진 아이콘 팝업의 실제 배치는 자동화에서 직접 캡처하지 못했다. 실제 트레이 수명/숨김/복원은 desktop 테스트로 검증했다.
- Structure Compliance PASS: 실제 diff 및 신규 모듈 검토, icon은 순수 렌더러, app/tray → icon 단방향, 기존 트레이/종료 경로 재사용. 시스템 설정 변경 없음.

## 2026-09-08 단일 실행

- Windows named mutex/event로 UI·로깅·센서 시작 전 중복 실행 차단. 기존 Tk poll에서 창 복원, worker 유지.
- 실제 별도 프로세스 중복 알림, 시작 전 대기 신호 소비, 정상 종료 후 재획득, 비정상 종료 후 abandoned mutex 회수 검증. 숨긴 편집창의 프로세스 간 복원 검증.
- pytest 73 passed; ruff/mypy 통과.
- Structure Compliance PASS: 신규 instance 경계와 app/__main__ 단방향 import, 기존 show/worker 재사용, 실제 diff 검토 및 정상/실패 수명 검증. 임시 파일이나 네트워크 포트 불필요.

## 네트워크 MB/s 통일
- 네트워크 수신/송신 숫자와 차트 눈금을 디스크와 같은 decimal MB/s로 변경. 누적량 표시는 유지.
- 비트 단위 분기를 제거하고 BYTES_PER_MB/format_speed를 단일 경로로 사용. 동일 byte/s 입력의 디스크/네트워크 숫자와 차트 일치 검증.
- 렌더 테스트 16개, ruff, mypy 및 diff check 통과. Structure Compliance PASS: 기존 렌더 소유권 유지, 중복 단위 처리 제거, 관련 diff 검토. 실행 중 앱에는 재시작 후 적용.

## 디스크·네트워크 정보 배치 통일
- 공통 이름/속도/MB/s/차트 배치로 통합하고 네트워크 전용 누적량 표시는 제거. 미사용 quantity 렌더 helper 제거. 센서 수집은 유지.
- 동일 속도의 두 카드에서 숫자·단위·차트 영역이 일치하는 렌더 테스트 16개 통과. ruff/mypy/diff check 통과. 생성 미리보기 육안 확인.
- Structure Compliance PASS: 기존 공통 렌더 루프 재사용, 중복 레이아웃 없음, 변경 코드 및 관련 테스트 검토.

## 최근 1분 I/O 사용량
- 속도 숫자 오른쪽 MB/s, 아래 1m MB. Point에 실측 구간 길이를 추가해 기존 이력을 적분; 최근 60초 경계는 비례 계산. 공백/어댑터 변경 시 기존 이력 초기화 정책 재사용.
- 테스트 77개, ruff/mypy 통과. 생성 미리보기 육안 확인. Structure Compliance PASS: 센서 이력이 계산 소유, 렌더는 표시만 수행, 중복 누적 상태 없음, 관련 diff 검토.
