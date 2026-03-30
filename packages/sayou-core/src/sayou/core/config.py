import os
from typing import Any, Dict


class SayouConfig:
    """
    Universal configuration manager for Sayou pipelines.

    Provides a two-level key-value store (section → key → value) with
    automatic fallback to environment variables.

    Integration with BaseComponent
    ───────────────────────────────
    Pass a ``SayouConfig`` instance to ``BaseComponent.initialize()`` or
    directly to the pipeline constructor's ``**kwargs``.  Each pipeline
    merges it into ``self.global_config`` which is forwarded to every
    component at run time::

        cfg = SayouConfig({
            "connector": {"timeout": 30, "max_retries": 3},
            "loader":    {"batch_size": 256},
        })
        ConnectorPipeline(**cfg.section("connector"))

    Environment variable fallback
    ─────────────────────────────
    If a key is absent from the config dict, ``get()`` looks for an env var
    named ``SAYOU_<SECTION>_<KEY>`` (uppercased).  Example::

        export SAYOU_CONNECTOR_TIMEOUT=60
        cfg.get("connector", "timeout")   # → "60"  (str from env)

    Note: env-var values are always strings — cast explicitly where needed.
    """

    def __init__(self, config_dict: Dict[str, Any] | None = None) -> None:
        self._config: Dict[str, Any] = config_dict or {}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, section: str, key: str | None = None, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Args:
            section: Top-level section name (e.g. ``"connector"``).
            key: Key within the section.  If ``None``, the entire section
                 dict is returned.
            default: Value returned when the key is absent and no env var
                     exists (default ``None``).

        Returns:
            The value from the config dict, the env var string, or
            ``default``.
        """
        section_data = self._config.get(section, {})

        if key is None:
            return section_data

        if key in section_data:
            return section_data[key]

        env_var = f"SAYOU_{section.upper()}_{key.upper()}"
        return os.environ.get(env_var, default)

    def section(self, name: str) -> Dict[str, Any]:
        """
        Return an entire section as a flat dict (convenience alias).

        Suitable for unpacking directly into pipeline ``**kwargs``::

            pipeline = LoaderPipeline(**cfg.section("loader"))
        """
        return self._config.get(name, {})

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a single configuration value at runtime.

        Args:
            section: Section name.
            key: Key within the section.
            value: The value to store.
        """
        self._config.setdefault(section, {})[key] = value

    def merge(self, other: "SayouConfig") -> "SayouConfig":
        """
        Return a new ``SayouConfig`` that is the shallow merge of this
        config and ``other``.  Values in ``other`` take precedence.

        The original instances are not modified.
        """
        merged: Dict[str, Any] = {}
        for section in set(self._config) | set(other._config):
            merged[section] = {
                **self._config.get(section, {}),
                **other._config.get(section, {}),
            }
        return SayouConfig(merged)

    def __repr__(self) -> str:
        sections = list(self._config.keys())
        return f"SayouConfig(sections={sections})"
