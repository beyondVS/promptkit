---
name: python-ecosystem-kb
description: 파이썬 및 Django 생태계의 검증된 대표 후보군을 우선 탐색하고, 최신 유지보수·호환성 검증을 거쳐 패키지를 추천할 때 사용합니다. (Awesome Python, Awesome Django, WikiDocs 14021 연계)
---

# Python Ecosystem Knowledge Base Skill

본 스킬은 파이썬 및 Django 생태계의 널리 쓰이는 패키지 후보군과 기술 스택을 온디맨드(Read-on-Demand)로 탐색하는 가이드입니다. 카탈로그는 최신성의 보증이 아니라 마이너한 패키지보다 검증된 후보군을 먼저 검토하기 위한 인덱스입니다.

> [!IMPORTANT]
> **패키지 선정의 최종 검증 수칙 (PyPI & Web Search Fallback)**
> - 본 스킬에서 제공하는 큐레이션 카탈로그(Awesome Python, Awesome Django, WikiDocs 14021)는 널리 검증된 대표적인 패키지들을 빠르게 탐색하기 위한 **1차 레퍼런스 가이드**입니다.
> - 본 스킬의 마크다운 카탈로그 요약만으로 세부 내용이 부족한 경우, 각 항목에 표기된 **위키독스 직링크 URL(`https://wikidocs.net/<page_id>`)로 웹 접근하여 2차 상세 내용 및 예제**를 탐색하십시오.
> - 최종적으로는 **PyPI(`pypi.org`), 최신 웹 검색, 패키지의 유효성 및 최신 유지보수 상태**를 확인하여 프로젝트에 가장 적합한 최신 패키지를 선별·추천해야 합니다.
> - 최종 추천에는 지원 Python·Django 버전, 라이선스, 보안 이력, 전이 의존성, 프로젝트의 기존 도구와의 호환성도 함께 확인해야 합니다.

## 🎯 온디맨드 패키지 탐색 가이드 (On-Demand Retrieval)

패키지 추천 또는 생태계 조회가 필요한 경우, 분야별 탐색 경로를 준수하십시오:

### 1. Awesome Python 글로벌 생태계 탐색
* **원격 수집 URL**: `https://raw.githubusercontent.com/vinta/awesome-python/main/README.md`
* **사용법**: 웹 Content Fetch 도구를 통해 위 Raw URL의 최신 마크다운을 직접 읽어 필요한 패키지 카테고리를 탐색하십시오.

### 2. Awesome Django 웹 프레임워크 생태계 탐색
* **원격 수집 URL**: `https://raw.githubusercontent.com/wsvincent/awesome-django/main/README.md`
* **사용법**: 웹 Content Fetch 도구를 통해 위 Raw URL의 최신 마크다운을 직접 읽어 필요한 Django 서드파티 패키지를 탐색하십시오.

### 3. WikiDocs 파이썬 생태계 지식 베이스 탐색
* **로컬 자원 경로**: `resources/wikidocs-14021.md`
* **사용법**: 에이전트 내장 파일 텍스트 검색 도구(Grep / File Search)를 사용하여 `resources/wikidocs-14021.md` 자원 파일 내의 기술 키워드를 온디맨드로 부분 검색하십시오. 카탈로그 전체를 컨텍스트에 넣지 말고 필요한 범주와 항목만 읽으십시오. 항목별 수록된 위키독스 URL(`https://wikidocs.net/<id>`)로 상세 페이지 접근이 가능합니다.
