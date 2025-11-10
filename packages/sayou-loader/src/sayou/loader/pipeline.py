from typing import Any
from sayou.core.base_component import BaseComponent
from .interfaces.base_translator import BaseTranslator
from .interfaces.base_writer import BaseWriter

class LoaderPipeline(BaseComponent):
    """
    (Orchestrator) 'Translator'와 'Writer'를
    '조립'하여 'Load' 파이프라인을 실행합니다.
    """
    component_name = "LoaderPipeline"

    def __init__(self, 
                translator: BaseTranslator,
                writer: BaseWriter):
        
        self.translator = translator
        self.writer = writer
        self._log("Pipeline initialized with Translator and Writer.")

    def initialize(self, **kwargs):
        """
        내부 컴포넌트(Translator, Writer)에 설정을 주입합니다.
        
        e.g., kwargs = {
            "filepath": "output.json", (Writer가 사용)
            "format": "jsonl",        (Writer가 사용)
            "neo4j_uri": "bolt://..." (Writer가 사용)
        }
        """
        self.translator.initialize(**kwargs)
        self.writer.initialize(**kwargs)

    def run(self, input_object: Any):
        """
        [Translator -> Writer] 파이프라인을 실행합니다.
        
        :param input_object: e.g., Assembler가 생성한 KnowledgeGraph
        """
        self._log(f"Loader pipeline run started for object type {type(input_object)}.")
        
        # 1. (Translator) e.g., KG -> Cypher List
        translated_data = self.translator.translate(input_object)
        
        # 2. (Writer) e.g., Cypher List -> DB
        self.writer.write(translated_data)
        
        self._log(f"Loader run finished successfully.")