# analyzer.py
"""
금융 지식 그래프 분석 모듈
SPARQL 쿼리를 활용한 고급 분석
"""

import pandas as pd

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD
from typing import Any, Dict, List, Optional

from .stock_kg import StockKnowledgeGraph
from .models import StockPriceData

class StockAnalyzer:
    """Knowledge Graph 기반 주식 트렌드 분석기"""

    def __init__(self, base_uri: str = "http://sayouzone.com/stock-ontology#"):
        self.base_uri = base_uri
        self.kg = StockKnowledgeGraph(base_uri)
        self.graph = self.kg.graph
        self.FIN = self.kg.FIN
        self.DATA = self.kg.DATA

    @property
    def stock_instances(self):
        return self.kg.stock_instances

    def add_stock(self, stock_code: str, stock_name: str, 
                  df: pd.DataFrame,
                  sector: str = None, industry: str = None,
                  market: str = 'KOSPI', **kwargs) -> URIRef:
        
        self.kg.add_stock(stock_code, stock_name, sector, industry, market, **kwargs)
        print(f"종목 추가: {stock_name} ({stock_code})")

        self._import_from_dataframe(stock_code, df)
        print("\n주가 데이터 추가 완료")

        # RSI 계산 및 추가
        self.calculate_and_add_rsi(stock_code, df)
        print("RSI 지표 추가 완료")

        # 추세 감지
        self.detect_trend(stock_code, df)
        print("추세 분석 완료")

    def add_correlation(self, stock_code1: str, stock_code2: str,
                       correlation_value: float = None):
        self.kg.add_correlation(stock_code1, stock_code2, correlation_value)

    def save_ontology(self, filepath: str, format: str = 'turtle'):
        self.kg.save_ontology(filepath, format)

    def _import_from_dataframe(self, stock_code: str, df: pd.DataFrame):
        """DataFrame에서 주가 데이터 임포트
        
        Args:
            df: 주가 데이터 DataFrame (columns: date, open, high, low, close, volume)
            stock_code: 종목코드
        """
        for _, row in df.iterrows():
            self.kg.add_price_data(
                stock_code=stock_code,
                date=row['date'],
                open_price=float(row['open']),
                close_price=float(row['close']),
                high_price=float(row['high']),
                low_price=float(row['low']),
                volume=int(row['volume'])
            )
    
    def calculate_and_add_rsi(self, stock_code: str, df: pd.DataFrame, period: int = 14):
        """RSI 계산 및 그래프에 추가"""
        # RSI 계산
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 그래프에 추가
        for idx, value in rsi.items():
            if pd.notna(value):
                date = df.loc[idx, 'date']
                self.kg.add_technical_indicator(
                    stock_code=stock_code,
                    indicator_type='RSI',
                    value=float(value),
                    date=date
                )
                
                # RSI 기반 신호 생성
                if value < 30:
                    self.kg.add_signal(stock_code, 'BuySignal', 
                                  confidence=0.7, date=date)
                elif value > 70:
                    self.kg.add_signal(stock_code, 'SellSignal', 
                                  confidence=0.7, date=date)
    
    def detect_trend(self, stock_code: str, df: pd.DataFrame, window: int = 20):
        """추세 감지 및 추가"""
        # 이동평균 계산
        df['ma'] = df['close'].rolling(window=window).mean()
        
        # 추세 판단
        df['trend'] = 0
        df.loc[df['close'] > df['ma'] * 1.02, 'trend'] = 1  # 상승
        df.loc[df['close'] < df['ma'] * 0.98, 'trend'] = -1  # 하락
        
        # 추세 변화점 감지
        df['trend_change'] = df['trend'].diff()
        
        trend_starts = df[df['trend_change'] != 0].copy()
        
        for idx in trend_starts.index:
            trend_value = df.loc[idx, 'trend']
            date = df.loc[idx, 'date']
            
            if trend_value == 1:
                trend_type = 'Uptrend'
            elif trend_value == -1:
                trend_type = 'Downtrend'
            else:
                trend_type = 'Sideways'
            
            # 추세 강도 계산 (단순화)
            strength = min(abs(df.loc[idx, 'close'] - df.loc[idx, 'ma']) / 
                         df.loc[idx, 'ma'], 1.0)
            
            self.kg.add_trend(
                stock_code=stock_code,
                trend_type=trend_type,
                strength=float(strength),
                start_date=date
            )
    
    def query_stocks_by_trend(self, trend_type: str) -> List[str]:
        """특정 추세를 보이는 종목 조회
        
        Args:
            trend_type: Uptrend, Downtrend, Sideways
        
        Returns:
            종목코드 리스트
        """
        query = f"""
        PREFIX stock: <{self.base_uri}>
        PREFIX rdf: <{RDF}>
        
        SELECT DISTINCT ?code ?name
        WHERE {{
            ?stock rdf:type stock:Stock ;
                   stock:stockCode ?code ;
                   stock:stockName ?name ;
                   stock:showsTrend ?trend .
            ?trend rdf:type stock:{trend_type} .
        }}
        """
        
        results = self.graph.query(query)
        stocks = [(str(row.code), str(row.name)) for row in results]
        return stocks
    
    def query_stocks_with_buy_signal(self, min_confidence: float = 0.5) -> List[Dict]:
        """매수 신호가 있는 종목 조회"""
        query = f"""
        PREFIX stock: <{self.base_uri}>
        PREFIX rdf: <{RDF}>
        PREFIX xsd: <{XSD}>
        
        SELECT ?code ?name ?confidence ?date
        WHERE {{
            ?stock rdf:type stock:Stock ;
                   stock:stockCode ?code ;
                   stock:stockName ?name ;
                   stock:generatesSignal ?signal .
            ?signal rdf:type stock:BuySignal ;
                    stock:signalConfidence ?confidence ;
                    stock:signalDate ?date .
            FILTER (?confidence >= {min_confidence})
        }}
        ORDER BY DESC(?confidence) DESC(?date)
        """
        
        results = self.graph.query(query)
        stocks = [{
            'code': str(row.code),
            'name': str(row.name),
            'confidence': float(row.confidence),
            'date': str(row.date)
        } for row in results]
        
        return stocks
    
    def query_sector_analysis(self) -> pd.DataFrame:
        """섹터별 종목 분석"""
        query = f"""
        PREFIX stock: <{self.base_uri}>
        PREFIX rdf: <{RDF}>
        PREFIX rdfs: <{RDFS}>
        
        SELECT ?sector (COUNT(?stock) as ?count)
        WHERE {{
            ?stock rdf:type stock:Stock ;
                stock:belongsToSector ?sectorObj .
            ?sectorObj rdfs:label ?sector .
        }}
        GROUP BY ?sector
        ORDER BY DESC(?count)
        """
        
        results = self.graph.query(query)
        df = pd.DataFrame([{
            'sector': str(row['sector']),
            'count': int(row['count'])
        } for row in results])
        
        return df
    
    def get_stock_summary(self, stock_code: str) -> Dict:
        """특정 종목의 종합 정보 조회"""
        query = f"""
        PREFIX stock: <{self.base_uri}>
        PREFIX rdf: <{RDF}>
        PREFIX rdfs: <{RDFS}>
        
        SELECT ?name ?sector ?industry ?market
        WHERE {{
            ?stock rdf:type stock:Stock ;
                   stock:stockCode "{stock_code}" ;
                   stock:stockName ?name .
            
            OPTIONAL {{
                ?stock stock:belongsToSector ?sectorObj .
                ?sectorObj rdfs:label ?sector .
            }}
            
            OPTIONAL {{
                ?stock stock:belongsToIndustry ?industryObj .
                ?industryObj rdfs:label ?industry .
            }}
            
            OPTIONAL {{
                ?stock stock:tradedOn ?marketObj .
                ?marketObj rdfs:label ?market .
            }}
        }}
        """
        
        results = list(self.graph.query(query))
        if not results:
            return None
        
        row = results[0]
        return {
            'name': str(row.name) if row.name else None,
            'sector': str(row.sector) if row.sector else None,
            'industry': str(row.industry) if row.industry else None,
            'market': str(row.market) if row.market else None
        }

    def analyze_valuation_comparison(self, industry: str) -> pd.DataFrame:
        """산업 내 밸류에이션 비교 분석"""
        query = f"""
        PREFIX fin: <{self.FIN}>
        PREFIX data: <{self.DATA}>
        
        SELECT ?code ?name ?per ?pbr ?roe ?marketCap
        WHERE {{
            ?company fin:belongsToIndustry ?industry ;
                     fin:companyName ?name ;
                     fin:stockCode ?code ;
                     fin:hasFinancialStatement ?fs .
            ?industry rdfs:label "{industry}"@ko .
            OPTIONAL {{ ?company fin:marketCap ?marketCap }}
            OPTIONAL {{ ?fs fin:per ?per }}
            OPTIONAL {{ ?fs fin:pbr ?pbr }}
            OPTIONAL {{ ?fs fin:roe ?roe }}
        }}
        ORDER BY DESC(?marketCap)
        """
        
        results = self.graph.query(query)
        data = [dict(row.asdict()) for row in results]
        
        df = pd.DataFrame(data)
        if not df.empty:
            # 평균 대비 분석
            df['per_vs_avg'] = df['per'] / df['per'].mean() if 'per' in df.columns else None
            df['pbr_vs_avg'] = df['pbr'] / df['pbr'].mean() if 'pbr' in df.columns else None
        
        return df

    def analyze_financial_trend(self, company_code: str) -> pd.DataFrame:
        """재무 트렌드 분석"""
        query = f"""
        PREFIX fin: <{self.FIN}>
        PREFIX data: <{self.DATA}>
        
        SELECT ?revenue ?operatingIncome ?netIncome
        WHERE {{
            data:company_{company_code} fin:hasFinancialStatement ?fs .
            OPTIONAL {{ ?fs fin:revenue ?revenue }}
            OPTIONAL {{ ?fs fin:operatingIncome ?operatingIncome }}
            OPTIONAL {{ ?fs fin:netIncome ?netIncome }}
        }}
        ORDER BY ?fs
        """
        
        results = self.graph.query(query)
        data = [dict(row.asdict()) for row in results]
        
        df = pd.DataFrame(data)
        if not df.empty and len(df) > 1:
            # 성장률 계산
            df['revenue_growth'] = df['revenue'].pct_change() * 100
            df['oi_growth'] = df['operatingIncome'].pct_change() * 100
            df['ni_growth'] = df['netIncome'].pct_change() * 100
        
        return df
    
    def analyze_news_sentiment(self, company_code: str) -> Dict[str, Any]:
        """뉴스 감성 분석"""
        query = f"""
        PREFIX fin: <{self.FIN}>
        PREFIX data: <{self.DATA}>
        
        SELECT ?publishedDate ?sentiment
        WHERE {{
            ?news fin:mentionsCompany data:company_{company_code} ;
                  fin:publishedDate ?publishedDate ;
                  fin:sentiment ?sentiment .
        }}
        ORDER BY DESC(?publishedDate)
        """
        
        results = self.graph.query(query)
        sentiments = [float(row['sentiment']) for row in results]
        
        if not sentiments:
            return {
                'average': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'neutral_ratio': 0,
                'trend': 'N/A'
            }
        
        analysis = {
            'average': sum(sentiments) / len(sentiments),
            'positive_ratio': len([s for s in sentiments if s > 0.3]) / len(sentiments),
            'negative_ratio': len([s for s in sentiments if s < -0.3]) / len(sentiments),
            'neutral_ratio': len([s for s in sentiments if -0.3 <= s <= 0.3]) / len(sentiments),
            'recent_trend': sum(sentiments[:5]) / min(5, len(sentiments)) if len(sentiments) >= 5 else sum(sentiments) / len(sentiments)
        }
        
        return analysis
    
    def find_undervalued_stocks(self, industry: Optional[str] = None) -> pd.DataFrame:
        """저평가 종목 발굴"""
        industry_filter = f'?industry rdfs:label "{industry}"@ko .' if industry else ''
        
        query = f"""
        PREFIX fin: <{self.FIN}>
        PREFIX data: <{self.DATA}>
        
        SELECT ?code ?name ?per ?pbr ?roe ?marketCap
        WHERE {{
            ?company fin:companyName ?name ;
                     fin:stockCode ?code ;
                     fin:hasFinancialStatement ?fs .
            {industry_filter}
            OPTIONAL {{ ?company fin:belongsToIndustry ?industry }}
            OPTIONAL {{ ?company fin:marketCap ?marketCap }}
            OPTIONAL {{ ?fs fin:per ?per }}
            OPTIONAL {{ ?fs fin:pbr ?pbr }}
            OPTIONAL {{ ?fs fin:roe ?roe }}
            FILTER(?per < 15 && ?pbr < 1.5 && ?roe > 5)
        }}
        ORDER BY ?per
        """
        
        results = self.graph.query(query)
        data = [dict(row.asdict()) for row in results]
        
        return pd.DataFrame(data)
    

    def analyze_price_momentum(self, company_code: str, days: int = 20) -> Dict[str, Any]:
        """주가 모멘텀 분석"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        prices = self.kg.query_stock_prices(
            company_code,
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        if not prices:
            return {'momentum': 'N/A', 'trend': 'N/A'}
        
        df = pd.DataFrame(prices)
        df['close'] = df['close'].astype(float)
        
        first_price = df.iloc[0]['close']
        last_price = df.iloc[-1]['close']
        
        return {
            'return_pct': ((last_price - first_price) / first_price) * 100,
            'high': df['high'].max(),
            'low': df['low'].min(),
            'avg_volume': df['volume'].mean(),
            'volatility': df['close'].pct_change().std() * 100
        }
    
    def generate_investment_report(self, company_code: str) -> Dict[str, Any]:
        """종합 투자 리포트 생성"""
        # 기업 정보
        company_info = self.kg.query_company_info(company_code)
        
        # 재무 지표
        financials = self.kg.query_financial_metrics(company_code)
        
        # 뉴스 감성
        news_sentiment = self.analyze_news_sentiment(company_code)
        
        # 주가 모멘텀
        momentum = self.analyze_price_momentum(company_code)
        
        return {
            'company': company_info[0] if company_info else {},
            'financials': financials[0] if financials else {},
            'news_sentiment': news_sentiment,
            'price_momentum': momentum,
            'timestamp': datetime.now().isoformat()
        }