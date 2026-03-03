from fastapi import APIRouter, HTTPException
from supabase_client import supabase

router = APIRouter()

def get_profile(user_id: str):
    result = supabase.schema("public") \
        .table("profiles") \
        .select("first_name","last_name","company_name") \
        .eq("id", user_id) \
        .execute()

    return result.data

@router.get("/profile/{user_id}")
def profile(user_id: str):
    data = get_profile(user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return data[0]
