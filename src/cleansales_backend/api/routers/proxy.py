import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from httpx import AsyncClient

from .. import get_client, settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.api_route(
    "/proxy/rest/v1/{table}", methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
)
async def supabase_proxy(
    table: str,
    request: Request,
    client: Annotated[AsyncClient, Depends(get_client)],
) -> Response:
    # 動態組裝 URL
    url = f"/rest/v1/{table}"

    logger.info(f"Proxying request to {url}")

    # 組裝 header
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 傳入參數
    params = dict(request.query_params)
    method = request.method

    try:
        # 根據 HTTP 方法處理請求
        if method == "GET":
            resp = await client.request(method, url, headers=headers, params=params)
        else:
            # 對於非 GET 請求，讀取 body
            body = await request.body()
            resp = await client.request(
                method, url, headers=headers, params=params, content=body
            )

        # 檢查響應狀態碼
        if resp.status_code >= 400:
            logger.error(f"Error from Supabase: {resp.status_code}, {resp.text}")
            return Response(
                content=resp.text,
                status_code=resp.status_code,
                media_type="application/json",
            )

        # 正常返回 JSON 響應
        return Response(
            content=resp.text,
            status_code=resp.status_code,
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return Response(
            content=str(e),
            status_code=500,
            media_type="application/json",
        )


async def proxy_health_check() -> int:
    try:
        # 檢查 Supabase 是否健康
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/ json",
        }
        resp = await get_client().get("/rest/v1/breedrecordorm", headers=headers)
        return resp.status_code
    except Exception as e:
        logger.error(f"Proxy health check error: {str(e)}")
        return 500
