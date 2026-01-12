# KisratingCrawler

- 신용등급 > 등급통계 > 등급별금리스프레드: https://www.kisrating.com/ratingsStatistics/statics_spread.do

```
kisrating/
├── __init__.py          # 공개 API 정의
├── client.py            # Kisrating HTTP 클라이언트
├── models.py            # 데이터 클래스 (DTO)
├── utils.py             # 유틸리티 함수 & 상수
├── crawler.py           # 통합 인터페이스 (Facade)
└── parsers/
│   ├── __init__.py
│   ├── html_extractor.py    # HTML 추출 파서
│   └── statistics.py        # Kisrating API/크롤링 파서
└── utils/
    ├── storage.py          # 저장 파서
    └── utils.py            # 유틸리티 함수 & 상수
```

## Tests

```python
from sayou.stock.kisrating import KisratingCrawler

crawler = KisratingCrawler()

# 신용등급 등급통계 조회
start_date='2025-01-01'
end_date='2025-12-31'
code = "005930"

data = crawler.statistics(start_date=start_date, end_date=end_date)
print(data)

# 신용등급 등급통계 조회 (엑셀로 저장)
df_main_prices = crawler.statistics_excel(code)
print(df_main_prices)
```