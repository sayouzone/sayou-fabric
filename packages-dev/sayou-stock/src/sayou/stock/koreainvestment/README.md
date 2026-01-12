# KoreainvestmentCrawler

- 한국투자증권 Open API 포털: https://apiportal.koreainvestment.com/intro
- Open API 개요: https://apiportal.koreainvestment.com/apiservice-summary
- open-trading-api: https://github.com/koreainvestment/open-trading-api

```
koreainvestment/
├── __init__.py          # 공개 API 정의
├── client.py            # Open API HTTP 클라이언트
├── models.py            # 데이터 클래스 (DTO)
├── utils.py             # 유틸리티 함수 & 상수
├── crawler.py           # 통합 인터페이스 (Facade)
└── parsers/
    ├── __init__.py
    ├── news.py          # Naver News 크롤링 파서
    └── market.py        # Naver Market API/크롤링 파서
```

## Tests

```python
from sayou.stock.koreainvestment import KoreainvestmentCrawler

kis_app_key = "your_app_key"
kis_app_secret = "your_app_secret"
crawler = KoreainvestmentCrawler(app_key, app_secret)

# 신용등급 등급통계 조회
start_date='2025-01-01'
end_date='2025-12-31'
code = "005930"

data = crawler.statistics(start_date=start_date, end_date=end_date)
print(data)

# 신용등급 등급통계 조회 (엑셀로 저장)
df_main_prices = crawler.statistics_excel(code)
print(df_main_prices)

# Naver 기업 정보 조회
metadata = crawler.company_metadata(code)
print(metadata)

# Naver 뉴스 카테고리별 검색
category_news = crawler.category_news()
print(category_news)

# Naver 뉴스 검색
news = crawler.news(query="삼성전자", display=10)
print(news)
```