from dataclasses import dataclass
from typing import Optional, Dict, Any
from starlette.datastructures import UploadFile


@dataclass
class UploadFileCommand:
    file: UploadFile
    metadata: Optional[Dict[str, Any]] = None