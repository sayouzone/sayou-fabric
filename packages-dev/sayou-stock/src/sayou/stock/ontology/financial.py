from rdflib import Graph, Namespace, RDF, RDFS, Literal, OWL, XSD

class FinancialOntology:
    """금융 온톨로지 클래스"""
    
    def __init__(self, base_uri: str = "http://sayouzone.com/finance/"):
        self.graph = Graph()
        self.base_uri = base_uri
        
        # 네임스페이스 정의
        self.FIN = Namespace(f"{base_uri}ontology#")
        self.DATA = Namespace(f"{base_uri}data#")
        
        # 네임스페이스 바인딩
        self.graph.bind("fin", self.FIN)
        self.graph.bind("data", self.DATA)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        
        self._define_ontology()
    
    def _define_ontology(self):
        """온톨로지 스키마 정의"""
        
        # 클래스 정의
        classes = {
            'Company': '기업',
            'Stock': '주식',
            'FinancialStatement': '재무제표',
            'IncomeStatement': '손익계산서',
            'BalanceSheet': '재무상태표',
            'CashFlowStatement': '현금흐름표',
            'StockPrice': '주가',
            'News': '뉴스',
            'Industry': '산업',
            'Market': '시장',
            'Investor': '투자자',
            'FinancialMetric': '재무지표',
            'Event': '이벤트'
        }
        
        for class_name, label in classes.items():
            class_uri = self.FIN[class_name]
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(label, lang='ko')))
        
        # 계층 구조 정의
        self.graph.add((self.FIN.IncomeStatement, RDFS.subClassOf, self.FIN.FinancialStatement))
        self.graph.add((self.FIN.BalanceSheet, RDFS.subClassOf, self.FIN.FinancialStatement))
        self.graph.add((self.FIN.CashFlowStatement, RDFS.subClassOf, self.FIN.FinancialStatement))
        
        # Object Properties 정의
        self._define_object_properties()
        
        # Datatype Properties 정의
        self._define_datatype_properties()
    
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
            'competitorOf': ('경쟁사', self.FIN.Company, self.FIN.Company)
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
            'marketCap': ('시가총액', XSD.decimal),
            'foundedDate': ('설립일', XSD.date),
            
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
            'closingPrice': ('종가', XSD.decimal),
            'openingPrice': ('시가', XSD.decimal),
            'highPrice': ('고가', XSD.decimal),
            'lowPrice': ('저가', XSD.decimal),
            'volume': ('거래량', XSD.integer),
            'tradingDate': ('거래일', XSD.date),
            
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
        """온톨로지 저장"""
        self.graph.serialize(destination=filepath, format=format)
        print(f"온톨로지가 {filepath}에 저장되었습니다.")