## Yahoo Finance API

패키지 구조

```
yahoo/
├── __init__.py          # 공개 API 정의
├── client.py            # OpenDART HTTP 클라이언트
├── models.py            # 데이터 클래스 (DTO)
├── utils.py             # 유틸리티 함수 & 상수
├── crawler.py           # 통합 인터페이스 (Facade)
├── examples.py          # 사용 예시
└── parsers/
    ├── __init__.py
    ├── analysis.py      # 분석 API 파서
    ├── chart.py         # 시세정보 API 파서
    ├── fundamentals.py  # 재무정보 API 파서
    ├── holders.py       # 소유주 API 파서
    ├── market.py        # 시장정보 API 파서
    ├── news.py          # 뉴스 API 파서
    ├── options.py       # 옵션 API 파서
    ├── profile.py       # 프로필 API 파서
    ├── quote.py         # 기업정보 API 파서
    ├── statistics.py    # 통계 API 파서
    └── summary.py       # 요약 API 파서
```

https://developer.yahoo.com/api/
https://www.yahoo.com/

#### Official Yahoo APIs
For general Yahoo news outside of the finance context, there is no official public API. Yahoo does maintain a Yahoo Developer Network with APIs primarily focused on other services like fantasy sports, which use the OAuth protocol for authentication.

#### Alternative Approaches

