# Quickstart Validation Guide: Monorepo & Django PostgreSQL Setup

## Overview

본 가이드는 Day 01 피처 구현 완료 후 전체 모노레포 가상환경 동기화, Django 서버 구동 및 PostgreSQL 연결 검증을 빠르게 실행할 수 있는 절차를 안내합니다.

---

## 1. Prerequisites

- Python 3.13 이상 설치
- `uv` 패키지 매니저 설치
- 실행 중인 PostgreSQL 16+ 인스턴스 (또는 Docker PostgreSQL 컨테이너)

---

## 2. Setup & Synchronization

### Step 1: `uv` 모노레포 가상환경 동기화
```bash
uv sync
```
- **기대 결과**: 루트에 `.venv` 가상환경이 구축되고 `pyproject.toml`에 선언된 패키지가 설치됨.

### Step 2: 환경 변수 설정
```bash
cp .env.example .env
```
- `.env` 파일 내 PostgreSQL 접속 정보(`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`)를 본인 환경에 맞춰 조정합니다.

---

## 3. Execution & Verification Commands

### Step 3: DB 연결 및 시스템 체크
```bash
uv run python apps/server/manage.py check --database default
```
- **기대 결과**: `System check identified no issues (0 silenced).`

### Step 4: Django 데이터베이스 마이그레이션
```bash
uv run python apps/server/manage.py migrate
```
- **기대 결과**: Django 기본 앱 스키마 마이그레이션 성공.

### Step 5: 하네스 검증 (Lint / Format / Type / Test)
```bash
# 린트 및 포맷 검사
uv run ruff check ; uv run ruff format --check

# 정적 타입 검사
uv run mypy .

# 유닛 테스트 실행
uv run pytest
```
- **기대 결과**: 모든 명령어 0 exit code로 정상 완료 (오류 0개).
