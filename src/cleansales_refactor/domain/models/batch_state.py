from enum import Enum


class BatchState(Enum):
    """批次狀態列舉

    用於追蹤雞隻批次的當前狀態，包含:
    - BREEDING: 養殖階段，雞隻正在生長
    - SALE: 銷售階段，開始進行銷售
    - COMPLETED: 結案階段，該批次已完成所有銷售
    """

    BREEDING = "養殖中"
    SALE = "銷售中"
    COMPLETED = "結案"
