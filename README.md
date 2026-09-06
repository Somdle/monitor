# Monitor35

Turing 3.5인치 USB 화면용 Windows 데스크톱 모니터와 기본 배치 편집기.
현재 장치: USB35INCHIPSV2, 480×320 가로 화면. 기존 UsbMonitor 설치는 유지한다.

## 실행

현재 PC에는 .venv와 의존성이 준비되어 있다. **start.cmd**를 실행하면 미리보기가 열린다.
다른 환경은 Python 3.12( tkinter 포함)를 설치하고 **setup.cmd**를 실행한다.

1. 기존 UsbMonitor에서 편집 중인 테마를 저장하고 프로그램을 종료한다.
2. start.cmd 실행 후 **화면 연결**을 누른다. 초기화에 수 초 걸릴 수 있다.
3. 미리보기 항목을 드래그하거나 오른쪽 위치/글자 크기를 입력하고 적용한다.
4. **테마 저장**으로 유지한다. Ctrl+S 저장, Ctrl+Z 실행 취소. 닫을 때 미저장 변경은 자동 저장한다.
5. **연결 해제**로 포트를 반납한다. 마지막 화면은 LCD에 남는다.

화면이 거꾸로 보이면 오른쪽 **화면 180° 회전**을 켠다. 미리보기와 실제 출력에 바로 반영되며,
회전한 미리보기에서도 항목을 드래그할 수 있다. **테마 저장**으로 방향을 유지한다.

CPU 사용률, RAM 사용률, 현재 드라이브 사용량, 시계를 표시한다.
위치·글자 크기·색상·밝기 편집 및 저장본 불러오기를 지원한다.
앱을 닫으면 종료된다. 트레이/로그인 자동 실행은 아직 설정하지 않는다.

## 자동 복구

- 절전 진입 시 화면 끄기 명령을 보내고 포트를 닫는다. 복귀 전에는 갱신하지 않는다.
- Windows 절전 복귀 이벤트와 실행 시간 공백을 감지한다.
- USB 오류 시 1~15초 간격으로 장치를 다시 탐색한다. COM4를 고정하지 않는다.
- 재연결 시 초기화·방향·밝기를 적용하고 화면 전체를 다시 보낸다.
- 정상 상태에서는 변경 영역만 보내고 30초마다 전체 화면을 갱신한다.
- 화면 아래 연결 상태·전송 수·실패 수·최근 전송 시간을 표시한다.

COM 포트 액세스 거부는 보통 다른 프로그램의 점유를 뜻한다. UsbMonitor와 동시에 연결하지 않는다.
별도 보드 모델에서 초기화 후 연결되지 않으면 **재연결 시 장치 초기화**를 해제하고 다시 연결한다.
USB 재삽입이 필요한 펌웨어 고장까지 소프트웨어로 복구된다고 보장하지 않는다.

## 진단 명령

```powershell
.\.venv\Scripts\python.exe -m monitor35 --devices
.\.venv\Scripts\python.exe -m monitor35 --smoke 3 --data-dir .tmp/preview
.\.venv\Scripts\python.exe -m monitor35 --connect --smoke 30 --data-dir .tmp/device
```

--smoke는 정상 종료 시 0, worker 오류 또는 마지막 실기기 전송 실패 시 1을 반환한다.
실기기 smoke 성공은 전송 완료 기준이며, 물리 화면 출력과 실제 절전·복귀 검증은 별도다.
테마: data/theme.json. 로그: data/monitor.jsonl. --data-dir로 분리할 수 있다.
로그는 로컬에만 기록되고 1MB 단위로 회전한다. 잘못된 테마는 덮어쓰지 않는다.

## 현재 범위와 제한

첫 버전은 연결 복구와 기본 편집 검증용이다. CPU/GPU 온도·GPU 사용률, 그래프, 배경 이미지,
세로 화면, 원본 .data 테마 가져오기, 트레이 및 자동 실행은 아직 없다.
실제 LCD ACK가 없는 장치이므로 전송 성공 수치만으로 화면 갱신을 확정할 수 없다.

## 개발

명령은 [AGENTS.md](AGENTS.md), 구조는 [docs/architecture](docs/architecture/overview.md),
선택 이유는 [decisions.md](docs/architecture/decisions.md)를 참고한다.

## 출처

장치 프로토콜은 [smartscreen-driver](https://github.com/hchargois/smartscreen-driver) 0.2.3을 사용한다.
원 프로젝트는 [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python)이다.
GPL-3.0-or-later. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 참고.
