# Sayou Stock

[![PyPI version](https://img.shields.io/pypi/v/sayou-stock.svg?color=blue)](https://pypi.org/project/sayou-stock/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/stock/)


## 📦 Installation

`sayou-stock` is automatically installed when you install any Sayou library.

    pip install sayou-stock

## 🔑 Key Components

1. `EDGARCrawler`: Retrieves `10-K, 10-Q, 8-K, 13F, DEF 14A` documents using `SEC EDGAR` API.
2. `FnGuideCrawler`: Crawls Company Information & Financial Statements from `FnGuide`.
3. `NaverCrawler`: Retrieves Market News using `Naver` API and Crawls Market Data from `Naver`.
4. `OpenDartCrawler`: Retrieves Company Information & Financial Statements using `OpenDart` API.
5. `YahooCrawler`: Retrieves Company Information & Market Data using `Yahoo Finance` API.

## 🤝 Usage Example

#### Retrieve SEC EDGAR 10-K

```python
from sayou.stock.edgar import EDGARCrawler

crawler = EDGARCrawler(user_agent="Sayouzone sjkim@sayouzone.com")
ticker = "AAPL"

# Retrieve CIK by Ticker
cik = crawler.fetch_cik_by_ticker(ticker)

# EDGAR 10-K Annual Report
filings = crawler.fetch_filings(cik, doc_type="10-K", count=1)
data = crawler.extract_10k(cik, filings[0].document_url, filings[0].accession_number)

# EDGAR 10-Q Quarterly Report
filings = crawler.fetch_filings(cik, doc_type="10-Q", count=1)
data = crawler.extract_10q(cik, filings[0].document_url, filings[0].accession_number)

# EDGAR 8-K Current Report
filings = crawler.fetch_filings(cik, doc_type="8-K", count=1)
data = crawler.extract_8k(cik, filings[0].document_url, filings[0].accession_number)

# EDGAR 13F Institutional Holdings
filings = crawler.fetch_filings(cik, doc_type="13F", count=1)
data = crawler.extract_13f(cik, filings[0].document_url, filings[0].accession_number)

# EDGAR DEF 14A Proxy Statement 
filings = crawler.fetch_filings(cik, doc_type="DEF 14A", count=1)
data = crawler.extract_def14a(cik, filings[0].document_url, filings[0].accession_number)
```

#### Retrieve FnGuide's Company Information

```python
from sayou.stock.fnguide import FnGuideCrawler

stock = "005930"
crawler = FnGuideCrawler()

# Company Finance
data = crawler.finance(stock)
print(data)

# Company Information
data = crawler.company(stock)
print(data)

# Company Finance Ratio
data = crawler.finance_ratio(stock)
print(data)

# Company Investment
data = crawler.invest(stock)
print(data)

# Company Consensus
data = crawler.consensus(stock)
print(data)
```

#### Retrieve Naver's Company News

```python
from sayou.stock.naver import NaverCrawler

client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
crawler = NaverCrawler(client_id, client_secret)

# Naver Category News
articles = crawler.category_news()
print(articles)

# Naver company's News
articles = crawler.news(query="삼성전자", max_articles=10)
print(articles)
```

#### Retrieve OpenDart's Company Information

```python
from sayou.stock.opendart import OpenDartCrawler

DART_API_KEY = "YOUR_DART_API_KEY"

stock = "005930"
crawler = OpenDartCrawler(api_key=DART_API_KEY)

# Search corp_code from Company Name or Stock Code
corp_code = crawler.fetch_corp_code(stock)
print(corp_code)

# Single Company's Main Accounts
api_type = "단일회사 주요계정"
last_year = 2024
data = crawler.finance(corp_code, last_year, api_type=api_type)
status = data.get("status", "")
list = data.get("list", [])
if status == "000" and len(list) > 0:
    print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
    df = pd.DataFrame(list)
    print(df)

# Multiple Companies' Main Accounts
api_type = "다중회사 주요계정"
data = crawler.finance(corp_code, last_year, api_type=api_type)
status = data.get("status", "")
list = data.get("list", [])
if status == "000" and len(list) > 0:
    print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
    df = pd.DataFrame(list)
    print(df)

# Single Company's Total Financial Statements (Linked)
api_type = "단일회사 전체 재무제표"
data = crawler.finance(corp_code, last_year, api_type=api_type)
status = data.get("status", "")
list = data.get("list", [])
if status == "000" and len(list) > 0:
    print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
    df = pd.DataFrame(list)
    print(df)
```

#### Retrieve Yahoo's Company Information

```python
from sayou.stock.yahoo import YahooCrawler

ticker = "AAPL"
crawler = YahooCrawler()

# Company Calendar
data = crawler.calendar(ticker)
print(data)

# Earning Estimate
data = crawler.earnings_estimate(ticker)
print(data)

# Revenue Estimate
data = crawler.revenue_estimate(ticker)
print(data)

# Earnings History
data = crawler.earnings_history(ticker)
print(data)
```

## 📜 License

Apache 2.0 License © 2025 Sayouzone