from enum import Enum


class BatchState(Enum):
    """State of a batch."""
    
    BREEDING = "養殖中"
    SALE = "銷售中"
    COMPLETED = "結案"

