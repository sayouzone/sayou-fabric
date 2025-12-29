# FnGuide 오픈API

패키지 구조

```
fnguide/
├── __init__.py          # 공개 API 정의
├── client.py            # OpenDART HTTP 클라이언트
├── models.py            # 데이터 클래스 (DTO)
├── utils.py             # 유틸리티 함수 & 상수
├── crawler.py           # 통합 인터페이스 (Facade)
├── examples.py          # 사용 예시
└── parsers/
    ├── __init__.py
    ├── company.py            # FnGuide 기업개요 파서
    ├── comparison.py         # FnGuide 경쟁사비교 파서
    ├── consensus.py          # FnGuide 컨센서스 파서
    ├── dart.py               # FnGuide 금감원공시 파서
    ├── disclosure.py         # FnGuide 거래소공시 파서
    ├── finance_ratio.py      # FnGuide 재무비율 파서
    ├── finance.py            # FnGuide 재무제표 파서
    ├── industry_analysis.py  # FnGuide 업종분석 파서
    ├── invest.py             # FnGuide 투자지표 파서
    ├── main.py               # FnGuide 메인(Snapshot) 파서
    └── share_analysis.py     # FnGuide 지분분석 파서
```

## FnGuide Url 목록

- [메인](https://comp.fnguide.com/SVO2/ASP/SVD_main.asp?gicode=A{stock})
- [기업개요](https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?gicode=A{stock})
- [재무제표](https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?gicode=A{stock})
- [재무비율](https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?gicode=A{stock})
- [재무비율 (연간)](https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?gicode=A{stock}&ReportGB=D)
- [재무비율 (분기)](https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?gicode=A{stock}&ReportGB=B)
- [재무비율 (메뉴 포함)](https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{stock}&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701)
- [투자지표](https://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?gicode=A{stock})
- [컨센서스](https://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?gicode=A{stock})
- [지분분석](https://comp.fnguide.com/SVO2/ASP/SVD_shareanalysis.asp?gicode=A{stock})
- [업종분석](https://comp.fnguide.com/SVO2/ASP/SVD_ujanal.asp?gicode=A{stock})
- [경쟁사비교](https://comp.fnguide.com/SVO2/ASP/SVD_Comparison.asp?gicode=A{stock})
- [거래소공시](https://comp.fnguide.com/SVO2/ASP/SVD_Disclosure.asp?gicode=A{stock})
- [금감원공시](https://comp.fnguide.com/SVO2/ASP/SVD_Dart.asp?gicode=A{stock})


## 사용 예시

#### FnGuide 기업 정보 | Snapshot 조회

```python
from fnguide import FnGuideCrawler

crawler = FnGuideCrawler()

data = crawler.main("005930")
print(data)
    >>> 
    >>> # FnGuide 기업 정보 | 재무제표 조회
    >>> data = crawler.finance("005930")
    >>> print(data)
```

#### # FnGuide 기업 정보 | 재무제표 조회

```python
from fnguide import FnGuideCrawler

crawler = FnGuideCrawler()

data = crawler.finance("005930")
print(data)
```

## 참조

- [삼성전자(A005930) | Snapshot | 기업정보 | Company Guide](https://comp.fnguide.com/SVO2/ASP/SVD_main.asp?gicode=A005930)
- [삼성전자(A005930) | 재무제표 | 기업정보 | Company Guide, 메뉴 포함](https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?gicode=A005930&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701)
- [삼성전자(A005930) | 재무제표 | 기업정보 | Company Guide, 메뉴 제외](https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?gicode=A005930)