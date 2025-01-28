from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ErrorMessage:
    message: str
    data: dict[str, Any]
    extra: dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
