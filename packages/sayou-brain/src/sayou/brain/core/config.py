from typing import Any, Dict

from sayou.core.config import SayouConfig as _CoreConfig


class SayouConfig(_CoreConfig):
    """
    Brain-level configuration manager.

    Extends ``sayou.core.config.SayouConfig`` with per-library property
    accessors so pipeline constructors can unpack sub-configs cleanly::

        cfg = SayouConfig({
            "connector": {"timeout": 30},
            "loader":    {"batch_size": 256},
        })

        ConnectorPipeline(**cfg.connector)   # → {"timeout": 30}
        LoaderPipeline(**cfg.loader)         # → {"batch_size": 256}

    All ``get()`` / ``set()`` / ``merge()`` behaviour is inherited from
    ``sayou.core.config.SayouConfig``.
    """

    # Convenience properties — each returns the section dict (never None)

    @property
    def connector(self) -> Dict[str, Any]:
        return self.section("connector")

    @property
    def document(self) -> Dict[str, Any]:
        return self.section("document")

    @property
    def refinery(self) -> Dict[str, Any]:
        return self.section("refinery")

    @property
    def chunking(self) -> Dict[str, Any]:
        return self.section("chunking")

    @property
    def wrapper(self) -> Dict[str, Any]:
        return self.section("wrapper")

    @property
    def assembler(self) -> Dict[str, Any]:
        return self.section("assembler")

    @property
    def loader(self) -> Dict[str, Any]:
        return self.section("loader")
