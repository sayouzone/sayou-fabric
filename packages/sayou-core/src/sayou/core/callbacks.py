from abc import ABC
from typing import Any


class BaseCallback(ABC):
    """
    Abstract base class for event handling across the Sayou ecosystem.

    This interface defines the standard hooks that any component (Connector,
    Refinery, Loader, …) can trigger.  Observers (e.g. progress loggers,
    telemetry tracers) should inherit from this class and override only the
    methods they are interested in.

    All methods have no-op default implementations so subclasses only need
    to override what they care about.
    """

    def on_start(self, component_name: str, input_data: Any, **kwargs) -> None:
        """
        Triggered when a component starts processing a unit of work.

        Args:
            component_name: Name of the emitting component.
            input_data: The input payload being processed.
            **kwargs: Additional context-specific metadata.
        """
        pass

    def on_finish(
        self,
        component_name: str,
        result_data: Any,
        success: bool,
        **kwargs,
    ) -> None:
        """
        Triggered when a component finishes processing a unit of work.

        Args:
            component_name: Name of the emitting component.
            result_data: The output payload produced by the component.
            success: Whether the operation completed without error.
            **kwargs: Additional context-specific metadata (e.g. elapsed time).
        """
        pass

    def on_error(
        self,
        component_name: str,
        error: Exception,
        **kwargs,
    ) -> None:
        """
        Triggered when an exception occurs during processing.

        Args:
            component_name: Name of the component where the error occurred.
            error: The exception object caught.
            **kwargs: Additional context-specific metadata.
        """
        pass

    def on_event(
        self,
        event_name: str,
        payload: Any = None,
        **kwargs,
    ) -> None:
        """
        Triggered for custom or generic events not covered by start/finish/error.

        Use this for granular updates such as ``"progress_update"`` or
        ``"state_change"``.

        Args:
            event_name: Identifier of the custom event.
            payload: Data associated with the event (optional).
            **kwargs: Additional metadata.
        """
        pass
