# Review Checklist

- 소유권 및 AST import 검사 통과.
- 제한 시간과 frame transaction 복구 정책이 session/device 사이에 중복되지 않음.
- UI thread에서 센서/USB I/O 없음.
- 실패 시 이전 프레임 폐기 및 전체 다시 그리기.
- 실제 장치 ACK가 없다는 한계를 전송 성공과 구분.
- 테마 검증 실패 시 기존 데이터 보존.
- 테스트, lint, format, mypy, 빌드 및 smoke 결과 기록.
- 실기기/절전/스크린리더 미검증 항목을 통과로 보고하지 않음.
- 원본 설치/테마/전원 설정과 시작 프로그램을 변경하지 않음.
