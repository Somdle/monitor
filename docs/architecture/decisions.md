# Decisions

## 2026-09-06 — Python desktop and existing serial driver

Why: 절전 복귀 후 연결 복구와 불편한 편집기를 개선하고, 첫 단계에서 현재 3.5인치 장치로 검증한다.
Alternatives: 제조사 최신 버전 유지, turing-smart-screen-python 전체 사용, React/Mantine 웹 편집기.
Decision: 설치된 Python 3.12의 Tkinter + Pillow + psutil, smartscreen-driver 0.2.3.
현재는 네이티브 데스크톱 앱이며 LAN 서버가 필요 없다. UI와 Windows 전원 이벤트를 직접 연결할 수 있다.
웹 편집기는 캔버스 기능을 늘릴 때 검토할 수 있지만 현재 JSON 모델/렌더러 계약을 유지해야 한다.

Drawbacks: Tkinter의 스크린리더 접근성과 디자인 확장에는 한계가 있다. 고급 편집기나 완성 제품으로 보지 않는다.
Windows 글꼴 Segoe UI와 Python tkinter가 필요하다. CPU/GPU 온도 수집은 아직 없다.
GPL 드라이버를 의존하므로 프로젝트에도 GPL-3.0-or-later를 명시하고 출처를 기록한다.

Migration: 새 프로젝트로 기존 계약 변경은 없다. 원본 .data 테마는 자동 호환되지 않는다.
원본 설치를 보존하며 앱 종료 후 UsbMonitor를 다시 실행해 복귀할 수 있다. 자동 실행은 설정하지 않는다.

## Pre-write evidence
빈 폴더에서 시작했으며 기존 코드/AGENTS/구조/설정은 없었다. 재사용 가능한 로컬 정의는 없다.
중앙 project-ai 템플릿을 복사해 실제 구조로 채웠다. Git 저장소가 아니므로 상태 검사 후 fetch/branch는 해당 없음이다.
증상 원인은 아직 실기기 절전으로 확정하지 못했으므로 추정 원인을 확정된 진단으로 기록하지 않는다.

## 2026-09-06 — 180-degree rotation

Why: 장착 방향 때문에 화면이 거꾸로 보인다.
Decision: Theme.rotate_180 선택 필드를 추가하고 runtime에서 장치 전송 직전에 회전한다.
공통 렌더러와 편집 미리보기는 항상 정방향이며 드래그 좌표도 유지한다.
Alternative: 장치 방향 명령 변경 대신 완성된 픽셀을 회전하여 기존 전송 계약을 유지한다.
Cost: 회전을 켠 경우 전송용 이미지가 한 장 추가된다.
Migration: 버전 1 테마에 기본값 false인 선택 필드를 추가한다. 기존 배치·방향을 유지하며
저장할 때 새 필드를 기록한다. 기존 필드나 계약을 제거하는 호환 레이어는 없다.
