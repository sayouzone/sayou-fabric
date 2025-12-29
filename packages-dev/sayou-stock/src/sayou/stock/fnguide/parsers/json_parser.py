import re
import pandas as pd
from typing import Dict, Any, Optional, List

class FnGuideJsonParser:
    """FnGuide API JSON 응답을 DataFrame으로 변환"""
    
    # 컬럼 매핑 (D_N -> 실제 기간)
    DATA_COL_PATTERN = re.compile(r"^D_\d+$")
    
    def __init__(self, data: Dict[str, Any] = None):
        """
        Args:
            data: FnGuide API JSON 응답 {'comp': [...]}
        """
        if data:
            self.raw_data = data
            self.records = data.get("comp", [])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FnGuideJsonParser":
        """딕셔너리에서 파서 생성"""
        return cls(data)
    
    def to_dataframe(
        self,
        data: Dict[str, Any] = None,
        use_period_columns: bool = True,
        strip_whitespace: bool = True
    ) -> pd.DataFrame:
        """
        DataFrame으로 변환
        
        Args:
            use_period_columns: True면 D_N 컬럼을 실제 기간명으로 변환
            strip_whitespace: 항목명 앞뒤 공백 제거
        
        Returns:
            변환된 DataFrame
        """
        if data:
            self.raw_data = data
            self.records = data.get("comp", [])

        if not self.records:
            return pd.DataFrame()
        
        # 헤더 행 추출 (SORT_ORDER='0')
        header_row = self._find_header_row()
        
        # 데이터 행 추출
        data_rows = [r for r in self.records if r.get("SORT_ORDER") != "0"]
        
        # 컬럼 매핑 생성
        col_mapping = self._create_column_mapping(header_row)
        
        # DataFrame 생성
        df = pd.DataFrame(data_rows)
        
        # 컬럼명 변경
        if use_period_columns and col_mapping:
            df = df.rename(columns=col_mapping)
        
        # 항목명을 인덱스로
        if "ACCOUNT_NM" in df.columns:
            if strip_whitespace:
                df["ACCOUNT_NM"] = df["ACCOUNT_NM"].str.strip()
            df = df.set_index("ACCOUNT_NM")
        
        # 메타 컬럼 제거 (선택적)
        meta_cols = ["SORT_ORDER", "GB", "PARENT_YN"]
        df = df.drop(columns=[c for c in meta_cols if c in df.columns], errors="ignore")
        
        return df
    
    def to_clean_dataframe(self) -> pd.DataFrame:
        """
        정제된 DataFrame 반환 (숫자 변환 포함)
        """
        df = self.to_dataframe()
        
        # 숫자 컬럼 변환
        for col in df.columns:
            df[col] = self._convert_to_numeric(df[col])
        
        return df
    
    def to_transposed_dataframe(self) -> pd.DataFrame:
        """
        전치된 DataFrame (기간이 행, 항목이 열)
        """
        df = self.to_clean_dataframe()
        return df.T
    
    def get_periods(self) -> List[str]:
        """기간 리스트 추출"""
        header_row = self._find_header_row()
        if not header_row:
            return []
        
        periods = []
        for key, value in header_row.items():
            if self.DATA_COL_PATTERN.match(key) and value and value != "항목":
                periods.append(value)
        
        return periods
    
    def get_items(self) -> List[str]:
        """항목명 리스트 추출"""
        items = []
        for record in self.records:
            if record.get("SORT_ORDER") == "0":
                continue
            name = record.get("ACCOUNT_NM", "").strip()
            if name:
                items.append(name)
        return items
    
    def _find_header_row(self) -> Optional[Dict[str, Any]]:
        """헤더 행 찾기"""
        for record in self.records:
            if record.get("SORT_ORDER") == "0":
                return record
        return None
    
    def _create_column_mapping(
        self,
        header_row: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """D_N -> 기간명 매핑 생성"""
        if not header_row:
            return {}
        
        mapping = {}
        for key, value in header_row.items():
            if self.DATA_COL_PATTERN.match(key) and value:
                mapping[key] = value
        
        return mapping
    
    def _convert_to_numeric(self, series: pd.Series) -> pd.Series:
        """시리즈를 숫자로 변환"""
        def parse_value(val):
            if pd.isna(val) or val == "" or val == "-":
                return None
            
            if isinstance(val, (int, float)):
                return val
            
            # 문자열 처리
            val_str = str(val).strip()
            
            # 빈 값
            if not val_str or val_str == "-":
                return None
            
            # 콤마 제거
            val_str = val_str.replace(",", "")
            
            try:
                return float(val_str)
            except ValueError:
                return val  # 변환 불가시 원본 유지
        
        return series.apply(parse_value)