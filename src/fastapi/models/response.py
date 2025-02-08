from typing import Any

from sqlmodel import SQLModel


class ResponseModel(SQLModel):
    status: str
    msg: str
    content: dict[str, Any]
