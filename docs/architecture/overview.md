# Architecture Overview

Monitor35는 Windows + Python 3.12 데스크톱 앱이다. tkinter는 네이티브 창과 폼을, Pillow는 480×320 화면 렌더링을 담당한다.
센서 수집 → Pillow 이미지 → 장치 세션 → smartscreen-driver Rev A → USB 직렬 화면 순서로 흐른다.
UI와 장치 전송은 별도 스레드다. 크기 1 mailbox는 최신 미리보기만 유지하고 USB 프레임 큐는 만들지 않는다.

진입점은 src/monitor35/__main__.py이며 --devices, --smoke SECONDS, --connect, --data-dir를 제공한다.
외부 I/O는 psutil 센서 조회, USB 직렬 포트, data/theme.json 및 회전 JSON 로그다. HTTP 서버나 외부 전송은 없다.

첫 구현 범위: 가로 화면, CPU/RAM/디스크/시계, 위치/크기/색상/밝기 편집, 저장/불러오기/실행 취소,
Windows 복귀 이벤트 및 시간 공백 감지, 제한 시간·재시도·포트 재탐색·전체 다시 그리기.
센서 온도/GPU, 트레이 상주/자동 실행, 세로 화면, 원본 .data 가져오기는 포함하지 않는다.

절전 진입은 power → worker 완료 대기(최대 1.5초) → session.screen_off/close 순서다.
복귀 시 worker가 세션을 다시 연결한다. 절전 중 frame 전송으로 화면을 다시 켜지 않는다.
