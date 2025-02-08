import logging
from typing import List

import pandas as pd
from sqlmodel import Session, and_, asc, or_, select

from cleansales_refactor import CleanSalesService, SourceData
from cleansales_refactor.exporters import BreedRecordORM, ProcessingEvent
from event_bus import Event, EventBus
from fastapi import Depends, UploadFile

from ..core.database import get_session
from ..core.event_bus import get_event_bus
from ..core.events import ProcessEvent as ApiProcessEvent
from ..models.breed import (
    BreedCardModel,
    BreedResponseModel,
    BreedSectionModel,
    SubCardInfo,
)
from ..models.response import ResponseModel

logger = logging.getLogger(__name__)


class PostApiDependency:
    def __init__(self, event_bus: EventBus, session: Session) -> None:
        self.service = CleanSalesService()
        self.event_bus = event_bus
        self.session = session

    def sales_processpipline(self, upload_file: UploadFile) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        result = self.service.execute_clean_sales(self.session, source_data)
        if result.status == "success":
            self.event_bus.publish(
                Event(
                    event=ApiProcessEvent.SALES_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )
        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    def breed_processpipline(self, upload_file: UploadFile) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        result = self.service.execute_clean_breeds(self.session, source_data)
        if result.status == "success":
            self.event_bus.publish(
                Event(
                    event=ApiProcessEvent.BREEDS_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )
        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    def process_breed_records(
        self, records: List[BreedRecordORM]
    ) -> BreedResponseModel:
        # 依批次分組
        batch_groups: dict[str, List[BreedRecordORM]] = {}
        for record in records:
            batch_name = record.batch_name or "未命名批次"
            if batch_name not in batch_groups:
                batch_groups[batch_name] = []
            batch_groups[batch_name].append(record)

        # 處理每個批次的資料
        all_cards = []
        for batch_name, batch_records in batch_groups.items():
            first_record = batch_records[0]

            if len(batch_records) == 1:
                # 單筆記錄
                card = BreedCardModel(
                    batch_name=batch_name,
                    farm_name=first_record.farm_name,
                    address=first_record.address,
                    farmer_name=first_record.farmer_name,
                    chicken_breed=first_record.chicken_breed or "未分類",
                    total_male=first_record.male or 0,
                    total_female=first_record.female or 0,
                    veterinarian=first_record.veterinarian,
                    is_completed=first_record.is_completed,
                    breed_date=first_record.breed_date,
                    supplier=first_record.supplier,
                    sub_cards=[],
                )
            else:
                # 多筆記錄
                card = BreedCardModel(
                    batch_name=batch_name,
                    farm_name=first_record.farm_name,
                    address=first_record.address,
                    farmer_name=first_record.farmer_name,
                    chicken_breed=first_record.chicken_breed or "未分類",
                    total_male=sum(r.male or 0 for r in batch_records),
                    total_female=sum(r.female or 0 for r in batch_records),
                    veterinarian=first_record.veterinarian,
                    is_completed=first_record.is_completed,
                    breed_date=None,
                    supplier=None,
                    sub_cards=[
                        SubCardInfo(
                            breed_date=r.breed_date,
                            supplier=r.supplier,
                            male=r.male or 0,
                            female=r.female or 0,
                        )
                        for r in batch_records
                    ],
                )
            all_cards.append(card)

        # 依品種分組
        breed_sections: dict[str, List[BreedCardModel]] = {}
        for card in all_cards:
            breed_type = card.chicken_breed
            if breed_type not in breed_sections:
                breed_sections[breed_type] = []
            breed_sections[breed_type].append(card)

        # 建立最終回應
        sections = []
        total_male = 0
        total_female = 0
        total_batches = len(all_cards)

        for breed_type, cards in breed_sections.items():
            section_total_male = sum(card.total_male for card in cards)
            section_total_female = sum(card.total_female for card in cards)
            total_male += section_total_male
            total_female += section_total_female

            sections.append(
                BreedSectionModel(
                    breed_type=breed_type,
                    total_batches=len(cards),
                    total_male=section_total_male,
                    total_female=section_total_female,
                    cards=cards,
                )
            )

        return BreedResponseModel(
            total_batches=total_batches,
            total_male=total_male,
            total_female=total_female,
            sections=sorted(sections, key=lambda x: x.breed_type),
        )

    def get_breeds_is_not_completed(self) -> ResponseModel:
        stmt = (
            select(BreedRecordORM)
            .where(
                and_(
                    or_(
                        BreedRecordORM.is_completed != "結場",
                        BreedRecordORM.is_completed == None,
                    ),
                    BreedRecordORM.event == ProcessingEvent.ADDED,
                )
            )
            .order_by(asc(BreedRecordORM.breed_date))
        )
        breeds = self.session.exec(stmt).all()

        breed_data = self.process_breed_records(list(breeds))

        return ResponseModel(
            status="success",
            msg=f"成功取得未結場入雛資料 {len(breeds)} 筆",
            content=breed_data.model_dump(),
        )


def get_api_dependency(
    event_bus: EventBus = Depends(get_event_bus),
    session: Session = Depends(get_session),
) -> PostApiDependency:
    return PostApiDependency(event_bus=event_bus, session=session)
