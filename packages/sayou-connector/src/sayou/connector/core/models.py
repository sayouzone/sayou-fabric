from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

@dataclass
class FetchTask:
    """수집 작업 명세서"""
    source_type: str
    uri: str
    params: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FetchResult:
    """수집 결과"""
    task: FetchTask
    data: Any
    success: bool = True
    error: Optional[str] = None
    next_tasks: List[FetchTask] = field(default_factory=list)