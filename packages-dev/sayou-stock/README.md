# Sayou Stock


패키지 구조

```
src
├──sayou/stock
│   ├── edgar/
│   │   ├── __init__.py          # 공개 API 정의
│   │   ├── client.py            # SEC EDGAR HTTP 클라이언트
│   │   ├── models.py            # 데이터 클래스 (DTO)
│   │   ├── utils.py             # 유틸리티 함수 & 상수
│   │   ├── crawler.py           # 통합 인터페이스 (Facade)
│   │   ├── examples.py          # 사용 예시
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── form_10k.py      # 10-K/10-Q 파서
│   │       ├── form_8k.py       # 8-K 파서
│   │       ├── form_13f.py      # 13F 파서
│   │       └── def14a.py        # DEF 14A 파서
│   ├── fnguide/
│   │   ├── __init__.py          # 공개 API 정의
│   │   ├── client.py            # OpenDART HTTP 클라이언트
│   │   ├── models.py            # 데이터 클래스 (DTO)
│   │   ├── utils.py             # 유틸리티 함수 & 상수
│   │   ├── crawler.py           # 통합 인터페이스 (Facade)
│   │   ├── examples.py          # 사용 예시
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── company.py            # FnGuide 기업개요 파서
│   │       ├── comparison.py         # FnGuide 경쟁사비교 파서
│   │       ├── consensus.py          # FnGuide 컨센서스 파서
│   │       ├── dart.py               # FnGuide 금감원공시 파서
│   │       ├── disclosure.py         # FnGuide 거래소공시 파서
│   │       ├── finance_ratio.py      # FnGuide 재무비율 파서
│   │       ├── finance.py            # FnGuide 재무제표 파서
│   │       ├── industry_analysis.py  # FnGuide 업종분석 파서
│   │       ├── invest.py             # FnGuide 투자지표 파서
│   │       ├── main.py               # FnGuide 메인(Snapshot) 파서
│   │       └── share_analysis.py     # FnGuide 지분분석 파서
│   ├── naver/
│   │   ├── __init__.py          # 공개 API 정의
│   │   ├── client.py            # OpenDART HTTP 클라이언트
│   │   ├── models.py            # 데이터 클래스 (DTO)
│   │   ├── utils.py             # 유틸리티 함수 & 상수
│   │   ├── crawler.py           # 통합 인터페이스 (Facade)
│   │   ├── examples.py          # 사용 예시
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── news.py          # Naver News 크롤링 파서
│   │       └── market.py        # Naver Market API/크롤링 파서
│   ├── opendart/
│   │   ├── __init__.py          # 공개 API 정의
│   │   ├── client.py            # OpenDART HTTP 클라이언트
│   │   ├── models.py            # 데이터 클래스 (DTO)
│   │   ├── utils.py             # 유틸리티 함수 & 상수
│   │   ├── crawler.py           # 통합 인터페이스 (Facade)
│   │   ├── examples.py          # 사용 예시
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── document.py        # 문서 API 파서
│   │       ├── document_viewer.py # 문서 뷰어 API 파서
│   │       ├── disclosure.py      # 공시정보 API 파서
│   │       ├── finance.py         # 정기보고서 재무정보 API 파서
│   │       ├── material_facts.py  # 주요사항보고서 주요정보 API 파서
│   │       ├── ownership.py       # 지분공시 종합정보 API 파서
│   │       ├── registration.py    # 증권신고서 주요정보 API 파서
│   │       └── reports.py         # 정기보고서 주요정보 API 파서
│   └── yahoo/
│       ├── __init__.py          # 공개 API 정의
│       ├── client.py            # OpenDART HTTP 클라이언트
│       ├── models.py            # 데이터 클래스 (DTO)
│       ├── utils.py             # 유틸리티 함수 & 상수
│       ├── crawler.py           # 통합 인터페이스 (Facade)
│       ├── examples.py          # 사용 예시
│       └── parsers/
│           ├── __init__.py
│           ├── analysis.py      # 분석 API 파서
│           ├── chart.py         # 시세정보 API 파서
│           ├── fundamentals.py  # 재무정보 API 파서
│           ├── quote.py         # 기업정보 API 파서
│           └── news.py          # 뉴스 API 파서
├── docs/
├── tests/
│   ├── examples_edgar.py          # Edgar 사용 예시
│   ├── examples_fnguide.py        # FnGuide 사용 예시
│   ├── examples_naver.py          # Naver 사용 예시
│   ├── examples_opendart.py       # OpenDART 사용 예시
│   └── examples_yahoo.py          # Yahoo 사용 예시
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.cfg
└── setup.py
```