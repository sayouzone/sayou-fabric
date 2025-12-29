# Sayou Stock

[![PyPI version](https://img.shields.io/pypi/v/sayou-stock.svg?color=blue)](https://pypi.org/project/sayou-stock/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/stock/)


## 📦 Installation

`sayou-stock` is automatically installed when you install any Sayou library.

    pip install sayou-stock

## 🔑 Key Components

1. `EDGARCrawler`: SEC EDGAR 10-K, 10-Q, 8-K, 13F, DEF 14A
2. `FnGuideCrawler`: FnGuide Company Information
3. `NaverCrawler`: Naver Market API/Crawling
4. `OpenDartCrawler`: OpenDART API
5. `YahooCrawler`: Yahoo Finance API

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

data = crawler.finance(stock)
print(data)

data = crawler.company(stock)
print(data)

data = crawler.finance_ratio(stock)
print(data)

data = crawler.invest(stock)
print(data)

data = crawler.consensus(stock)
print(data)
```

## 📚 Package Hierarchy

```
sayou/stock
│   ├── edgar/
│   │   ├── __init__.py          # Public API Definition
│   │   ├── client.py            # SEC EDGAR HTTP Client
│   │   ├── models.py            # Data Class (DTO)
│   │   ├── utils.py             # Utility Functions & Constants
│   │   ├── crawler.py           # Unified Interface Crawler
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── form_10k.py      # 10-K/10-Q Parser
│   │       ├── form_8k.py       # 8-K Parser
│   │       ├── form_13f.py      # 13F Parser
│   │       └── def14a.py        # DEF 14A Parser
│   ├── fnguide/
│   │   ├── __init__.py          # Public API Definition
│   │   ├── client.py            # OpenDART HTTP Client
│   │   ├── models.py            # Data Class (DTO)
│   │   ├── utils.py             # Utility Functions & Constants
│   │   ├── crawler.py           # Unified Interface Crawler
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── company.py            # FnGuide Company Overview Parser
│   │       ├── comparison.py         # FnGuide Comparison Parser
│   │       ├── consensus.py          # FnGuide Consensus Parser
│   │       ├── dart.py               # FnGuide Dart Parser
│   │       ├── disclosure.py         # FnGuide Disclosure Parser
│   │       ├── finance_ratio.py      # FnGuide Finance Ratio Parser
│   │       ├── finance.py            # FnGuide Financial Statement Parser
│   │       ├── industry_analysis.py  # FnGuide Industry Analysis Parser
│   │       ├── invest.py             # FnGuide Investment Parser
│   │       ├── json_parser.py        # FnGuide JSON Parser
│   │       ├── main.py               # FnGuide Main Parser
│   │       ├── share_analysis.py     # FnGuide Share Analysis Parser
│   │       └── tables.py             # FnGuide Tables Parser
│   ├── naver/
│   │   ├── __init__.py          # Public API Definition
│   │   ├── client.py            # OpenDART HTTP Client
│   │   ├── models.py            # Data Class (DTO)
│   │   ├── utils.py             # Utility Functions & Constants
│   │   ├── crawler.py           # Unified Interface Crawler
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── news.py          # Naver News Crawling Parser
│   │       └── market.py        # Naver Market API/Crawling Parser
│   ├── opendart/
│   │   ├── __init__.py          # Public API Definition
│   │   ├── client.py            # OpenDART HTTP Client
│   │   ├── models.py            # Data Class (DTO)
│   │   ├── utils.py             # Utility Functions & Constants
│   │   ├── crawler.py           # Unified Interface Crawler
│   │   └── parsers/
│   │       ├── __init__.py
│   │       ├── document.py        # Document API Parser
│   │       ├── document_viewer.py # Document Viewer API Parser
│   │       ├── disclosure.py      # Disclosure API Parser
│   │       ├── finance.py         # Finance API Parser
│   │       ├── material_facts.py  # Material Facts API Parser
│   │       ├── ownership.py       # Ownership API Parser
│   │       ├── registration.py    # Registration API Parser
│   │       └── reports.py         # Reports API Parser
│   └── yahoo/
│       ├── __init__.py          # Public API Definition
│       ├── client.py            # OpenDART HTTP Client
│       ├── models.py            # Data Class (DTO)
│       ├── utils.py             # Utility Functions & Constants
│       ├── crawler.py           # Unified Interface Crawler
│       └── parsers/
│           ├── __init__.py
│           ├── analysis.py      # Analysis API Parser
│           ├── chart.py         # Chart API Parser
│           ├── conversations.py # Conversations API Parser
│           ├── financials.py    # Financials API Parser
│           ├── fundamentals.py  # Fundamentals API Parser
│           ├── holders.py       # Holders API Parser
│           ├── market.py        # Market API Parser
│           ├── news.py          # News API Parser
│           ├── options.py       # Options API Parser
│           ├── profile.py       # Profile API Parser
│           ├── quotes.py        # Quotes API Parser
│           ├── statistics.py    # Statistics API Parser
│           └── summary.py       # Summary API Parser
├── docs/
├── tests/
│   ├── test_edgar_.py          # Edgar Test
│   ├── test_fnguide_.py        # FnGuide Test
│   ├── test_naver_.py          # Naver Test
│   ├── test_opendart_.py       # OpenDART Test
│   └── test_yahoo_.py          # Yahoo Test
├── LICENSE
├── pyproject.toml
└── README.md
```

## 📜 License

Apache 2.0 License © 2025 Sayouzone