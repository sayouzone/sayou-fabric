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
        self.ns = Namespace(base_uri)
        
        # 네임스페이스 바인딩
        self.graph.bind("stock", self.ns)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        
        self._define_ontology()
    
    def _define_ontology(self):
        """온톨로지 스키마 정의"""
        
        # ===== 클래스 정의 =====
        
        # 주요 엔티티
        classes = {
            'Stock': '개별 주식 종목',
            'Company': '상장 기업',
            'Sector': '산업 섹터',
            'Industry': '산업 분류',
            'Market': '거래 시장',
            
            # 가격 및 지표
            'PriceData': '주가 데이터',
            'TechnicalIndicator': '기술적 지표',
            'FundamentalIndicator': '기본적 지표',
            
            # 이벤트
            'MarketEvent': '시장 이벤트',
            'CorporateAction': '기업 행동',
            'NewsEvent': '뉴스 이벤트',
            
            # 트렌드 및 패턴
            'Trend': '추세',
            'Pattern': '차트 패턴',
            'Signal': '매매 신호',
            
            # 투자자
            'Investor': '투자자',
            'Institution': '기관 투자자',
            'Foreign': '외국인 투자자',
            'Individual': '개인 투자자',
        }
        
        for class_name, description in classes.items():
            class_uri = self.ns[class_name]
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(class_name, lang='en')))
            self.graph.add((class_uri, RDFS.comment, Literal(description, lang='ko')))
        
        # 클래스 계층 구조
        hierarchies = [
            ('TechnicalIndicator', ['RSI', 'MACD', 'BollingerBands', 'MovingAverage']),
            ('FundamentalIndicator', ['PER', 'PBR', 'ROE', 'EPS', 'DividendYield']),
            ('Trend', ['Uptrend', 'Downtrend', 'Sideways']),
            ('Pattern', ['HeadAndShoulders', 'DoubleTop', 'DoubleBottom', 'Triangle']),
            ('Signal', ['BuySignal', 'SellSignal', 'HoldSignal']),
            ('MarketEvent', ['Earning', 'Dividend', 'Split', 'Merger']),
        ]
        
        for parent, children in hierarchies:
            parent_uri = self.ns[parent]
            for child in children:
                child_uri = self.ns[child]
                self.graph.add((child_uri, RDF.type, OWL.Class))
                self.graph.add((child_uri, RDFS.subClassOf, parent_uri))
                self.graph.add((child_uri, RDFS.label, Literal(child, lang='en')))
        
        # ===== Object Properties (관계) 정의 =====
        
        object_properties = {
            'belongsToSector': ('Stock', 'Sector', '섹터에 속함'),
            'belongsToIndustry': ('Stock', 'Industry', '산업에 속함'),
            'tradedOn': ('Stock', 'Market', '거래됨'),
            'issuedBy': ('Stock', 'Company', '발행됨'),
            
            'hasPriceData': ('Stock', 'PriceData', '가격 데이터 보유'),
            'hasTechnicalIndicator': ('Stock', 'TechnicalIndicator', '기술적 지표 보유'),
            'hasFundamentalIndicator': ('Stock', 'FundamentalIndicator', '기본적 지표 보유'),
            
            'showsTrend': ('Stock', 'Trend', '추세 보임'),
            'showsPattern': ('Stock', 'Pattern', '패턴 보임'),
            'generatesSignal': ('Stock', 'Signal', '신호 생성'),
            
            'experiencesEvent': ('Stock', 'MarketEvent', '이벤트 경험'),
            'correlatesWith': ('Stock', 'Stock', '상관관계'),
            'competsWith': ('Company', 'Company', '경쟁관계'),
            
            'ownedBy': ('Stock', 'Investor', '보유됨'),
        }
        
        for prop_name, (domain, range_class, description) in object_properties.items():
            prop_uri = self.ns[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.graph.add((prop_uri, RDFS.domain, self.ns[domain]))
            self.graph.add((prop_uri, RDFS.range, self.ns[range_class]))
            self.graph.add((prop_uri, RDFS.label, Literal(prop_name, lang='en')))
            self.graph.add((prop_uri, RDFS.comment, Literal(description, lang='ko')))
        
        # ===== Data Properties (속성) 정의 =====
        
        data_properties = {
            # 주식 속성
            'stockCode': (XSD.string, '종목코드'),
            'stockName': (XSD.string, '종목명'),
            'marketCap': (XSD.decimal, '시가총액'),
            'listedDate': (XSD.date, '상장일'),
            
            # 가격 속성
            'openPrice': (XSD.decimal, '시가'),
            'closePrice': (XSD.decimal, '종가'),
            'highPrice': (XSD.decimal, '고가'),
            'lowPrice': (XSD.decimal, '저가'),
            'volume': (XSD.integer, '거래량'),
            'priceDate': (XSD.date, '가격 날짜'),
            
            # 지표 속성
            'indicatorValue': (XSD.decimal, '지표 값'),
            'indicatorDate': (XSD.date, '지표 날짜'),
            
            # 추세 속성
            'trendStrength': (XSD.decimal, '추세 강도'),
            'trendDuration': (XSD.integer, '추세 지속기간'),
            'trendStartDate': (XSD.date, '추세 시작일'),
            
            # 신호 속성
            'signalConfidence': (XSD.decimal, '신호 신뢰도'),
            'signalDate': (XSD.date, '신호 발생일'),
        }
        
        for prop_name, (datatype, description) in data_properties.items():
            prop_uri = self.ns[prop_name]
            self.graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            self.graph.add((prop_uri, RDFS.range, datatype))
            self.graph.add((prop_uri, RDFS.label, Literal(prop_name, lang='en')))
            self.graph.add((prop_uri, RDFS.comment, Literal(description, lang='ko')))
    
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

