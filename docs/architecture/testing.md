# Testing

AGENTS.md에 실행 명령을 모아 둔다. tests/test_session.py는 외부 Display만 fake로 대체한다.
검증: 최초 전체 전송, 변경 영역 전송, 미변경 생략, 재시도 간격, 실패 후 최신 전체 프레임,
COM 번호 변경, 복귀 시 재연결, 밝기 재적용, 주기적 전체 갱신.
test_device.py는 외부 Serial 경계에서 timeout/부분 write가 실패로 전파되는지 확인한다.
test_theme.py는 저장/읽기, 잘못된 입력 보존, 렌더링 변화를 검증한다.

UI 검증은 실제 창에서 드래그, 저장, 실행 취소, 오류 표시를 확인한다.
실기기에서는 기존 UsbMonitor 종료 후 --connect --smoke 30으로 전송한다.
실제 절전/복귀 및 USB 재삽입은 사용자와 함께 수행하며 모의 테스트와 구분해 기록한다.
화면이 실제로 보이는지와 센서가 갱신되는지는 사용자가 물리 화면에서 확인해야 한다.

test_desktop.py는 실제 Tk 창 수명을 끝까지 기다려 다음 테스트에 Tcl 인스턴스를 남기지 않는다.
네이티브 절전/복귀 메시지 전달 및 중복 복귀 알림 무시를 검증한다.
test_runtime.py는 센서 실패, 최신 snapshot 유지, worker 절전 중 전송 중지와 복귀를 검증한다.
