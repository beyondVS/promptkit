# Nginx Deployment & Proxy Rules (Nginx 리버스 프록시 및 서버 수칙)

Nginx를 Reverse Proxy, Web Server, SSL Termination 용도로 배포할 때 적용되는 아키텍처 및 보안 설정 지침입니다.

---

## 🌐 1. 프록시 헤더 필수 설정 (Proxy Headers)

- **클라이언트 식별 헤더 누락 금지**:
  - 백엔드(FastAPI, Node.js, Django 등)로 요청을 전파할 때, 클라이언트의 실제 IP와 프로토콜이 유지되도록 아래 헤더를 `proxy_pass`와 함께 필수로 선언하십시오:
    ```nginx
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    ```

---

## 🔒 2. 보안 및 버퍼/타임아웃 최적화 (Security & Buffers)

- **서버 버전 정보 숨김**:
  - 보안 취약점 노출을 막기 위해 `server_tokens off;` 옵션을 반드시 포함하십시오.
- **클라이언트 바디 용량 제한 (`client_max_body_size`)**:
  - 무제한 업로드로 인한 DoS 공격을 방지하기 위해 서비스에 알맞은 용량(예: `client_max_body_size 10M;`)을 지정하십시오.
- **보안 헤더 주입**:
  - 기본 HTTP 응답 헤더에 `X-Frame-Options SAMEORIGIN`, `X-Content-Type-Options nosniff`, `X-XSS-Protection "1; mode=block"`을 추가하십시오.

---

## ⚡ 3. Static File Serving & Gzip/Brotli 압축

- **정적 자원 캐싱 규칙**:
  - Static 파일(`images`, `css`, `js`) 서빙 시 `expires 30d;` 및 `add_header Cache-Control "public, no-transform";`을 지정하십시오.
- **Gzip/Brotli 압축 활성화**:
  - 텍스트 기반 자원(`text/plain`, `text/css`, `application/json`, `application/javascript`)의 네트워크 전송량 절감을 위해 `gzip on;` 및 최소 크기(`gzip_min_length 1000;`)를 활성화하십시오.
