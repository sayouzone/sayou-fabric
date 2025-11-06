# src/sayou/wrapper/pipeline.py
from typing import List, Any
from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom
from sayou.core.exceptions import InitializationError
from sayou.wrapper.interfaces.base_mapper import BaseMapper
from sayou.wrapper.interfaces.base_validator import BaseValidator

class Pipeline(BaseComponent):
    """
    (Orchestrator) 'Mapper'와 'Validator'를
    '조립'하여 'Wrapping' 파이프라인을 실행합니다.
    """
    component_name = "WrapperPipeline"

    def __init__(self, 
                mapper: BaseMapper,
                validator: BaseValidator):
        
        self.mapper = mapper
        self.validator = validator
        self._log("Pipeline initialized with Mapper and Validator.")

    def initialize(self, **kwargs):
        """
        내부 컴포넌트(Mapper, Validator)에 설정을 주입합니다.
        
        e.g., kwargs = {
            "field_mappings": {0: "payload.entity_id"},
            "static_fields": {"source": "csv_source"},
            "ontology_path": "path/to/schema.json"
        }
        """
        self.mapper.initialize(**kwargs)
        self.validator.initialize(**kwargs)

    def run(self, raw_data_list: List[Any]) -> List[DataAtom]:
        """
        [Mapper -> Validator -> DataAtom] 파이프라인을 실행합니다.
        
        :param raw_data_list: e.g., CSV row 리스트
        :return: 생성된 DataAtom 리스트
        """
        self._log(f"Wrapper pipeline run started with {len(raw_data_list)} items.")
        
        # 1. (Mapper) Raw -> Dict 리스트로 매핑
        mapped_dicts = self.mapper.map_list(raw_data_list)
        
        # 2. (Validator) 스키마 검증 및 필터링
        validated_dicts = self.validator.validate_list(mapped_dicts)
        
        # 3. (공통) DataAtom 객체 생성
        final_atoms: List[DataAtom] = []
        for v_dict in validated_dicts:
            try:
                # ⭐️ DataAtom.from_dict()가 아닌, 키를 직접 매핑
                # (BaseWrapper.wrap()의 로직을 파이프라인이 수행)
                atom = DataAtom(
                    source=v_dict.get("source"),
                    type=v_dict.get("type"),
                    payload=v_dict.get("payload", {})
                )
                final_atoms.append(atom)
            except Exception as e:
                self._log(f"DataAtom creation failed: {e}")

        self._log(f"Wrapper run finished. {len(final_atoms)} atoms created.")
        return final_atoms