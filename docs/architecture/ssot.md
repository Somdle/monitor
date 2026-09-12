# SSOT

- 테마의 필드/범위/버전: theme.py의 Widget와 Theme.
- 화면 크기: theme.py의 WIDTH, HEIGHT.
- 연결 상태/카운터: session.py의 Status.
- 장치 I/O 계약: session.py의 Display.
- 센서/프레임 전달: runtime.py의 Snapshot.
- 센서 값/시간 이력: sensors.py의 Telemetry, Point. Sampler만 변경 가능한 기준값을 소유한다.
- GPU 센서: gpu.py의 GpuSample과 NvidiaSampler. CPU 온도는 Telemetry.cpu_temperature.
- CPU 온도 수집은 cpu_temperature.py와 동봉 PowerShell probe가 소유한다. 클럭 수집은 하지 않는다.
- 공통 차트 위치/크기: render.py의 CHART_BOX. 각 카드 하단에 한 번만 렌더링한다.
- 카드 크기와 저장 필드: theme.py의 CARD_WIDTH/CARD_HEIGHT와 Theme(version 2).
- 지원 장치 식별: device.py의 SUPPORTED_IDS.

UI는 Theme를 replace하여 전달한다. worker에 mutable UI 상태를 공유하지 않는다.
미리보기와 USB 출력은 같은 render()를 사용한다. 선택 테두리는 PC 편집기에만 표시한다.

화면 방향은 Theme.rotate_180이 소유한다. render()와 Snapshot은 항상 정방향이다.
runtime이 장치 전송 직전에 전체 프레임을 회전하며 별도의 방향 상태를 만들지 않는다.
편집기의 포인터와 선택 테두리는 회전 설정과 관계없이 원래 배치 좌표를 사용한다.
rotate_180은 기본값 false이며 버전 1 테마 이전 시에도 방향을 유지한다.

- 창 표시 여부는 Tk window state, 트레이 준비 여부는 Tray.ready, 전체 종료는 MonitorApp.close가 소유한다. 숨김은 worker/power listener를 종료하지 않는다.

- 앱 아이콘 디자인: icon.app_icon. 트레이와 Tk iconphoto에서 재사용한다.

- 실행 소유권: instance.SingleInstance의 named mutex. 데이터 폴더나 창 제목에 의존하지 않는다. 두 번째 실행은 named event로 기존 창 열기만 요청한다.

- 최근 1분 I/O 사용량: Point.interval_seconds와 Telemetry.minute_bytes. 기존 history에서 유효 구간만 적분하며 렌더는 MB 표시만 담당한다.
- 디스크 및 네트워크 합산: Sampler가 장치별 카운터 차이를 합산해 속도와 Point를 만든다.
  빈 network_interface는 루프백을 제외한 활성 어댑터 전체 합산, 지정 이름은 단일 어댑터다.
  어댑터 목록 변경은 기준값만 갱신하고, 사용자가 측정 대상을 바꾸면 네트워크 누적량·이력을 초기화한다.

- 로그인 자동 실행 등록 여부는 HKCU Run의 Monitor35 값에서 읽는다. 테마에 복제하지 않는다. Windows 자체 시작 허용/차단 상태는 Windows가 소유한다.
