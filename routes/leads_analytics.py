from fastapi import APIRouter, HTTPException
from supabase_client import supabase

router = APIRouter()


@router.get("/lead-analytics/{user_id}")
def get_lead_list(user_id: str):
    try:

        result = (
            supabase.schema("analytics")
            .table("lead_analytics")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "lead_list": result.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/{user_id}")
def get_user_leads(user_id: str):
    try:
        result = (
            supabase.table("leads")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        leads = result.data or []
        pending_leads = [l for l in leads if l.get("status") == "pending"]
        approved_leads = [l for l in leads if l.get("status") == "approved"]

        return {
            "pending_leads": pending_leads,
            "approved_leads": approved_leads
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
