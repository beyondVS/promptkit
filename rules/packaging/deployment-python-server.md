# Python Application Server Rules (Gunicorn + Uvicorn 배포 규칙)

Python 웹 애플리케이션(FastAPI, Litestar, Django, Flask 등)을 프로덕션 환경에 Gunicorn 및 Uvicorn 프로세스 매니저로 실행할 때 적용되는 규칙입니다.

---

## 🦄 1. Gunicorn + UvicornWorker 실행 표준

- **Gunicorn을 Master Process Manager로 활용**:
  - 프로덕션 환경에서는 `uvicorn` 단독 실행 대신, 프로세스 관리/워커 재시작/메모리 관리가 뛰어난 `gunicorn`을 마스터 프로세스로 사용하고 `-k uvicorn.workers.UvicornWorker` 워커 클래스를 연결하십시오.

---

## ⚙️ 2. Worker 산출 공식 및 프로세스 설정

- **워커 수 산출 공식**:
  - 기본 워커 수(`workers`)는 CPU 코어 수에 맞추어 산출하십시오:
    - 공식: `(2 * CPU 코어 수) + 1`
  - I/O 지연이 많은 서비스의 경우 아키텍처에 맞게 조정하되, 메모리 초과(OOM)가 발생하지 않도록 상한선을 관리하십시오.
- **Worker Timeout & Keepalive**:
  - HTTP Keep-alive 시간(`keepalive 5`) 및 작업 수용 타임아웃(`timeout 60` ~ `120`)을 명시하여 교착 상태(Deadlock) 워커를 자동으로 수거하게 하십시오.

---

## 🔄 3. Graceful Shutdown 및 무중단 배포

- **Graceful Timeout 설정**:
  - 서버 중지 시 진행 중인 요청을 정상 처리하고 종료할 수 있도록 `graceful_timeout 30` 옵션을 지정하십시오.
- **HUP 시그널 재로딩**:
  - 설정 또는 소스 코드 변경 후 워커 프로세스를 재시작할 때는 `kill -HUP [gunicorn_pid]` 시그널을 사용하여 무중단 재로딩(Graceful Reload)을 수행하십시오.
