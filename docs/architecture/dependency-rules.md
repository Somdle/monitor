# Dependency Rules

- render → theme, sensors
- runtime → device, render, session, theme, sensors
- app → power, render, runtime, theme, sensors
- __main__ → app, device, logging_setup, runtime, theme
- theme, sensors, device, power, session, logging_setup은 다른 프로젝트 모듈에 의존하지 않는다.

tests/test_architecture.py가 허용된 import를 AST로 검사한다. 이 방향은 순환을 허용하지 않는다.
장치 클래스는 Display protocol의 실행 구현이며 런타임에서 조립한다.
smartscreen-driver의 공식 Rev A 클래스/명령을 사용한다. 인코딩 코드를 복제하지 않는다.
BoundedRevA의 override는 upstream이 timeout을 삼키거나 같은 포트를 재시도하지 못하게 하는 명시적 확장이다.
