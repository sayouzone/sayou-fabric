# Sayou Stock


Package Hierarchy

```
src
├──sayou/stock
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
│   │       ├── main.py               # FnGuide Main Parser
│   │       └── share_analysis.py     # FnGuide Share Analysis Parser
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
│   ├── test_edgar.py           # Edgar Test
│   ├── test_fnguide.py         # FnGuide Test
│   ├── test_naver.py           # Naver Test
│   ├── test_opendart.py        # OpenDART Test
│   └── test_yahoo.py           # Yahoo Test
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.cfg
└── setup.py
```

## Installation

```bash
pip install sayou-stock
```

##