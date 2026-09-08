# Layers and Ownership

| Module | Owns |
|---|---|
| theme | 불변 Widget/Theme 모델, 유효성 검사, JSON 저장 |
| render | Pillow 화면 렌더링, 글꼴 캐시 |
| device | 장치 검색, smartscreen-driver 확장, 제한 시간 있는 전송 |
| session | Display protocol, 복구 상태, 마지막 성공 프레임, 차분 전송 |
| sensors | Telemetry/Point, psutil 수집, 시간 기반 속도·누적량·60초 이력 |
| gpu | GpuSample, 제한 시간 있는 NVIDIA 읽기 전용 조회와 센서 재시도 |
| cpu_temperature | 별도 LibreHardwareMonitor 프로세스 수명, CPU 온도 읽기·유효성·신선도 |
| runtime | worker 수명, 최신 snapshot 전달, 장치 출력 회전 |
| power | Windows WM_POWERBROADCAST 수신 및 절전/복귀 알림 |
| app | Tk 편집기, 사용자 액션, undo, 오류 표시 |
| logging_setup | 로컬 회전 JSON 로그 |
| __main__ | CLI 조립, GUI/스모크 실행 |

새 화면 종류를 추측해 추가하지 않는다. 현재 장치의 serial ID만 허용한다.

- tray: pystray Windows 이벤트 루프와 아이콘 수명 소유. 메뉴 콜백은 큐에 명령만 넣는다. app의 Tk poll이 숨김/복원/종료를 처리한다.

- icon: 트레이/편집창 공통 아이콘의 순수 Pillow 렌더링. assets의 PNG/ICO는 app_icon(256)에서 내보낸 배포 자산.

- instance: Windows 세션 내 단일 실행 소유권과 프로세스 간 창 열기 신호. __main__이 수명을 관리하고 app.poll이 신호를 소비한다.
