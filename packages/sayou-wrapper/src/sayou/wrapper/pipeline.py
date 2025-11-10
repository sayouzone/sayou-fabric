import json
from typing import Dict, List, Any

from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom
from .interfaces.base_mapper import BaseMapper
from .interfaces.base_validator import BaseValidator

class WrapperPipeline(BaseComponent):
    """
    (Orchestrator) 'Mapper'와 'Validator'를
    '조립'하여 'Wrapping' 파이프라인을 실행합니다.
    """
    component_name = "WrapperPipeline"

    def __init__(self, 
        mapper: BaseMapper,
        validator: BaseValidator
    ):
        
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

    def run(self, raw_data: Any, **kwargs) -> Dict[str, Any]: # 👈 'raw_data'를 받음
        """
        1. Connector가 전달한 *단일* 'raw_data'(JSON 문자열)를 받습니다.
        2. 'paths' 리스트를 *직접* 파싱합니다.
        3. 'BaseMapper.map_list' (뼈대)에 *진짜 리스트*를 전달합니다.
        """
        self._log(f"Wrapper pipeline run started with single raw_data item.")

        real_raw_data_list = []
        try:
            parsed_data = json.loads(raw_data)
            current_data = parsed_data.get("body", {}).get("paths")

            if current_data is None:
                self._log("'paths' field not found in JSON body.")

            if isinstance(current_data, list) and current_data and isinstance(current_data[0], str):
                current_data = "".join(current_data) 
            while isinstance(current_data, str):
                current_data = json.loads(current_data)

            if isinstance(current_data, list):
                real_raw_data_list = current_data
            else:
                self._log(f"Expected 'paths' to resolve to a list, but got {type(current_data)}")

        except Exception as e:
            self._log(f"Failed to parse and extract 'paths' from raw_data: {e}")

        mapped_dicts = self.mapper.map_list(real_raw_data_list)
        validated_dicts = self.validator.validate_list(mapped_dicts)
        final_atoms: List[DataAtom] = []
        for v_dict in validated_dicts:
            try:
                atom = DataAtom(
                    source=v_dict.get("source"),
                    type=v_dict.get("type"),
                    payload=v_dict.get("payload", {})
                )
                final_atoms.append(atom)
            except Exception as e:
                self._log(f"DataAtom creation failed: {e}")

        self._log(f"Wrapper run finished. {len(final_atoms)} atoms created.")

        return {"atoms": final_atoms}