import json
import logging
from sqlite3 import Connection, Row

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.database.init import init_db
from cleansales_backend.handlers.upload_handler import UploadCommandHandler

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"

init_db()

connection = Connection("./data/sqlite.db")
connection.row_factory = Row

# Create API router
router = APIRouter()

upload_handler = UploadCommandHandler(DB_PATH)

# This router will be included in main.py


@router.post("/upload")
async def api_upload(file: UploadFile = File(...)):
    """API上傳路由，返回JSON格式"""
    command = UploadFileCommand(file=file)
    result = await upload_handler.handle(command)

    # 使用 UploadResult 的 to_json 方法
    return JSONResponse(content=json.loads(result.to_json(ensure_ascii=False)))


@router.get(
    "/sales",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_sales_data(page: int = Query(default=1, ge=1), page_size: int = Query(default=100, ge=10, le=100)):
    """Fetch sales data with pagination and breed information.

    This endpoint retrieves sales data joined with the breed information
    to calculate the age of the chickens at the time of sale. The data
    is ordered by sale date in descending order and supports pagination
    through the `offset` and `page_size` parameters.

    Args:
        page (int, optional): The page number for pagination. Defaults to 1.
        page_size (int, optional): The number of records per page. Defaults to 100.

    Returns:
        JSONResponse: A JSON response containing the sales data.

    Raises:
        HTTPException: If there is an error fetching the sales data.
    """
    stmt = """
        SELECT
            sub_q.chicken_breed,
            sale.handler,
            CAST(JULIANDAY(sale.sale_date) - JULIANDAY(sub_q.breed_date) + 1 AS INTEGER) AS dayage,
            sale.sale_date,
            sale.batch_name,
            sale.customer,
            sale.male_count,
            sale.female_count,
            CASE
                WHEN total_price IS NULL
                OR (male_count + female_count) = 0 THEN NULL
                ELSE total_price / (male_count + female_count)
            END AS avg_price,
            CASE
                WHEN male_count = 0
                OR total_weight IS NULL THEN NULL
                ELSE ((total_weight - male_count * 0.8) / (male_count + female_count)) + 0.8
            END AS male_avg_weight,
            CASE
                WHEN female_count = 0
                OR total_weight IS NULL THEN NULL
                ELSE (total_weight - male_count * 0.8) / (male_count + female_count)
            END AS female_avg_weight,
            sale.total_weight,
            sale.total_price,
            sale.male_price,
            sale.female_price,
            sale.unpaid,
            sale.created_at
        FROM
            sale
            JOIN (
                SELECT
                    batch_name,
                    MIN(breed_date) AS breed_date,
                    chicken_breed
                FROM
                    breed
                GROUP BY
                    batch_name
            ) AS sub_q ON sale.batch_name = sub_q.batch_name
        ORDER BY sale.sale_date DESC
        LIMIT :page_size OFFSET :page
    """
    try:
        result = connection.execute(stmt, {"page_size": page_size, "page": (page - 1) * page_size}).fetchall()
        data = [dict(row) for row in result]
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"獲取銷售資料時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))
