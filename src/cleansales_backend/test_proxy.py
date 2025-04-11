# 直接發送一個簡單的 GET 請求測試
import httpx

SUPABASE_URL = "http://192.168.1.200:8000"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzQzOTU1MjAwLAogICJleHAiOiAxOTAxNzIxNjAwCn0.fOJYaoMHXtiUGcBUGENwkwMlGmnaFUmknG9Bbl9iuDw"

url = f"{SUPABASE_URL}/rest/v1/breedrecordorm?select=*"
headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


async def test() -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        # print(resp.status_code)
        print(resp.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())
