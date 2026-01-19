from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd

class StockOntology:
    """주식 트렌드 분석을 위한 온톨로지 클래스"""
    
    def __init__(self, base_uri: str = "http://sayouzone.com/stock-ontology#"):
        """
        Args:
            base_uri: 온톨로지 기본 URI
        """
        self.graph = Graph()
        self.base_uri = base_uri

        # 네임스페이스 정의
        self.FIN = Namespace(f"{base_uri}ontology#")
        self.DATA = Namespace(f"{base_uri}data#")
        self.ns = Namespace(base_uri)
        
        # 네임스페이스 바인딩
        self.graph.bind("stock", self.ns)
        self.graph.bind("fin", self.FIN)
        self.graph.bind("data", self.DATA)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        
        self._define_ontology()
    
    def _define_ontology(self):
        """온톨로지 스키마 정의"""
        
        # ===== 클래스 정의 =====
        
        # 주요 엔티티
        classes = {
            'Company': '기업',
            'Stock': '주식',
            'Sector': '산업 섹터',
            'Industry': '산업',
            'Market': '시장',
            
            # 가격 및 지표
            'StockPrice': '주가',
            'TechnicalIndicator': '기술적 지표',
            'FundamentalIndicator': '기본적 지표',
            
            # 이벤트
            'MarketEvent': '시장 이벤트',
            'CorporateAction': '기업 행동',
            'News': '뉴스',
            'Event': '이벤트',
            
            # 트렌드 및 패턴
            'Trend': '추세',
            'Pattern': '차트 패턴',
            'Signal': '매매 신호',
            
            # 투자자
            'Investor': '투자자',
            'Institution': '기관 투자자',
            'Foreign': '외국인 투자자',
            'Individual': '개인 투자자',

            # 재무제표
            'FinancialMetric': '재무지표',
            'FinancialStatement': '재무제표',
            'IncomeStatement': '손익계산서',
            'BalanceSheet': '재무상태표',
            'CashFlowStatement': '현금흐름표',
        }
        
        for class_name, description in classes.items():
            class_uri = self.ns[class_name]
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(class_name, lang='en')))
            self.graph.add((class_uri, RDFS.comment, Literal(description, lang='ko')))

        # 계층 구조 정의
        self.graph.add((self.FIN.IncomeStatement, RDFS.subClassOf, self.FIN.FinancialStatement))
        self.graph.add((self.FIN.BalanceSheet, RDFS.subClassOf, self.FIN.FinancialStatement))
        self.graph.add((self.FIN.CashFlowStatement, RDFS.subClassOf, self.FIN.FinancialStatement))
        
        # Hierarchies Properties 정의
        self._define_hierarchy_properties()
        
        # Object Properties 정의
        self._define_object_properties()
        
        # Datatype Properties 정의
        self._define_datatype_properties()
        """
        # ===== Object Properties (관계) 정의 =====
        
        object_properties = {
            'belongsToSector': ('Stock', 'Sector', '섹터에 속함'),
            'belongsToIndustry': ('Stock', 'Industry', '산업에 속함'),
            'tradedOn': ('Stock', 'Market', '거래됨'),
            'issuedBy': ('Stock', 'Company', '발행됨'),
            
            'hasStockPrice': ('Stock', 'StockPrice', '주가 보유'),
            'hasTechnicalIndicator': ('Stock', 'TechnicalIndicator', '기술적 지표 보유'),
            'hasFundamentalIndicator': ('Stock', 'FundamentalIndicator', '기본적 지표 보유'),
            
            'showsTrend': ('Stock', 'Trend', '추세 보임'),
            'showsPattern': ('Stock', 'Pattern', '패턴 보임'),
            'generatesSignal': ('Stock', 'Signal', '신호 생성'),
            
            'experiencesEvent': ('Stock', 'MarketEvent', '이벤트 경험'),
            'correlatesWith': ('Stock', 'Stock', '상관관계'),
            'competsWith': ('Company', 'Company', '경쟁관계'),
            
            'ownedBy': ('Stock', 'Investor', '보유됨'),

            'hasFinancialMetric': ('Stock', 'FinancialMetric', '재무지표 보유'),
            'hasFinancialStatement': ('Stock', 'FinancialStatement', '재무제표 보유'),
            'hasIncomeStatement': ('Stock', 'IncomeStatement', '손익계산서 보유'),
            'hasBalanceSheet': ('Stock', 'BalanceSheet', '재무상태표 보유'),
            'hasCashFlowStatement': ('Stock', 'CashFlowStatement', '현금흐름표 보유'),
        }
        
        for prop_name, (domain, range_class, description) in object_properties.items():
            prop_uri = self.ns[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((prop_uri, RDFS.domain, self.ns[domain]))
            self.graph.add((prop_uri, RDFS.range, self.ns[range_class]))
            self.graph.add((prop_uri, RDFS.label, Literal(prop_name, lang='en')))
            self.graph.add((prop_uri, RDFS.comment, Literal(description, lang='ko')))
        """

    def _define_hierarchy_properties(self):
        """계층 구조 프로퍼티 정의"""
        
        # 클래스 계층 구조
        properties = [
            ('TechnicalIndicator', ['RSI', 'MACD', 'BollingerBands', 'MovingAverage']),
            ('FundamentalIndicator', ['PER', 'PBR', 'ROE', 'EPS', 'DividendYield']),
            ('Trend', ['Uptrend', 'Downtrend', 'Sideways']),
            ('Pattern', ['HeadAndShoulders', 'DoubleTop', 'DoubleBottom', 'Triangle']),
            ('Signal', ['BuySignal', 'SellSignal', 'HoldSignal']),
            ('MarketEvent', ['Earning', 'Dividend', 'Split', 'Merger']),
        ]
        
        for parent, children in properties:
            parent_uri = self.ns[parent]
            for child in children:
                child_uri = self.ns[child]
                self.graph.add((child_uri, RDF.type, OWL.Class))
                self.graph.add((child_uri, RDFS.subClassOf, parent_uri))
                self.graph.add((child_uri, RDFS.label, Literal(child, lang='en')))


    def _define_object_properties(self):
        """객체 프로퍼티 정의"""
        
        properties = {
            'belongsToIndustry': ('속한_산업', self.FIN.Company, self.FIN.Industry),
            'listedIn': ('상장된_시장', self.FIN.Stock, self.FIN.Market),
            'hasStock': ('보유_주식', self.FIN.Company, self.FIN.Stock),
            'hasFinancialStatement': ('재무제표_보유', self.FIN.Company, self.FIN.FinancialStatement),
            'hasStockPrice': ('주가_정보', self.FIN.Stock, self.FIN.StockPrice),
            'mentionsCompany': ('언급_기업', self.FIN.News, self.FIN.Company),
            'relatedToEvent': ('관련_이벤트', self.FIN.News, self.FIN.Event),
            'hasMetric': ('보유_지표', self.FIN.FinancialStatement, self.FIN.FinancialMetric),
            'competitorOf': ('경쟁사', self.FIN.Company, self.FIN.Company),
            'correlationOf': ('상관관계', self.FIN.Company, self.FIN.Company),
            
            'hasStockPrice': ('보유_주가', self.FIN.Stock, self.FIN.StockPrice),
            'hasTechnicalIndicator': ('보유_기술적지표', self.FIN.Stock, self.FIN.TechnicalIndicator),
            'hasFundamentalIndicator': ('보유_기본적지표', self.FIN.Stock, self.FIN.FundamentalIndicator),
            
            'showsTrend': ('보유_추세', self.FIN.Stock, self.FIN.Trend),
            'showsPattern': ('보유_패턴', self.FIN.Stock, self.FIN.Pattern),
            'generatesSignal': ('신호_생성', self.FIN.Stock, self.FIN.Signal),
            
            'experiencesEvent': ('이벤트_경험', self.FIN.Stock, self.FIN.MarketEvent),
        }
        
        for prop_name, (label, domain, range_class) in properties.items():
            prop_uri = self.FIN[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((prop_uri, RDFS.label, Literal(label, lang='ko')))
            self.graph.add((prop_uri, RDFS.domain, domain))
            self.graph.add((prop_uri, RDFS.range, range_class))
    
    def _define_datatype_properties(self):
        """데이터타입 프로퍼티 정의"""
        
        properties = {
            # 기업 속성
            'companyName': ('기업명', XSD.string),
            'stockCode': ('종목코드', XSD.string),
            'stockName': ('종목명', XSD.string),
            'marketCap': ('시가총액', XSD.decimal),
            'foundedDate': ('설립일', XSD.date),
            'listedDate': ('상장일', XSD.date),

            # 재무 속성
            'revenue': ('매출액', XSD.decimal),
            'operatingIncome': ('영업이익', XSD.decimal),
            'netIncome': ('순이익', XSD.decimal),
            'totalAssets': ('총자산', XSD.decimal),
            'totalLiabilities': ('총부채', XSD.decimal),
            'totalEquity': ('총자본', XSD.decimal),
            'eps': ('주당순이익', XSD.decimal),
            'per': ('주가수익비율', XSD.decimal),
            'pbr': ('주가순자산비율', XSD.decimal),
            'roe': ('자기자본이익률', XSD.decimal),

            # 주가 속성
            'openingPrice': ('시가', XSD.decimal),
            'closingPrice': ('종가', XSD.decimal),
            'highPrice': ('고가', XSD.decimal),
            'lowPrice': ('저가', XSD.decimal),
            'volume': ('거래량', XSD.integer),
            'tradingDate': ('거래일', XSD.date),
            
            # 지표 속성
            'indicatorValue': ('지표 값', XSD.decimal),
            'indicatorDate': ('지표 날짜', XSD.date),

            # 추세 속성
            'trendStrength': ('추세 강도', XSD.decimal),
            'trendDuration': ('추세 지속기간', XSD.integer),
            'trendStartDate': ('추세 시작일', XSD.date),

            # 신호 속성
            'signalConfidence': ('신호 신뢰도', XSD.decimal),
            'signalDate': ('신호 발생일', XSD.date),
            
            # 뉴스 속성
            'newsTitle': ('뉴스제목', XSD.string),
            'newsContent': ('뉴스내용', XSD.string),
            'publishedDate': ('발행일', XSD.dateTime),
            'sentiment': ('감성점수', XSD.decimal)
        }
        
        for prop_name, (label, datatype) in properties.items():
            prop_uri = self.FIN[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            self.graph.add((prop_uri, RDFS.label, Literal(label, lang='ko')))
            self.graph.add((prop_uri, RDFS.range, datatype))
    
    def save_ontology(self, filepath: str, format: str = 'turtle'):
        """온톨로지를 파일로 저장
        
        Args:
            filepath: 저장 경로
            format: 저장 포맷 (turtle, xml, n3, nt)
        """
        self.graph.serialize(destination=filepath, format=format, encoding='utf-8')
        print(f"온톨로지 저장 완료: {filepath}")
    
    def load_ontology(self, filepath: str, format: str = 'turtle'):
        """온톨로지 파일 로드"""
        self.graph.parse(filepath, format=format)
        print(f"온톨로지 로드 완료: {filepath}")

