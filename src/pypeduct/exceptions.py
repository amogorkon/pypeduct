from typing import Any, Sequence


class PipeTransformError(Exception):
    """Enhanced exception with context for pipe transformation errors."""

    def __init__(
        self,
        message: str,
        exceptions: Sequence[Exception] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.inner_exceptions = exceptions or []
        self.context = context or {}

    def __str__(self) -> str:
        context_info = f"\nContext: {self.context}" if self.context else ""
        return f"{super().__str__()}{context_info}"
