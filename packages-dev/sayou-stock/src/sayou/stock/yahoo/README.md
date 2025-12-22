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
    ├── chart.py         # 시세정보 API 파서
    ├── fundamentals.py  # 재무정보 API 파서
    ├── quote.py         # 기업정보 API 파서
    └── news.py          # 뉴스 API 파서
```

https://developer.yahoo.com/api/
https://www.yahoo.com/

#### Official Yahoo APIs
For general Yahoo news outside of the finance context, there is no official public API. Yahoo does maintain a Yahoo Developer Network with APIs primarily focused on other services like fantasy sports, which use the OAuth protocol for authentication.

#### Alternative Approaches

If you need general news or are unable to use yfinance, consider these alternatives:
- **Web Scraping:** You could use Python libraries like requests and BeautifulSoup to scrape news headlines directly from Yahoo News webpages, though this is less reliable than an API and subject to changes in the website's structure.
- **Third-Party News APIs:** Use a dedicated, reliable news API (e.g., Apify's Yahoo Finance scraper or general news APIs like Alpha Vantage or Finnhub) that may offer a Yahoo News data scraper or a broad range of news sources. These services often involve a subscription or usage limits.


yfinance

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