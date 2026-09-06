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

## 2026-09-06 — Performance dashboard

Why: 단일 실행 드라이브의 %만 표시하던 모델로는 다중 디스크, 실제 메모리 용량,
네트워크 속도와 시간 추이를 표현할 수 없다. 사용자가 작업관리자 형태의 재설계를 요청했다.
Decision: sensors 모듈의 불변 Telemetry/Volume/Point가 센서 계약을 소유하고 Sampler가
monotonic 시간과 어댑터별 기준값으로 속도·측정 누적량·최대 60초 이력을 계산한다.
runtime은 worker 수명과 전송만 조립한다. render는 정방향의 230×150 카드 4개를 그린다.
대안: 기존 scalar dict 확장은 타입/단위/이력 소유권이 불명확해 채택하지 않았다.
단일 디스크 선택 대신 로컬 볼륨 전체를 열거하고 LCD에서 2개씩 6초 순환한다.
I/O는 전체 물리 디스크 처리량이며 볼륨 용량 또는 Windows 활성 시간 %와 구분한다.
네트워크는 한 어댑터를 선택해 VPN/가상 장치 중복 합산을 피한다. 자동 선택은 연결 동안 고정한다.
Cost: 차트 변경으로 전송량이 늘며 작은 화면에서는 보조 글자가 작다. 디스크 페이지 순환으로
다른 볼륨 확인에 최대 6초×페이지 수가 걸린다. PC 편집기에는 전체 볼륨 표를 제공한다.
Migration: Theme 버전 2는 새 배치/색상과 network 항목을 사용한다. v1은 유효성을 검사한 뒤
새 배치로 일방향 변환하며 밝기/장치 초기화/회전을 유지한다. 첫 저장 전에 원본을 원자적으로
theme.v1.json에 보관한다. 런타임 구형 렌더러/좌표 호환 분기는 없다.
Legacy exit: v1 importer는 기존 파일 입력 경계에만 있다. 모든 사용 테마가 v2로 저장되고
v1 지원 종료를 명시하는 다음 테마 major 변경 시 migrate_v1과 이전 테스트를 함께 제거한다.
Rollback: 앱 종료 후 보관한 원본을 theme.json으로 복원하고 이전 소스를 사용한다.
검증 근거: 설치된 psutil 7.2.2 API와 https://psutil.io/ 의 공식 disk/network API 문서.

Pre-write: main은 origin/main과 동기화되고 작업 전 clean이었다. 기존 render/theme/runtime,
AST import 검사, 테스트를 확인했다. 새 수집 계약은 sensors만 소유하고 theme은 I/O에 의존하지
않는다. USB 복구와 화면 회전 정책은 기존 소유자에 유지한다. 센서 실패는 기존 worker 오류
경계, 읽기 불가 볼륨/네트워크 단절은 경고와 unavailable 값으로 관측 가능하게 표시한다.
