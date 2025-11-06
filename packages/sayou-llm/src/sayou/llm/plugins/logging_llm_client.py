from sayou.llm.llm_client.openai_client import OpenAIClient
from typing import Dict, Any, List, Optional
import time

class LoggingOpenAIClient(OpenAIClient):
    """
    (Tier 3 - 플러그인) 'OpenAIClient'(T2)를 상속받아,
    'invoke' 호출 시간을 로깅하는 '래퍼' 플러그인.
    """
    component_name = "LoggingOpenAIClient"
    # ⭐️ T2와 동일한 타입을 선언하여 '대체(Override)'
    SUPPORTED_TYPES = ["openai_chat"] 

    def initialize(self, **kwargs):
        """T2의 초기화를 먼저 호출"""
        super().initialize(**kwargs)
        self._log("LoggingOpenAIClient (Plugin) is active. (Overrides T2)")

    def invoke(self, 
        prompt: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        **kwargs) -> Dict[str, Any]:
        """
        [T1 메서드 래핑] T2(부모)의 'invoke'를 호출하고
        부가 기능(시간 측정)을 추가합니다.
        """
        self._log("T3 Plugin: Measuring invocation time...")
        start_time = time.time()
        
        # ⭐️ T2(부모)의 공통 골격(invoke) 호출
        response = super().invoke(prompt, chat_history, **kwargs)
        
        duration = time.time() - start_time
        self._log(f"T3 Plugin: Invocation completed in {duration:.2f} seconds.")
        
        # T2의 결과에 정보 추가
        response["metadata"]["duration_sec"] = duration
        
        return response
    
    # (stream 메서드는 래핑하지 않았으므로 T2의 것이 그대로 사용됨)