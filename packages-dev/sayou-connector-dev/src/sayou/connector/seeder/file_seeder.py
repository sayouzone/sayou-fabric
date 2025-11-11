from typing import List
from ..interfaces.base_seeder import BaseSeeder
from ..core.exceptions import ConnectorError

class FileSeeder(BaseSeeder):
    """(Tier 2) '파일'에서 Seed 리스트를 읽는 일반 엔진."""
    component_name = "FileSeeder"
    
    def initialize(self, **kwargs):
        self.filepath = kwargs.get("seed_filepath")
        if not self.filepath:
            raise ConnectorError("FileSeeder requires 'seed_filepath'.")

    def _do_seed(self) -> List[str]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # 공백/주석(#) 제거 후 리스트 반환
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            self._log(f"Seed file not found: {self.filepath}")
            return []