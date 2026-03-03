from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from supabase_client import supabase

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    lead_ids: List[str]


@router.delete("/delete-leads")
def delete_leads_bulk(payload: BulkDeleteRequest):
    if not payload.lead_ids:
        raise HTTPException(status_code=400, detail="No lead IDs provided")

    response = (
        supabase.table("leads")
        .delete()
        .in_("id", payload.lead_ids)
        .execute()
    )

    return {
        "status": "success",
        "deleted_count": len(response.data or []),
        "deleted_ids": payload.lead_ids
    }
