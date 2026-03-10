import logging
from fastapi import APIRouter
from supabase_client import supabase

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/modify-content-check/{user_id}")
def modify_content_check(user_id: str):

    logger.info(f"GET /modify-content-check/{user_id}")

    result = supabase.schema("analytics") \
        .table("user_about_status") \
        .select("about_exists") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    logger.info(f"user_about_status result for {user_id}: {result.data}")
    logger.info("---------------------------------") 
    logger.info(f"Full result object: {result}")
    logger.info("---------------------------------")
    if result.data:
        about_exists = result.data.get("about_exists", False)
        result_val = 1 if about_exists else 0
        logger.info(f"about_exists={about_exists} → result={result_val} for user_id={user_id}")
        return {"result": result_val}

    logger.info(f"No row found in user_about_status for user_id={user_id} — returning 0")
    return {"result": 0}