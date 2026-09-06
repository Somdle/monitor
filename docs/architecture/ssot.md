# SSOT

- 테마의 필드/범위/버전: theme.py의 Widget와 Theme.
- 화면 크기: theme.py의 WIDTH, HEIGHT.
- 연결 상태/카운터: session.py의 Status.
- 장치 I/O 계약: session.py의 Display.
- 센서/프레임 전달: runtime.py의 Snapshot.
- 지원 장치 식별: device.py의 SUPPORTED_IDS.

UI는 Theme를 replace하여 전달한다. worker에 mutable UI 상태를 공유하지 않는다.
미리보기와 USB 출력은 같은 render()를 사용한다. 선택 테두리는 PC 편집기에만 표시한다.

화면 방향은 Theme.rotate_180이 소유한다. render()와 Snapshot은 항상 정방향이다.
runtime이 장치 전송 직전에 전체 프레임을 회전하며 별도의 방향 상태를 만들지 않는다.
편집기의 포인터와 선택 테두리는 회전 설정과 관계없이 원래 배치 좌표를 사용한다.
rotate_180은 버전 1의 선택 필드(default false)이며 기존 테마의 방향을 유지한다.
