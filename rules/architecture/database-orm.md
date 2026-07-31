# Database & ORM General Rules (범용 DB & ORM 설계 및 마이그레이션 규칙)

프레임워크나 ORM 종류(Prisma, SQLAlchemy, TypeORM, Django ORM 등)에 구애받지 않고 적용되는 범용 데이터베이스 설계, 인덱싱 및 마이그레이션 안전 규칙입니다.

---

## ⚠️ 1. 파괴적 마이그레이션 2단계 절차 (Non-Destructive Schema Migration)

- **즉시 컬럼 DROP 금지 (Zero Downtime Principle)**:
  - 컬럼 삭제나 이름 변경 시 단일 마이그레이션으로 즉시 `DROP COLUMN`을 실행하지 마십시오. 서비스 중단 및 구버전 애플리케이션의 런타임 에러를 유발합니다.
- **2단계 Deprecation 절차 준수**:
  - **1단계 (Add/Deprecate)**: 신규 컬럼 추가 또는 Nullable 처리 후 코드 배포 및 데이터 이관 수행
  - **2단계 (Cleanup)**: 구버전 코드 및 데이터 참조가 완전히 제거된 후 별도의 마이그레이션으로 구 컬럼 DROP

---

## 🔍 2. 인덱싱(Indexing) 및 쿼리 성능 원칙

- **외래키(FK) 및 검색 필드 인덱스 필수**:
  - 관계형 DB의 외래키(FK) 컬럼, 자주 조인되는 필드 및 `WHERE` 조건절에 빈번히 포함되는 검색 필드에는 반드시 인덱스를 생성하십시오.
- **복합 인덱스(Composite Index) 순서 지침**:
  - 복합 인덱스 지정 시 카디널리티(Cardinality, 고유값 개수)가 높은 컬럼을 좌측(Leading Column)에 먼저 배치하십시오.
- **N+1 쿼리 사전 예방**:
  - ORM 사용 시 반복문 내 개별 쿼리 조회를 금지하고, Eager Loading(`JOIN`, `select_related`, `include` 등)을 사전 정의하십시오.

---

## 🔒 3. 데이터 무결성 및 트랜잭션 수칙

- **DB 수준의 제약 조건 (Constraints)**:
  - 데이터 무결성을 애플리케이션 코드에만 의존하지 마십시오. `NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY` 제약 조건을 DB 스키마 레벨에 엄격히 정의하십시오.
- **트랜잭션 바운더리 최소화**:
  - `@transaction` 블록 또는 DB 트랜잭션 범위 내에서 외부 API 호출, 파일 I/O 등 느린 작업을 수행하지 마십시오. DB 커넥션 풀 고갈을 초래합니다.
- **Down 마이그레이션 (Rollback) 검증**:
  - 마이그레이션 작성 시 롤백용 `down` 스크립트가 정상 동작하는지 반드시 테스트하고 버전 관리에 포함시키십시오.
