import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()  # loads .env file

# Read and sanitize environment variables (strip whitespace and surrounding quotes)
def _clean_env(name: str):
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    return v

SUPABASE_URL = _clean_env("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _clean_env("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise Exception("Supabase env variables not set")

# Create Supabase client
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)
