import pandas as pd
from rdflib import Literal, RDF, RDFS, URIRef # Graph, Namespace, OWL, 
from rdflib.namespace import XSD

from .ontology import StockOntology

class StockKnowledgeGraph(StockOntology):
    """주식 Knowledge Graph 구축 및 관리"""
    
    def __init__(self, base_uri: str = "http://sayouzone.com/stock-ontology#"):
        super().__init__(base_uri)
        self.stock_instances = {}
        
    def add_stock(self, stock_code: str, stock_name: str, 
                  sector: str = None, industry: str = None,
                  market: str = 'KOSPI', **kwargs) -> URIRef:
        """주식 인스턴스 추가
        
        Args:
            stock_code: 종목코드
            stock_name: 종목명
            sector: 섹터
            industry: 산업
            market: 시장
            **kwargs: 추가 속성
        
        Returns:
            생성된 주식 인스턴스 URI
        """
        stock_uri = self.ns[f"stock_{stock_code}"]
        
        # 타입 선언
        self.graph.add((stock_uri, RDF.type, self.ns.Stock))
        
        # 기본 속성
        self.graph.add((stock_uri, self.ns.stockCode, Literal(stock_code)))
        self.graph.add((stock_uri, self.ns.stockName, Literal(stock_name, lang='ko')))
        
        # 섹터 관계
        if sector:
            sector_uri = self.ns[f"sector_{sector.replace(' ', '_')}"]
            self.graph.add((sector_uri, RDF.type, self.ns.Sector))
            self.graph.add((sector_uri, RDFS.label, Literal(sector, lang='ko')))
            self.graph.add((stock_uri, self.ns.belongsToSector, sector_uri))
        
        # 산업 관계
        if industry:
            industry_uri = self.ns[f"industry_{industry.replace(' ', '_')}"]
            self.graph.add((industry_uri, RDF.type, self.ns.Industry))
            self.graph.add((industry_uri, RDFS.label, Literal(industry, lang='ko')))
            self.graph.add((stock_uri, self.ns.belongsToIndustry, industry_uri))
        
        # 시장 관계
        market_uri = self.ns[f"market_{market}"]
        self.graph.add((market_uri, RDF.type, self.ns.Market))
        self.graph.add((market_uri, RDFS.label, Literal(market)))
        self.graph.add((stock_uri, self.ns.tradedOn, market_uri))
        
        # 추가 속성
        for key, value in kwargs.items():
            if hasattr(self.ns, key):
                prop_uri = self.ns[key]
                self.graph.add((stock_uri, prop_uri, Literal(value)))
        
        self.stock_instances[stock_code] = stock_uri
        return stock_uri
    
    def add_price_data(self, stock_code: str, date: str, 
                       open_price: float, close_price: float,
                       high_price: float, low_price: float, 
                       volume: int) -> URIRef:
        """주가 데이터 추가"""
        if stock_code not in self.stock_instances:
            raise ValueError(f"종목 {stock_code}가 그래프에 없습니다.")
        
        stock_uri = self.stock_instances[stock_code]
        price_uri = self.ns[f"price_{stock_code}_{date}"]
        
        # 가격 데이터 인스턴스
        self.graph.add((price_uri, RDF.type, self.ns.PriceData))
        self.graph.add((stock_uri, self.ns.hasPriceData, price_uri))
        
        # 속성
        self.graph.add((price_uri, self.ns.priceDate, Literal(date, datatype=XSD.date)))
        self.graph.add((price_uri, self.ns.openPrice, Literal(open_price, datatype=XSD.decimal)))
        self.graph.add((price_uri, self.ns.closePrice, Literal(close_price, datatype=XSD.decimal)))
        self.graph.add((price_uri, self.ns.highPrice, Literal(high_price, datatype=XSD.decimal)))
        self.graph.add((price_uri, self.ns.lowPrice, Literal(low_price, datatype=XSD.decimal)))
        self.graph.add((price_uri, self.ns.volume, Literal(volume, datatype=XSD.integer)))
        
        return price_uri
    
    def add_technical_indicator(self, stock_code: str, indicator_type: str,
                               value: float, date: str) -> URIRef:
        """기술적 지표 추가
        
        Args:
            stock_code: 종목코드
            indicator_type: 지표 타입 (RSI, MACD, etc.)
            value: 지표 값
            date: 날짜
        """
        if stock_code not in self.stock_instances:
            raise ValueError(f"종목 {stock_code}가 그래프에 없습니다.")
        
        stock_uri = self.stock_instances[stock_code]
        indicator_uri = self.ns[f"{indicator_type}_{stock_code}_{date}"]
        
        # Namespace 객체에서 속성으로 접근
        if hasattr(self.ns, indicator_type):
            indicator_class = self.ns[indicator_type]
        else:
            indicator_class = self.ns.TechnicalIndicator
    
        self.graph.add((indicator_uri, RDF.type, indicator_class))
        self.graph.add((stock_uri, self.ns.hasTechnicalIndicator, indicator_uri))
        
        self.graph.add((indicator_uri, self.ns.indicatorValue, 
                    Literal(value, datatype=XSD.decimal)))
        self.graph.add((indicator_uri, self.ns.indicatorDate, 
                    Literal(date, datatype=XSD.date)))
        
        return indicator_uri
    
    def add_trend(self, stock_code: str, trend_type: str,
                  strength: float, start_date: str, 
                  duration_days: int = None) -> URIRef:
        """추세 정보 추가
        
        Args:
            stock_code: 종목코드
            trend_type: 추세 타입 (Uptrend, Downtrend, Sideways)
            strength: 추세 강도 (0-1)
            start_date: 시작일
            duration_days: 지속 기간 (일)
        """
        if stock_code not in self.stock_instances:
            raise ValueError(f"종목 {stock_code}가 그래프에 없습니다.")
        
        stock_uri = self.stock_instances[stock_code]
        trend_uri = self.ns[f"trend_{stock_code}_{start_date}"]
        
        # 추세 타입에 따른 클래스
        if hasattr(self.ns, trend_type):
            trend_class = self.ns[trend_type]
        else:
            trend_class = self.ns.Trend
        
        self.graph.add((trend_uri, RDF.type, trend_class))
        self.graph.add((stock_uri, self.ns.showsTrend, trend_uri))
        
        self.graph.add((trend_uri, self.ns.trendStrength, 
                    Literal(strength, datatype=XSD.decimal)))
        self.graph.add((trend_uri, self.ns.trendStartDate, 
                    Literal(start_date, datatype=XSD.date)))
        
        if duration_days:
            self.graph.add((trend_uri, self.ns.trendDuration, 
                        Literal(duration_days, datatype=XSD.integer)))
        
        return trend_uri
    
    def add_signal(self, stock_code: str, signal_type: str,
                   confidence: float, date: str) -> URIRef:
        """매매 신호 추가
        
        Args:
            stock_code: 종목코드
            signal_type: 신호 타입 (BuySignal, SellSignal, HoldSignal)
            confidence: 신뢰도 (0-1)
            date: 발생일
        """
        if stock_code not in self.stock_instances:
            raise ValueError(f"종목 {stock_code}가 그래프에 없습니다.")
        
        stock_uri = self.stock_instances[stock_code]
        signal_uri = self.ns[f"signal_{stock_code}_{date}"]
        
        if hasattr(self.ns, signal_type):
            signal_class = self.ns[signal_type]
        else:
            signal_class = self.ns.Signal
        
        self.graph.add((signal_uri, RDF.type, signal_class))
        self.graph.add((stock_uri, self.ns.generatesSignal, signal_uri))
        
        self.graph.add((signal_uri, self.ns.signalConfidence, 
                    Literal(confidence, datatype=XSD.decimal)))
        self.graph.add((signal_uri, self.ns.signalDate, 
                    Literal(date, datatype=XSD.date)))
        
        return signal_uri
    
    def add_correlation(self, stock_code1: str, stock_code2: str,
                       correlation_value: float = None):
        """종목 간 상관관계 추가"""
        if stock_code1 not in self.stock_instances or stock_code2 not in self.stock_instances:
            raise ValueError("종목이 그래프에 없습니다.")
        
        stock_uri1 = self.stock_instances[stock_code1]
        stock_uri2 = self.stock_instances[stock_code2]
        
        self.graph.add((stock_uri1, self.ns.correlatesWith, stock_uri2))
        
        # 대칭적 관계
        self.graph.add((stock_uri2, self.ns.correlatesWith, stock_uri1))