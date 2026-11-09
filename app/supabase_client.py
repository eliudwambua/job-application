import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

_supabase_client = None

def get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip()

def get_supabase_key() -> str:
    return os.getenv("SUPABASE_KEY", "").strip()

def is_supabase_configured() -> bool:
    url = get_supabase_url()
    key = get_supabase_key()
    return bool(url and key and "your-project" not in url)

def get_supabase():
    global _supabase_client
    if not is_supabase_configured():
        return None
    
    if _supabase_client is None:
        try:
            from supabase import create_client, Client
            url = get_supabase_url()
            key = get_supabase_key()
            _supabase_client = create_client(url, key)
        except Exception as e:
            print(f"[Supabase] Connection initialization error: {e}")
            return None

    return _supabase_client

