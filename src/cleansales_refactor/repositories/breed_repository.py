"""
################################################################################
# 養殖記錄倉儲模組
#
# 這個模組提供了養殖記錄的數據訪問層，包括：
# 1. 基本的 CRUD 操作
# 2. 批次相關查詢
# 3. 統計數據查詢
#
# 主要功能：
# - 養殖記錄的增刪改查
# - 批次相關的數據查詢
# - 養殖統計數據獲取
################################################################################
"""

from typing import List, Literal, Protocol, runtime_checkable

from sqlmodel import Session, and_, asc, col, or_, select

from cleansales_refactor.domain.models import BatchState, BreedRecord
from cleansales_refactor.exporters import BreedRecordORM, ProcessingEvent


@runtime_checkable
class BreedRepositoryProtocol(Protocol):
    """養殖記錄倉儲協議

    定義了查詢服務（QueryService）所需的倉儲操作。
    主要包括：
    1. 根據批次狀態查詢
    2. 根據批次名稱查詢
    """

    def get_all(self, session: Session) -> List[BreedRecord]:
        """獲取所有養殖記錄

        Args:
            session (Session): 數據庫會話

        Returns:
            List[BreedRecord]: 所有養殖記錄列表
        """
        ...

    def get_by_batch_name(self, session: Session, batch_name: str) -> List[BreedRecord]:
        """根據批次名稱查詢養殖記錄

        Args:
            batch_name (str): 批次名稱（支持模糊匹配）

        Returns:
            List[BreedRecord]: 符合條件的養殖記錄列表
        """
        ...


class BreedRepository:
    """養殖記錄倉儲實現"""

    def get_all(self, session: Session) -> List[BreedRecord]:
        """獲取所有養殖記錄

        Args:
            session (Session): 數據庫會話

        Returns:
            List[BreedRecord]: 所有養殖記錄列表
        """
        statement = select(BreedRecordORM).where(
            and_(
                BreedRecordORM.event == ProcessingEvent.ADDED,
                col(BreedRecordORM.batch_name).is_not(None),
            )
        )
        breeds_orm = session.exec(statement).all()
        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]

    def get_by_batch_name(self, session: Session, batch_name: str) -> List[BreedRecord]:
        """根據批次名稱獲取養殖記錄

        Args:
            batch_name (str): 批次名稱

        Returns:
            List[BreedRecord]: 養殖記錄列表
        """
        return self._get_by_criteria(session, batch_name, "eq")

    def get_by_state(
        self, session: Session, state: BatchState | None
    ) -> List[BreedRecord]:
        """根據狀態獲取養殖記錄

        Args:
            session (Session): 數據庫會話
            state (BatchState | None): 批次狀態

        Returns:
            List[BreedRecord]: 養殖記錄列表
        """
        if state is None:
            statement = select(BreedRecordORM).where(
                BreedRecordORM.event == ProcessingEvent.ADDED
            )
        else:
            statement = select(BreedRecordORM).where(
                and_(
                    BreedRecordORM.is_completed == state.value,
                    BreedRecordORM.event == ProcessingEvent.ADDED,
                )
            )

        breeds_orm = session.exec(statement).all()
        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]

    def _get_by_criteria(
        self,
        session: Session,
        batch_name: str | None = None,
        condition: Literal["like", "eq"] = "like",
    ) -> List[BreedRecord]:
        """根據條件獲取養殖記錄

        Args:
            state (BatchState | None): 批次狀態
            batch_name (str | None): 批次名稱

        Returns:
            List[BreedRecord]: 養殖記錄列表
        """
        statement = select(BreedRecordORM).where(
            BreedRecordORM.event == ProcessingEvent.ADDED
        )
        if batch_name and condition == "eq":
            statement = statement.where(BreedRecordORM.batch_name == batch_name)
        elif batch_name and condition == "like":
            statement = statement.where(
                col(BreedRecordORM.batch_name).contains(batch_name)
            )
        return [BreedRecord(**orm.__dict__) for orm in session.exec(statement).all()]

    def get_not_completed_breeds(self, session: Session) -> List[BreedRecord]:
        """獲取未結案的養殖記錄

        Returns:
            List[BreedRecord]: 未結案的養殖記錄列表
        """
        stmt = (
            select(BreedRecordORM)
            .where(
                and_(
                    or_(
                        BreedRecordORM.is_completed != "結場",
                        col(BreedRecordORM.is_completed).is_(None),
                    ),
                    col(BreedRecordORM.batch_name).is_not(None),
                    BreedRecordORM.event == ProcessingEvent.ADDED,
                )
            )
            .order_by(asc(BreedRecordORM.breed_date))
        )
        breeds_orm = session.exec(stmt).all()

        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]

    def get_breeds_by_batch_name(
        self, session: Session, batch_name: str
    ) -> List[BreedRecord]:
        """根據批次名稱查詢養殖記錄

        Args:
            batch_name (str): 批次名稱（支持模糊匹配）

        Returns:
            List[BreedRecord]: 符合條件的養殖記錄列表
        """
        stmt = select(BreedRecordORM).where(
            and_(
                col(BreedRecordORM.batch_name).contains(batch_name),
                BreedRecordORM.event == ProcessingEvent.ADDED,
            )
        )
        breeds_orm = session.exec(stmt).all()
        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]
