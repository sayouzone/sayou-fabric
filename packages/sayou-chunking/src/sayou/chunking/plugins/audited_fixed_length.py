from typing import Any, Dict, List

from ..splitter.fixed_length_splitter import FixedLengthSplitter


class AuditedFixedLengthSplitter(FixedLengthSplitter):

    component_name = "AuditedFixedLengthSplitter"

    SUPPORTED_TYPES = ["fixed_length_audited"]

    def initialize(self, **kwargs):
        super().initialize(**kwargs)
        self._audit_tag = kwargs.get("audit_tag", "audited_by_sayou_plugin")
        self._log(
            f"AuditedFixedLengthSplitter (Plugin) is ready. Tag: {self._audit_tag}"
        )

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:

        default_chunks = super()._do_split(split_request)

        for chunk in default_chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["audit_tag"] = self._audit_tag

        return default_chunks
