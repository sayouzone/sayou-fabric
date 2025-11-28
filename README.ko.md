<div align='center'>

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/sayou_logo.png?raw=true" width="250">

# Sayou Fabric

[![PyPI](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue&label=pypi%20package)](https://pypi.org/project/sayou-brain/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blueviolet.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://static.pepy.tech/badge/sayou-rag?color=orange)](https://pepy.tech/project/sayou-rag)
[![GitHub stars](https://img.shields.io/github/stars/sayouzone/sayou-fabric.svg)](https://github.com/sayouzone/sayou-fabric/stargazers)

_엔터프라이즈 RAG 파이프라인 구축을 위한 데이터 중심(Data-Centric) 프레임워크_

</div>

[English (README.md)](./README.md)

---

## 1. Philosophy

**Sayou Fabric**은 하나의 단순한 전제에서 출발했습니다.
**"RAG(검색 증강 생성)의 품질을 결정하는 것은 모델이 아니라, 데이터의 구조다."**

LLM 체이닝에 집중하는 기존 프레임워크들과 달리, Sayou Fabric은 **데이터의 생애 주기**에 집중합니다. 복잡한 RAG 파이프라인을 **10개의 원자 단위**로 분해하여, 원본 데이터가 LLM에 도달하기 전에 완벽하게 정제되고, 구조화되고, 지식 그래프로 조립되도록 보장합니다.

### 1.1. Structure-First Architecture
우리는 텍스트를 단순히 자르지 않고 이해합니다. 헤더, 표(Table), 코드 블록과 같은 문서의 계층 구조를 보존하고 엄격한 스키마를 강제함으로써, RAG의 고질적인 문제인 문맥 손실과 환각 현상을 원천 차단합니다.

### 1.2. The 3-Tier Design Pattern
생태계 내의 모든 라이브러리는 일관된 **Interface-Template-Plugin** 패턴을 따르며, 이는 안정성과 무한한 확장성을 동시에 보장합니다.
* **Tier 1 (Interface):** 변하지 않는 계약 (Contract).
* **Tier 2 (Template):** 즉시 사용 가능한 표준 구현체 (Batteries-included).
* **Tier 3 (Plugin):** 특정 벤더나 로직을 위한 확장 영역.

---

## 2. The Ecosystem

Sayou Fabric은 서로 독립적이면서도 유기적으로 연결되는 라이브러리들로 구성되어 있습니다.

| 단계 | 패키지 | 설명 |
| :--- | :--- | :--- |
| **0. Core** | `sayou-core` | 기본 컴포넌트, 로깅, 데코레이터 등 공통 기반. |
| **1. Ingest** | `sayou-connector` | 파일, 웹, API, DB 등 다양한 소스에서 원시 데이터를 수집. |
| **2. Parse** | `sayou-document` | PDF, DOCX 등의 좌표와 스타일을 보존하는 High-Fidelity 파싱. |
| **3. Refine** | `sayou-refinery` | 복잡한 JSON 구조를 LLM 친화적인 표준 Markdown으로 정규화. |
| **4. Split** | `sayou-chunking` | 문맥 인식 청킹. 표나 코드 블록 등 원자적 요소를 보호하며 분할. |
| **5. Wrap** | `sayou-wrapper` | 모든 데이터를 사내 표준 스키마(`SayouNode`)로 변환 및 검증. |
| **6. Build** | `sayou-assembler` | 노드 간의 부모-자식 관계를 연결하여 인메모리 지식 그래프 조립. |
| **7. Load** | `sayou-loader` | 완성된 그래프를 파일, VectorDB, GraphDB에 안전하게 적재. |
| **8. Query** | `sayou-extractor` | 벡터 검색과 그래프 탐색을 결합한 하이브리드 검색 수행. |
| **9. Gen** | `sayou-llm` | 다양한 LLM(OpenAI, Local)을 위한 통합 어댑터 계층. |
| **10. Main** | `sayou-brain` | 전체 파이프라인을 총괄하고 제어하는 관제탑 (`StandardPipeline`). |

---

## 3. Installation

오케스트레이터 패키지를 설치하면 전체 제품군을 한 번에 사용할 수 있습니다.

```bash
pip install sayou-brain
```

필요한 컴포넌트만 개별적으로 설치하는 것도 가능합니다.

```bash
pip install sayou-chunking sayou-document
```

---

## 4. Quick Start

`sayou-brain`의 `StandardPipeline`은 복잡한 내부 모듈을 추상화한 퍼사드(Facade) 역할을 합니다. 입력 데이터의 타입을 자동으로 감지하여 최적의 경로로 처리합니다.

### Step 1: Initialize the Brain

```python
from sayou.brain.pipeline.standard import StandardPipeline

# 오케스트레이터 초기화 (하위 파이프라인 자동 로드)
brain = StandardPipeline()
brain.initialize()
```

### Step 2: Ingest Data (ETL)

파일 경로나 URL만 입력하세요. 연결, 파싱, 정제, 청킹, 포장, 조립, 적재까지의 모든 과정을 자동으로 수행합니다.

```python
# 예제: PDF 파일 적재
# 지식 그래프를 생성하고 'knowledge_graph.json'에 저장합니다.
result = brain.ingest(
    source="./reports/financial_q1.pdf",
    strategy="local_scan",
    save_to="knowledge_graph.json"
)

print(f"Ingestion Complete: {result['status']}")
print(f"Total Nodes Created: {result['total_nodes']}")
```

### Step 3: Ask Questions (Inference)

구조화된 지식을 바탕으로 질문합니다.

```python
# 적재된 지식 그래프를 기반으로 답변 생성
answer = brain.ask(
    query="1분기 순이익은 얼마인가요?",
    load_from="knowledge_graph.json"
)

print(f"Answer: {answer}")
```

---

## 5. Documentation

아키텍처 가이드, API 레퍼런스, 커스텀 플러그인 개발 방법 등 자세한 내용은 **[공식 문서](https://sayouzone.github.io/sayou-fabric/)**에서 확인하실 수 있습니다.

* [아키텍처 가이드](https://sayouzone.github.io/sayou-fabric/architecture)
* [플러그인 개발 가이드](https://sayouzone.github.io/sayou-fabric/guides/plugins)
* [API 레퍼런스](https://sayouzone.github.io/sayou-fabric/api)

---

## 6. Contributing

Sayou Fabric은 기여를 환영합니다!
모듈형 설계 덕분에 여러분은 특정 부분만 쉽게 확장할 수 있습니다.
1.  새로운 **Connector Plugin** 추가 (예: Notion, Slack 연동).
2.  **Document Parser** 개선 (예: HWP 지원).
3.  더 똑똑한 **Assembler Strategy** 제안.

Pull Request를 보내기 전에 [기여 가이드라인](CONTRIBUTING.md)을 확인해 주세요.

---

## 7. License

Apache 2.0 License © 2025 **Sayouzone**