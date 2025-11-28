from ..core.models import FetchTask, FetchResult
from ..interfaces.base_fetcher import BaseFetcher

from sayou.core.decorators import retry, measure_time, safe_run

class FileFetcher(BaseFetcher):
    """
    (Tier 2) 로컬 파일 시스템에서 바이너리를 읽어오는 Fetcher.
    """
    component_name = "FileFetcher"
    SUPPORTED_TYPES = ["file"]

    def fetch(self, task: FetchTask) -> FetchResult:
        try:
            file_path = task.uri
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            return FetchResult(
                task=task,
                data=file_bytes,
                success=True
            )
            
        except Exception as e:
            self._log(f"Error reading file {task.uri}: {e}")
            return FetchResult(
                task=task,
                data=None,
                success=False,
                error=str(e)
            )