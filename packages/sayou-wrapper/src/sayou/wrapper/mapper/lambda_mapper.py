from sayou.wrapper.interfaces.base_mapper import BaseMapper
from typing import Callable, Any, Dict

class LambdaMapper(BaseMapper):
    """
    사용자로부터 '함수(lambda)'를 입력받아
    _do_map_item을 대신 실행하는 '어댑터' 클래스입니다.
    """
    component_name = "LambdaMapper"

    def __init__(self, map_function: Callable[[Any], Dict[str, Any]]):
        super().__init__()
        if not callable(map_function):
            raise TypeError("LambdaMapper requires a 'map_function' (Callable).")
        self.map_function = map_function

    def _do_map_item(self, item: Any) -> Dict[str, Any]:
        """BaseMapper의 뼈대가 호출하면, 등록된 함수를 실행합니다."""
        try:
            return self.map_function(item)
        except Exception as e:
            self._log(f"Lambda function failed for item {item}: {e}")
            return None