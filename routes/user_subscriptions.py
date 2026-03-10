import logging
from fastapi import APIRouter
from supabase_client import supabase

logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_subscription(user_id: str):
    logger.info(f"Querying subscription for user_id: {user_id}")
    result = supabase.schema("analytics") \
        .table("user_subscription_details") \
        .select("expiration_date, status, plan_name") \
        .eq("user_id", user_id) \
        .execute()
    logger.info(f"Supabase raw result: {result}")
    return result.data

@router.get("/user-subscription/{user_id}")
def user_subscription(user_id: str):
    logger.info(f"GET /user-subscription/{user_id} called")
    data = get_user_subscription(user_id)
    logger.info(f"Data returned from query: {data}")
    if not data:
        logger.warning(f"No subscription found for user_id: {user_id}")
        return None
    logger.info(f"Returning subscription: {data[0]}")
    return data[0]