If you need general news or are unable to use yfinance, consider these alternatives:
- **Web Scraping:** You could use Python libraries like requests and BeautifulSoup to scrape news headlines directly from Yahoo News webpages, though this is less reliable than an API and subject to changes in the website's structure.
- **Third-Party News APIs:** Use a dedicated, reliable news API (e.g., Apify's Yahoo Finance scraper or general news APIs like Alpha Vantage or Finnhub) that may offer a Yahoo News data scraper or a broad range of news sources. These services often involve a subscription or usage limits.


## Tests

#### YahooCrawler

```python
from sayou.stock.yahoo import YahooCrawler

crawler = YahooCrawler()
ticker = "AAPL"

# Yahoo 기업 캘린더 조회
data = crawler.calendar(ticker)
print(data)

# 기업 수익 추정치 (Earning Estimate) 조회
data = crawler.earnings_estimate(ticker)
print(data)

# 기업 매출 추정치 (Revenue Estimate) 조회
data = crawler.revenue_estimate(ticker)
print(data)

# 기업 수익 내역 (Earnings History) 조회
data = crawler.earnings_history(ticker)
print(data)

# 기업 EPS 추세 (EPS Trend) 조회
data = crawler.eps_trend(ticker)
print(data)

# 기업 EPS 수정치 (EPS Revisions) 조회
data = crawler.eps_revisions(ticker)
print(data)

# 기업 성장 추정치 (Growth Estimate) 조회
data = crawler.growth_estimate(ticker)
print(data)

# 기업 이익공시일 (Earning Calendar) 조회
data = crawler.earning_calendar(ticker)
print(data)

# 기업 SEC 공시 정보 (SEC Filings) 조회
data = crawler.sec_filings(ticker)
print(data)

# 기업 추천도움 (Recommendation) 조회
data = crawler.recommendation(ticker)
print(data)

# 일별 시세 조회
start_date='2025-12-01'
end_date='2025-12-31'
data = crawler.chart(ticker, start_date=start_date, end_date=end_date)
print(data) 

# 배당 조회
data = crawler.dividends(ticker=ticker)
print(data)

# 양도소득 조회
data = crawler.capital_gains(ticker=ticker)
print(data)

# 주식 분할 조회
data = crawler.splits(ticker=ticker)
print(data)

# Yahoo 재무제표 손익계산서 (Income Statement)
data = crawler.income_statement(ticker)
print(data)

# Yahoo 재무제표 손익계산서 (Income Statement) (분기)
data = crawler.quarterly_income_statement(ticker)
print(data)

# 재무상태표 (Balance Sheet) (연간)
data = crawler.balance_sheet(ticker)
print(data)

# 재무상태표 (Balance Sheet) (분기)
data = crawler.quarterly_balance_sheet(ticker)
print(data)

# 현금흐름표 (Cash Flow) (연간)
data = crawler.cash_flow(ticker)
print(data)

# 현금흐름표 (Cash Flow) (분기)
data = crawler.quarterly_cash_flow(ticker)
print(data)
```

#### yfinance

```python
import yfinance as yf

# 기업 정보 조회
info = yf.Ticker('AAPL').info
print(info)

# 일별 시세 조회
history = yf.Ticker('AAPL').history(start='2025-01-01', end='2025-12-31')
print(history)

# 재무제표 (Financials) (연간)
financials = yf.Ticker('TSLA').financials
print(financials)

# 재무제표 손익계산서 (Income Statement) (연간)
income_stmt = yf.Ticker('TSLA').income_stmt
print(income_stmt)

# 재무제표 손익계산서 (Income Statement) (분기)
quarterly_income_stmt = yf.Ticker('TSLA').quarterly_income_stmt
print(quarterly_income_stmt)

# 재무상태표 (Balance Sheet) (연간)
balance_sheet = yf.Ticker('TSLA').balance_sheet
print(balance_sheet)

# 재무상태표 (Balance Sheet) (분기)
quarterly_balance_sheet = yf.Ticker('TSLA').quarterly_balance_sheet
print(quarterly_balance_sheet)

# 배당금 (Dividends)
dividends = yf.Ticker('AAPL').dividends
print(dividends)

# 주식 분할 (Splits)
splits = yf.Ticker('AAPL').splits
print(splits)

# 양도소득 (Capital Gains)
capital_gains = yf.Ticker('AAPL').capital_gains
print(capital_gains)

# 매출 추정치 (Revenue Estimate)
revenue_estimate = yf.Ticker('AAPL').revenue_estimate
print(revenue_estimate)

# 수익 추정치 (Earning Estimate)
earnings_trend = yf.Ticker('AAPL').earnings_estimate
print(earnings_estimate)

# EPS 추세 (EPS Trend)
eps_trend = yf.Ticker('AAPL').eps_trend
print(eps_trend)

# EPS 수정치 (EPS Revisions)
eps_revisions = yf.Ticker('AAPL').eps_revisions
print(eps_revisions)

earnings = yf.Ticker('AAPL').earnings
print(earnings)

quarterly_earnings = yf.Ticker('AAPL').quarterly_earnings
print(quarterly_earnings)

earnings_dates = yf.Ticker('AAPL').earnings_dates
print(earnings_dates)

recommendations = yf.Ticker('AAPL').recommendations
print(recommendations)

recommendations_summary = yf.Ticker('AAPL').recommendations_summary
print(recommendations_summary)

options = yf.Ticker('AAPL').options
print(options)

sec_filings = yf.Ticker('AAPL').sec_filings
print(sec_filings)

fast_info = yf.Ticker('AAPL').fast_info
print(fast_info)
```

https://github.com/ranaroussi/yfinance

```python
_QUERY1_URL_ = 'https://query1.finance.yahoo.com'
_BASE_URL_ = 'https://query2.finance.yahoo.com'
_ROOT_URL_ = 'https://finance.yahoo.com'
```

https://finance.yahoo.com/xhr/ncp?queryRef={query_ref}&serviceKey=ncp_fin (POST)
https://finance.yahoo.com/calendar/earnings?symbol=INTC
https://markets.businessinsider.com/ajax/SearchController_Suggest?max_results=25&query={urlencode(q)}
https://finance.yahoo.com/calendar/earnings?symbol={}&offset={}&size={} # .format(ticker, offset, size), size: ~ 100
https://query1.finance.yahoo.com/v1/finance/visualization

```python
    def get_news(self, count=10, tab="news", proxy=_SENTINEL_) -> list:
        """Allowed options for tab: "news", "all", "press releases"""
        if self._news:
            return self._news

        logger = utils.get_yf_logger()

        if proxy is not _SENTINEL_:
            warnings.warn("Set proxy via new config function: yf.set_config(proxy=proxy)", DeprecationWarning, stacklevel=2)
            self._data._set_proxy(proxy)

        tab_queryrefs = {
            "all": "newsAll",
            "news": "latestNews",
            "press releases": "pressRelease",
        }

        query_ref = tab_queryrefs.get(tab.lower())
        if not query_ref:
            raise ValueError(f"Invalid tab name '{tab}'. Choose from: {', '.join(tab_queryrefs.keys())}")

        url = f"{_ROOT_URL_}/xhr/ncp?queryRef={query_ref}&serviceKey=ncp_fin"
        payload = {
            "serviceConfig": {
                "snippetCount": count,
                "s": [self.ticker]
            }
        }

        data = self._data.post(url, body=payload)
        if data is None or "Will be right back" in data.text:
            raise RuntimeError("*** YAHOO! FINANCE IS CURRENTLY DOWN! ***\n"
                               "Our engineers are working quickly to resolve "
                               "the issue. Thank you for your patience.")
        try:
            data = data.json()
        except _json.JSONDecodeError:
            logger.error(f"{self.ticker}: Failed to retrieve the news and received faulty response instead.")
            data = {}

        news = data.get("data", {}).get("tickerStream", {}).get("stream", [])

        self._news = [article for article in news if not article.get('ad', [])]
        return self._news
```