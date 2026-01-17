import pandas as pd

from rdflib import Graph, Namespace, RDF, RDFS, Literal
from rdflib.namespace import XSD
from typing import Dict, List

from .kg import StockKnowledgeGraph

class StockTrendAnalyzer(StockKnowledgeGraph):
    """Knowledge Graph 기반 주식 트렌드 분석기"""
    
    def import_from_dataframe(self, df: pd.DataFrame, stock_code: str):
        """DataFrame에서 주가 데이터 임포트
        
        Args:
            df: 주가 데이터 DataFrame (columns: date, open, high, low, close, volume)
            stock_code: 종목코드
        """
        for _, row in df.iterrows():
            self.add_price_data(
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
                self.add_technical_indicator(
                    stock_code=stock_code,
                    indicator_type='RSI',
                    value=float(value),
                    date=date
                )
                
                # RSI 기반 신호 생성
                if value < 30:
                    self.add_signal(stock_code, 'BuySignal', 
                                  confidence=0.7, date=date)
                elif value > 70:
                    self.add_signal(stock_code, 'SellSignal', 
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
            
            self.add_trend(
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