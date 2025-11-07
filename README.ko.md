# Sayou Data Platform

[English (README.md)](./README.md)
> LLM 데이터 파이프라인 구축을 위한 모듈형 오픈소스 프레임워크

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/sayouzone/sayou-fabric/LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/)

## 1. Core Architecture

`Sayou Data Platform`은 LLM 데이터 파이프라인을 **데이터 처리 흐름 단위**로 분리하여,
프로덕션 환경에 필요한 **안정성**, **경량성**, **확장성**을 제공합니다.

### 1.1. 경량·모듈형 구조 (Lightweight & Modular Packages)

`Sayou Data Platform`의 각 구성 요소(Connector, Chunking, RAG 등)는 **독립적인 Python 패키지**로 배포됩니다.

* 사용자는 `pip install sayou-chunking`처럼 **정확히 필요한 기능만** 설치할 수 있습니다.
* 각 라이브러리는 `sayou-core` 외의 의존성을 최소화하여, 불필요한 충돌을 줄이고 경량화된 컨테이너 구성을 지원합니다.

### 1.2. 일관된 3-Tier 아키텍처 (Interface → Default → Plugin)

모든 `sayou` 라이브러리는 일관된 3-Tier 설계를 기반으로 합니다.

* **Tier 1 – Interface:** 시스템의 표준 인터페이스 (BaseFetcher, BaseLLMClient 등)
* **Tier 2 – Default:** 공식 기본 구현체 (RecursiveCharacterSplitter, OpenAIClient 등)
* **Tier 3 – Plugin:** 사용자가 직접 구현하거나 확장할 수 있는 확장 계층 (사내 DB, 커스텀 LLM 등)

### 1.3. 명시적 구성과 조합형 워크플로우 (Explicit Composition)

`Sayou Data Platform`의 `RAGExecutor`는 암묵적 로직 대신, 사용자가 명시적으로 조립한 T1/T2/T3 노드(Router, Tracer, Fetcher, Generator)를 실행합니다. 이는 RAG 파이프라인의 모든 단계를 투명하게 디버깅하고 제어할 수 있음을 의미합니다.

## 2. Ecosystem Packages

`Sayou Data Platform`은 다음의 핵심 라이브러리들을 포함합니다.

| 패키지 (Package) | 상태 (Status) | 설명 (Description) |
| :--- | :--- | :--- |
| `sayou-core` | ![Beta](https://img.shields.io/badge/status-beta-brightgreen) | 모든 라이브러리의 공통 기반 (BaseComponent) |
| `sayou-connector` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터 '수집' (API, File, DB...) |
| `sayou-wrapper` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터를 '표준 Atom'으로 포장/검증 |
| `sayou-chunking` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 텍스트 '분할' |
| `sayou-refinery` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터 '정제' |
| `sayou-assembler` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터를 '구조화' (KG Builder...) |
| `sayou-loader` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터를 '저장' (VectorDB, File...) |
| `sayou-extractor` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 데이터를 '조회' (Retriever, Querier...) |
| `sayou-llm` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] LLM '어댑터' (OpenAI, Local LLM...) |
| `sayou-rag` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] RAG/Agent '워크플로우 실행기' |

## 3. Installation

필요한 라이브러리만 선택하여 설치합니다.

```bash
# 예제 1: RAG 파이프라인과 로컬 LLM(Hugging Face) 설치
pip install sayou-rag sayou-llm[transformers] sayou-extractor

# 예제 2: 데이터 수집 및 청킹 모듈만 설치
pip install sayou-connector sayou-chunking
```

각 라이브러리의 선택적 의존성(extras) 목록은 [공식 문서]를 참조하십시오.

## 4. Quick Start

## 5. Documentation

Sayou Data Platform의 아키텍처, 튜토리얼, T3 플러그인 개발 가이드 및 전체 API 레퍼런스는 **공식 문서**에서 제공됩니다.

## 6. Contributing

기여는 이슈(issues) 또는 풀 리퀘스트(pull requests)를 통해 언제든지 환영합니다. 주요 변경 사항에 대해서는 먼저 이슈를 열어 논의해 주시기 바랍니다.

**Git 브랜치 전략**

- `main`: 프로덕션 릴리즈 브랜치 (직접 커밋 금지)
- `develop`: 개발 브랜치 (모든 PR은 이 브랜치를 대상으로 함)
- `feature/`, `fix/`: develop에서 분기하는 임시 작업 브랜치

**Workflow:**

```Bash
# 1. develop 브랜치 최신화
git checkout develop
git pull origin develop

# 2. 새 피처 브랜치 생성
git checkout -b feature/add-semantic-chunker

# 3. 커밋 및 푸시
git commit -m "feat(chunking): Add T2 SemanticChunker"
git push origin feature/add-semantic-chunker
```

## 7. License

Sayou Data Platform(sayou-fabric)은 Apache License 2.0을 따릅니다.