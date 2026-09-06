# AGENTS

## Project Purpose
Windows의 Turing 3.5인치 USB 화면용 개인 모니터링 앱이다. Python 3.12 + Tkinter 데스크톱 UI를 사용한다.
`python -m monitor35`는 미리보기로 시작한다. 장치 전송은 화면 연결 또는 `--connect`로 명시한다.
원본 UsbMonitor 설치·테마·자동 실행·전원 설정은 변경하지 않는다. 같은 장치는 한 프로세스만 사용한다.

## Context Loading
[overview](docs/architecture/overview.md)를 먼저 읽고 작업에 맞는 layers, dependency-rules, ssot, errors, testing 문서를 읽는다.
중앙 coding standards와 repo-prewrite/repo-postwrite를 적용한다.

## Commands
PowerShell, 프로젝트 루트 기준:
- 설치: `./setup.cmd`
- 실행: `./start.cmd`
- 린트: `.venv/Scripts/python -m ruff check src tests`
- 포맷: `.venv/Scripts/python -m ruff format --check src tests`
- 타입: `.venv/Scripts/python -m mypy src`
- 테스트: `.venv/Scripts/python -m pytest --basetemp=.tmp/pytest`
- 빌드: `.venv/Scripts/python -m build --outdir .tmp/dist`
- 무장치 스모크: `.venv/Scripts/python -m monitor35 --smoke 3 --data-dir .tmp/smoke`

## Structure Rules
소유권과 import 방향은 architecture 문서 및 tests/test_architecture.py에 기록한다.
UI에서 USB I/O를 실행하지 않는다. 재연결 정책은 DisplaySession만 소유한다.
임시 산출물은 .tmp/, 사용자 데이터는 data/, 의존성은 .venv/에 둔다.
아직 Git 저장소가 아니므로 fetch/upstream/branch 검사는 해당 없음이다. Git 초기화나 원격 연결을 자동 수행하지 않는다.
