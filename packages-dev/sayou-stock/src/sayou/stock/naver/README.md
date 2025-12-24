# NaverCrawler

네이버 뉴스에서 분야별 헤드라인 기사 수집
- 정치: https://news.naver.com/section/100
- 경제: https://news.naver.com/section/101
- 사회: https://news.naver.com/section/102
- 생활/문화: https://news.naver.com/section/103
- IT/과학: https://news.naver.com/section/105
- 세계: https://news.naver.com/section/104
- 뉴스검색 OpenAPI: https://openapi.naver.com/v1/search/news.json?query=xxxx&display=100


```
opendart/
├── __init__.py          # 공개 API 정의
├── client.py            # OpenDART HTTP 클라이언트
├── models.py            # 데이터 클래스 (DTO)
├── utils.py             # 유틸리티 함수 & 상수
├── crawler.py           # 통합 인터페이스 (Facade)
├── examples.py          # 사용 예시
└── parsers/
    ├── __init__.py
    ├── news.py          # Naver News 크롤링 파서
    └── market.py        # Naver Market API/크롤링 파서
```

```
NaverCrawler
├── NaverNews (뉴스 클래스)
│   ├── fetch (질문으로 Naver News API를 이용하여 뉴스 목록 조회)
│   └── parse (뉴스 목록으로 뉴스 상세 정보 조회)
├── NaverMarket (주식 클래스)
│   ├── fetch (기업 코드로 시작일과 종료일 사이 일별 시세를 조회)
│   ├── fetch_market_sum (현재 종목의 시가총액을 스크래핑하여 숫자로 반환)
│   ├── fetch_company_metadata (현재 종목의 시가총액을 스크래핑하여 숫자로 반환)
│   └── parse (...)
├── ...
├── check_gcp (GCP에서 Caching 정보 확인)
└── save_gcp (GCP에서 Caching 정보 저장)
```

## 증권정보 API사용 가능 여부
https://help.naver.com/service/5617/contents/176?lang=ko&osType=COMMONOS


네이버 증권에서 제공하는 국내 지수 및 종목, 해외 지수 및 종목, 환율, 원자재, 금리 등의 모든 정보는 각 콘텐츠 제공사와의 유료 계약에 의해 서비스됩니다.

네이버 증권은 해당 서비스 내에서만 정보를 제공할 수 있으며, 제3자에게 재배포하는 것은 금지되어 있습니다.

따라서 개인적인 투자 참고 목적 외에 데이터를 재가공하여 개인 프로그램 또는 웹 페이지에 사용하는 것은 금지되어 있습니다. 

지속적으로 불법적인 접근을 시도할 경우 서비스 이용이 제한될 수 있으니 참고하세요.