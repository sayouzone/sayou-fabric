import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef

from .stock_kg import StockKnowledgeGraph

class KnowledgeGraphVisualizer:
    """Knowledge Graph 시각화"""
    
    def __init__(self, kg: StockKnowledgeGraph):
        self.kg = kg
    
    def to_networkx(self) -> nx.DiGraph:
        """RDF 그래프를 NetworkX 그래프로 변환"""
        G = nx.DiGraph()
        
        for s, p, o in self.kg.graph:
            # URI를 간단한 레이블로 변환
            s_label = self._get_label(s)
            p_label = self._get_label(p)
            o_label = self._get_label(o)
            
            G.add_node(s_label, type='subject')
            G.add_node(o_label, type='object')
            G.add_edge(s_label, o_label, label=p_label)
        
        return G
    
    def _get_label(self, uri):
        """URI에서 간단한 레이블 추출"""
        if isinstance(uri, Literal):
            return str(uri)[:30]
        
        uri_str = str(uri)
        if '#' in uri_str:
            return uri_str.split('#')[-1]
        elif '/' in uri_str:
            return uri_str.split('/')[-1]
        return uri_str
    
    def visualize_interactive(self, output_file: str = 'stock_kg.html',
                             filter_type: str = None):
        """인터랙티브 시각화 (Pyvis)
        
        Args:
            output_file: 출력 HTML 파일명
            filter_type: 필터링할 노드 타입 (Stock, Sector 등)
        """
        net = Network(height='750px', width='100%', 
                     bgcolor='#222222', font_color='white',
                     notebook=False, directed=True)
        
        # 노드 색상 매핑
        color_map = {
            'Stock': '#FF6B6B',
            'Sector': '#4ECDC4',
            'Industry': '#45B7D1',
            'TechnicalIndicator': '#FFA07A',
            'Trend': '#98D8C8',
            'Signal': '#FFD93D',
        }
        
        for s, p, o in self.kg.graph:
            # 필터링
            if filter_type:
                s_type = self._get_type(s)
                if filter_type not in str(s_type):
                    continue
            
            s_label = self._get_label(s)
            p_label = self._get_label(p)
            o_label = self._get_label(o)
            
            # 노드 타입 파악
            s_type = self._get_type(s)
            o_type = self._get_type(o)
            
            # 노드 추가
            s_color = self._get_color(s_type, color_map)
            o_color = self._get_color(o_type, color_map)
            
            net.add_node(s_label, label=s_label, color=s_color, 
                        title=str(s_type))
            net.add_node(o_label, label=o_label, color=o_color, 
                        title=str(o_type))
            
            # 엣지 추가
            net.add_edge(s_label, o_label, label=p_label, 
                        title=p_label)
        
        # 물리 엔진 설정
        net.set_options("""
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -30000,
              "springLength": 200,
              "springConstant": 0.04
            }
          }
        }
        """)
        
        net.save_graph(output_file)
        print(f"인터랙티브 그래프 저장: {output_file}")
    
    def _get_type(self, uri):
        """URI의 타입 조회"""
        for s, p, o in self.kg.graph.triples((uri, RDF.type, None)):
            return o
        return None
    
    def _get_color(self, type_uri, color_map):
        """타입에 따른 색상 반환"""
        if type_uri:
            type_label = self._get_label(type_uri)
            return color_map.get(type_label, '#CCCCCC')
        return '#CCCCCC'
    
    def plot_sector_distribution(self, save_path: str = None):
        """섹터별 분포 시각화"""
        df = self.kg.query_sector_analysis()
        
        plt.figure(figsize=(10, 6))
        plt.bar(df['sector'], df['count'], color='steelblue')
        plt.xlabel('Sector', fontsize=12)
        plt.ylabel('Number of Stocks', fontsize=12)
        plt.title('Stock Distribution by Sector', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()