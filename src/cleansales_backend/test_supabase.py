import json

from cleansales_backend.core import get_settings
from supabase import Client, create_client

settings = get_settings()
url = settings.SUPABASE_CLIENT_URL
key = settings.SUPABASE_KEY

client: Client = create_client(
    supabase_url=url,
    supabase_key=key,
)

response = client.table("breedrecordorm").select("*").execute()

print(json.dumps(response.data, ensure_ascii=False, indent=4))
