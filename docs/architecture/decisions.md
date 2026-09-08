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

## 2026-09-06 — Large numeric readouts

Why: 사용자가 디스크 용량은 불필요하며 3.5인치 화면의 주요 숫자를 CPU % 크기로 요청했다.
Decision: 용량 수집/Volume 모델/표/페이지 전환을 제거하고 전체 물리 디스크 R/W를 유지한다.
속도와 네트워크 누적량은 좌우 열에 숫자와 단위를 분리해 표시한다. 메모리 사용/전체 용량,
R/W, 송수신 속도와 누적량은 각 Widget.size(기본 24px)를 적용한다.
Alternative: 긴 값 전체를 한 줄로 확대하면 카드 밖으로 넘쳐 채택하지 않았다.
Cost: 보조 단위와 차트 눈금은 작은 크기를 유지한다. 100 이상 변환값은 소수점을 생략한다.
Migration: 저장 형식과 기본 숫자 크기는 그대로이며 모든 카드에서 숫자 크기 편집을 제공한다.
구형 용량 수집 호환 경로나 새 상태는 없다. 기존 센서/렌더러/편집기 소유권과 회전은 유지한다.

## 2026-09-07 — Uniform bottom charts and GPU telemetry

Why: 사용자가 모든 차트를 기존 디스크 크기로 맞추고 정보를 위로 배치하도록 요청했다.
CPU/GPU 교대 대신 같은 카드에 두 사용률을 함께 표시하는 선택을 확인했다.
Decision: CHART_BOX=(10,84,219,132)를 renderer가 소유하고 모든 카드가 한 공통 호출로
하단 차트를 그린다. CPU/GPU는 큰 사용률 숫자와 두 곡선을 표시한다. GPU 온도/그래픽 클럭,
CPU 기준 클럭과 네트워크 누적량은 상단 보조 행에 둔다. 테마 형식과 회전 계약은 그대로다.
Sensor boundary: gpu.py가 nvidia-smi의 명시적 CSV 필드 조회와 GpuSample을 소유한다.
명령은 읽기 전용, shell 없이 숨김 실행, 0.7초 제한이며 실패 즉시 오래된 값을 폐기하고
15초 후 재시도한다. UI/USB thread 소유권은 변하지 않는다. GPU 조회에는 새 의존성이 없다.
Alternatives: NVIDIA는 호환성 면에서 NVML 바인딩을 권장한다. 여기서는 GPU 드라이버 호출을
별도 프로세스에서 시간 제한할 수 있는 CLI를 사용한다. 출력 형식을 엄격히 검사하고 실패를
unavailable로 전파하므로 드라이버 변경 시 잘못된 수치를 표시하지 않는다.
Cost: 프로세스 조회 비용이 추가된다. NVIDIA GPU 0만 지원하며 AMD 내장 GPU/CPU 온도는
현재 지원하지 않는다. CPU max frequency는 기준 클럭으로 표기하고 현재 부스트 값으로 주장하지 않는다.
Evidence: RTX 4070 SUPER 사용률/온도/현재 그래픽 클럭을 실제 조회했다.
Source: https://docs.nvidia.com/deploy/nvidia-smi/index.html
Pre-write: main/origin/main 동기화, 설명 가능한 진행 중 변경만 존재했다. 기존 sensors/render
소유권과 import 검사에서 GPU 경계를 추가했고, 원본 앱·드라이버·전원 설정은 수정하지 않았다.

## 2026-09-07 — CPU/GPU temperatures instead of clocks

Decision: CPU/GPU 클럭 표시와 전용 클럭 조회를 제거하고 온도를 22px로 표시한다.
CPU는 별도 PowerShell 프로세스의 LibreHardwareMonitor CPU package/Tctl/Tdie 센서를 사용한다.
기존 Windows 센서는 Ryzen 7 9700X 온도를 제공하지 않았으며 ACPI/메인보드 값을 대체하지 않는다.
온도 프로세스는 직렬 I/O worker를 막지 않고 최신 값만 전달한다. 5초 공백/프로세스 종료/범위 오류는
unavailable로 처리한다. worker 종료 시 센서 프로세스를 종료한다. 센서 라이브러리는 공식
0.9.6 zip의 SHA-256 검증 후 .venv/hardware에 준비하며 기본 의존성에 자동 설치하지 않는다.
Alternative: 제거된 구버전 LHM WMI API나 메인 앱 내부 .NET 로딩 대신 격리 프로세스를 사용한다.
Cost: PawnIO 드라이버와 관리자 권한이 필요할 수 있다. 시스템 변경은 사용자 사전 승인 대상이다.
공식 배포본 내 PawnIO 설치 파일의 Authenticode 서명은 Valid(namazso)로 확인했다.
드라이버 설치 전에는 CPU 온도 실측을 완료했다고 주장하지 않는다.

## 트레이 상주
pystray 0.19.5의 Windows 이벤트 루프를 별도 스레드에서 실행한다. Tk 조작은 기존 poll 루프만 수행한다. 창 X는 저장 후 숨김, 명시적 완전 종료는 기존 worker 종료 경로를 재사용한다. 숨김 중에는 편집기 재렌더링만 생략한다. 로그인 자동 실행 및 시스템 설정은 변경하지 않는다.

## 단일 실행과 기존 창 활성화
창 제목 검색은 시작 중/트레이 숨김을 놓치므로 Windows named mutex로 GUI 초기화 전에 소유권을 획득한다. 먼저 생성한 auto-reset event가 시작 중 열기 요청도 보관한다. 파일 잠금/네트워크 서버 없이 기존 Tk poll에서 창을 복원한다. 같은 Windows 세션에서 data-dir와 관계없이 한 인스턴스만 허용한다. 진단 --devices와 무장치 --smoke는 제외하며 --connect 스모크는 잠금을 준수한다. 이전 버전에는 이 프로토콜이 없으므로 업데이트 후 기존 앱을 한 번 완전히 종료해야 한다.
근거: https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createmutexw 및 https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createeventw

## 선택적 로그인 자동 실행
사용자 체크 액션에서만 HKCU Run의 Monitor35 값을 등록/해제한다. 관리자 권한이나 작업 스케줄러 없이 로그인 시 pythonw를 실행하며 절대 data-dir 및 --background --connect를 전달한다. 콘솔창과 작업 디렉터리 의존을 피한다. 기존 단일 실행 정책을 재사용한다. 앞선 자동 실행 제외 범위를 이 기능으로 확장하되 기존 UsbMonitor 설정은 변경하지 않는다.
근거: https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys
