# C# Coding Style Guide (C# 스타일 및 컨벤션 지침)

Google C# Style Guide 기반의 관용적 .NET 코딩 규격입니다.

---

## 🏷️ 1. 명명 규칙 (Naming Conventions)

- **`PascalCase`**: 클래스, 메서드, 상수, 속성(Property), 네임스페이스, Public 필드
- **`_camelCase`**: Private 및 Protected 클래스 내부 필드 (선행 밑줄 적용)
- **`camelCase`**: 지역 변수 및 메서드 매개변수
- **인터페이스 (Interfaces)**: `I` 접두사 사용 (`IMyService`)
- **제네릭 타입 파라미터**: `T` 접두사 사용 (`TValue`, `TKey`)

---

## 📐 2. 포맷팅 및 구조 (Formatting & Structure)

- **들여쓰기**: 2공백 들여쓰기 (탭 사용 금지)
- **한 줄 길이**: 100자 제한
- **선언 순서**:
  1. Static, Const, Readonly 필드
  2. 일반 필드 및 속성 (Properties)
  3. 생성자 (Constructors)
  4. 메서드 (Methods)
  - 접근 수준 정렬: Public -> Internal -> Protected -> Private

---

## ⚡ 3. 언어 기능 규칙 (Language Features)

- **`var` 사용**: 우변에서 타입을 명확히 알 수 있는 경우(`var list = new List<string>();`)에 선호하되, 원시 타입 선언 시에는 명시적 타입을 권장합니다.
- **Null 연산자**: 널 조건 연산자(`?.`) 및 널 병합 연산자(`??`)를 적극 활용하십시오.
- **문자열 보간**: `$"Hello, {name}"` 형태의 문자열 보간법을 활용하십시오.
- **접근 수식어 명시**: 생략하지 말고 `public`, `private` 등 접근 수식어를 명시적으로 작성하십시오.
- **컬렉션 인터페이스 반환**: 입력 매개변수에는 가능한 가치 제약이 큰 컬렉션 타입(`IEnumerable<T>`, `IReadOnlyList<T>`)을 사용하십시오.
