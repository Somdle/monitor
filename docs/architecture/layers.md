# Layers and Ownership

| Module | Owns |
|---|---|
| theme | 불변 Widget/Theme 모델, 유효성 검사, JSON 저장 |
| render | Pillow 화면 렌더링, 글꼴 캐시 |
| device | 장치 검색, smartscreen-driver 확장, 제한 시간 있는 전송 |
| session | Display protocol, 복구 상태, 마지막 성공 프레임, 차분 전송 |
| runtime | 센서 수집, worker 수명, 최신 snapshot 전달 |
| power | Windows WM_POWERBROADCAST 수신 및 절전/복귀 알림 |
| app | Tk 편집기, 사용자 액션, undo, 오류 표시 |
| logging_setup | 로컬 회전 JSON 로그 |
| __main__ | CLI 조립, GUI/스모크 실행 |

새 화면 종류를 추측해 추가하지 않는다. 현재 장치의 serial ID만 허용한다.
