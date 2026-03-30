import logging
from abc import ABC
from typing import List

from .callbacks import BaseCallback


class BaseComponent(ABC):
    """
    The foundational base class for all Sayou components.

    Provides standardised logging, configuration management, and an event
    observation mechanism (Callback System).

    Logging policy
    ──────────────
    Following Python library best practices (PEP 3141 / logging HOWTO), this
    class attaches only a ``NullHandler`` to the component logger.  It does
    **not** add ``StreamHandler`` or configure formatting — that is the
    responsibility of the application (Brain orchestrator or user code).

    This prevents the library from hijacking the host application's logging
    configuration and avoids the handler-duplication bug that occurs when
    multiple instances share the same ``component_name``.

    To see log output during development, add a handler in your application:

        import logging
        logging.basicConfig(level=logging.DEBUG)
    """

    component_name: str = "BaseComponent"

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.component_name)
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

        self._callbacks: List[BaseCallback] = []

    def initialize(self, **kwargs) -> None:
        """
        Optional hook for subclasses to register settings or state.
        Called by the pipeline after construction.
        """
        pass

    def _log(self, msg: str, level: str = "info") -> None:
        """Emit a log message at the requested level."""
        level = level.lower()
        if level == "debug":
            self.logger.debug(msg)
        elif level == "warning":
            self.logger.warning(msg)
        elif level == "error":
            self.logger.error(msg)
        else:
            self.logger.info(msg)

    def __repr__(self) -> str:
        return f"<{self.component_name}>"

    # -------------------------------------------------------------------------
    # Callback / Observer Pattern
    # -------------------------------------------------------------------------

    def add_callback(self, callback: BaseCallback) -> None:
        """
        Register a callback listener to this component.

        Duplicate registrations are silently ignored.

        Args:
            callback: An instance of a class inheriting from BaseCallback.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _emit(self, event_method: str, **kwargs) -> None:
        """
        Broadcast an event to all registered callbacks.

        Dynamically invokes ``event_method`` on each callback if it exists.
        Exceptions raised by callbacks are caught and logged as warnings so
        that a misbehaving observer never interrupts the pipeline.

        Args:
            event_method: The method name to call on each callback
                          (e.g. ``"on_start"``, ``"on_finish"``).
            **kwargs: Arguments forwarded to the callback method.
        """
        for callback in self._callbacks:
            handler = getattr(callback, event_method, None)
            if callable(handler):
                try:
                    handler(component_name=self.component_name, **kwargs)
                except Exception as exc:
                    self._log(
                        f"Callback {type(callback).__name__}.{event_method} "
                        f"raised: {exc}",
                        level="warning",
                    )
