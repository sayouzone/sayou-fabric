from typing import List
from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom

from .core.exceptions import AssemblerError
from .utils.schema_manager import SchemaManager
from .utils.schema_validator import SchemaValidator
from .interfaces.base_builder import BaseBuilder
from .interfaces.base_storer import BaseStorer

class AssemblerPipeline(BaseComponent):
    """
    Assembler 파이프라인 (Orchestrator).
    (Validator -> Builder -> Storer) 순서로 작업을 실행합니다.
    """
    component_name = "AssemblerPipeline"

    def __init__(self,
                schema_manager: SchemaManager,
                validator: SchemaValidator,
                builder: BaseBuilder,
                storer: BaseStorer):
        
        self.schema_manager = schema_manager
        self.validator = validator
        self.builder = builder
        self.storer = storer
        self._log("Pipeline initialized with components.")

    def initialize(self, **kwargs):
        """
        컴포넌트들을 초기화하고 의존성을 주입합니다.
        (e.g., Manager -> Validator)
        """
        try:
            # 1. 스키마 관리자 및 검증기 초기화
            self.schema_manager.initialize(**kwargs)
            ontology_data = self.schema_manager.get_ontology()
            
            # Validator가 로드된 스키마 데이터를 받아서 초기화
            kwargs_for_validator = kwargs.copy()
            kwargs_for_validator['ontology'] = ontology_data
            self.validator.initialize(**kwargs_for_validator)
            
            # 2. 빌더 및 스토어 초기화 (kwargs 전달)
            self.builder.initialize(**kwargs)
            self.storer.initialize(**kwargs)
        
        except Exception as e:
            raise AssemblerError(f"Failed to initialize pipeline components: {e}")

        self._log("All components initialized.")

    def run(self, refined_atoms: List[DataAtom], **kwargs) -> dict:
        """
        atoms 대신 RAG의 'refined_atoms'를 받습니다.
        
        :param refined_atoms: Refinery가 반환한 DataAtom 리스트
        :return: {"kg_object": ..., "kg_path": ...} 딕셔너리
        """
        self._log(f"Assembler run started with {len(refined_atoms)} atoms.")

        # 1. 검증 (Validation)
        valid_atoms = self.validator.validate_batch(refined_atoms)
        self._log(f"Validation complete: {len(valid_atoms)} / {len(refined_atoms)} valid atoms.")
        if not valid_atoms:
            self._log("No valid atoms to process. Exiting.")
            return {"kg_object": None, "kg_path": None}

        # 2. 구축 (Build)
        self._log(f"Running Builder: {self.builder.component_name}...")
        built_object = self.builder.build(valid_atoms)
        if built_object is None:
            self._log("Builder returned None. Exiting.")
            return {"kg_object": None, "kg_path": None}
        self._log(f"Build complete. Object type: {type(built_object)}")

        # 3. 저장 (Store)
        self._log(f"Running Storer: {self.storer.component_name}...")
        self.storer.store(built_object)
        self._log(f"Store complete. Assembly finished.")

        return {
            "kg_object": built_object,
            "kg_path": getattr(self.storer, "filepath", None) # FileStorer가 경로를 가지고 있다고 가정
        }