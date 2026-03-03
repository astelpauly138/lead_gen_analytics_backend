from fastapi import APIRouter, HTTPException
from supabase_client import supabase
import asyncio

router = APIRouter()


def get_campaign_kpis_sync(user_id: str):
    result = supabase.schema("analytics") \
        .table("campaigns_kpis") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

    return result.data


def get_campaign_kpis_all_sync(user_id: str):
    result = supabase.schema("analytics") \
        .table("campaigns_kpi_all") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()

    return result.data


@router.get("/campaign-kpis/{user_id}")
async def get_campaign_kpis(user_id: str):
    try:
        kpis_task = asyncio.to_thread(get_campaign_kpis_sync, user_id)
        kpis_all_task = asyncio.to_thread(get_campaign_kpis_all_sync, user_id)

        kpis_result, kpis_all_result = await asyncio.gather(kpis_task, kpis_all_task)

        return {
            "campaign_kpis": kpis_result,
            "campaign_kpis_all": kpis_all_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
