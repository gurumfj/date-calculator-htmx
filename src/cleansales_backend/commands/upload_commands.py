from dataclasses import dataclass
from typing import Any, Dict, Optional

from starlette.datastructures import UploadFile


@dataclass
class UploadFileCommand:
    file: UploadFile
    metadata: Optional[Dict[str, Any]] = None