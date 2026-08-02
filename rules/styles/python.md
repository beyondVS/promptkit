# Python Coding Style Guide (Python 스타일 및 컨벤션 지침)

Google Python Style Guide 및 현대 파이썬 코딩 베스트 프랙티스 기반의 스타일 규격입니다. 기존 프로젝트에서는 설정 파일과 관례를 우선하며, 신규 프로젝트에서는 이 문서를 기본 프로필로 사용하고 formatter·linter 설정으로 기계적으로 확정하십시오.

---

## 🐍 1. 언어 활용 규칙 (Language Rules)

- **형식 검사 및 린팅 (Linting)**: `ruff` 또는 `pylint`를 활용해 문법 및 스타일 오류를 조기에 탐지하십시오.
- **순환 복잡도 통제 (McCabe Complexity Limit)**: 함수 1개의 순환 복잡도를 10 이하로 통제(Ruff `C901`, `max-complexity = 10`)하여 과도하게 길고 복잡한 중첩 분기문 작성을 엄격히 제어하십시오.
- **모듈 임포트 규칙 (Imports)**:
  - 패키지 및 모듈에는 `import x` 형식을 기본으로 사용합니다.
  - 서브모듈을 가져올 경우에만 `from x import y` 형식을 허용합니다.
  - 임포트는 **표준 라이브러리**, **서드파티 패키지**, **자체 프로젝트 모듈** 순서로 그룹화하여 빈 줄로 구분하십시오.
- **예외 처리 (Exceptions)**:
  - 파이썬 내장 예외 클래스 또는 명시적 커스텀 예외를 사용하고, 예외 종류를 지정하지 않는 bare `except:` 구문 사용을 엄격히 금지합니다.
- **전역 상태 제어 (Global State)**:
  - 가변(Mutable) 전역 상태 사용을 지양하십시오. 모듈 수준의 상수는 허용되며 `ALL_CAPS_WITH_UNDERSCORES` 명명 규칙을 적용합니다.
- **디폴트 인자 값 (Default Arguments)**:
  - 함수의 기본 인자 값으로 리스트(`[]`), 딕셔너리(`{}`) 등 가변 객체를 절대 직접 지정하지 마십시오. (`None`을 디폴트로 사용 후 내부 동적 할당)
- **조건문 진위 평가 (Truth Value Testing)**:
  - 빈 리스트나 문자열 체크 시 `if not my_list:`와 같은 암묵적 거짓 평가를 적극 활용하십시오.
  - `None` 검사 시에는 반드시 `if foo is None:` 또는 `if foo is not None:`을 사용하십시오.
- **타입 힌팅 (Type Annotations)**:
  - 모든 Public 함수, 메서드 및 모듈 API에는 Type Annotations를 명시적으로 작성하십시오.

---

## 🎨 2. 코드 스타일 및 포맷팅 (Style Rules)

- **들여쓰기 (Indentation)**: 탭(Tab) 사용을 금지하고, 4개의 공백(Spaces)을 사용합니다.
- **라인 길이 (Line Length)**: 한 줄당 최대 88자(Black / Ruff 표준) 또는 80자를 넘지 않도록 작성합니다.
- **빈 줄 (Blank Lines)**: 최상위 클래스 및 함수 정의 사이에는 2줄, 클래스 내부 메서드 정의 사이에는 1줄의 빈 줄을 둡니다.
- **문자열 포맷팅 (Strings)**:
  - 동적 문자열 구성 시 `f-string`을 우선적으로 사용합니다.
  - 따옴표 표기법은 팀 및 프로젝트 내에서 일관성을 유지하십시오.
- **Docstring 명세**:
  - 모든 Public 모듈, 클래스, 함수에는 Google 스타일의 `"""triple double quotes"""` Docstring을 작성합니다.
  - 구조: 한 줄 요약 -> 상세 설명 -> `Args:`, `Returns:`, `Raises:` 구획 명시.
- **주석 (Comments)**:
  - 코드의 동작 방식보다는 **"왜(Why)"** 작성되었는지 이유를 명시하십시오.
  - 해결이 필요한 작업에는 `TODO(username): 설명` 형식을 준수하십시오.

---

## 🏷️ 3. 명명 규칙 (Naming Conventions)

- **모듈 / 패키지 / 함수 / 변수 / 메서드**: `snake_case`
- **클래스 / 예외 클래스**: `PascalCase`
- **전역 상수**: `ALL_CAPS_WITH_UNDERSCORES`
- **내부 전용 멤버 (Internal Use)**: 캡슐화가 필요한 모듈/클래스 내부 멤버는 단일 선행 밑줄(`_private_var`)을 부여합니다.

---

## 🚀 4. 메인 엔트리포인트 (Main Protocol)

- 직접 실행 가능한 모든 파이썬 모듈은 메인 로직을 `main()` 함수로 추상화하고, `if __name__ == '__main__':` 블록에서 호출하도록 작성하십시오.
