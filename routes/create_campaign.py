from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase_client import supabase
from routes.activity_log import insert_activity_log
from datetime import datetime

router = APIRouter()


# Campaign request model
class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    industry: str
    area: str
    city: str
    state: str
    country: str
    job_titles: List[str]
    requested_leads: int
    status: str
    black_listed_domains: Optional[List[str]] 


# Email content request model
class EmailContentCreate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    modify_with_ai: bool = False


@router.post("/campaigns/{user_id}")
def create_campaign(user_id: str, payload: CampaignCreate):
    try:

        # 1️⃣ Prepare campaign data
        campaign_data = payload.model_dump(mode='json')
        campaign_data["user_id"] = user_id
        campaign_data["created_at"] = datetime.utcnow().isoformat()

        # 2️⃣ Insert campaign
        campaign_result = supabase.table("campaigns").insert(campaign_data).execute()

        if not campaign_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert campaign")

        inserted_campaign = campaign_result.data[0]
        campaign_id = inserted_campaign["id"]

        # 4️⃣ Insert activity log
        activity_log = insert_activity_log(
            user_id=user_id,
            campaign_id=campaign_id,
            action="Started lead scraping",
            metadata=campaign_data
        )

        # 5️⃣ Return response
        return {
            "campaign": inserted_campaign,
            "activity_log": activity_log
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/saved_email_contents/{user_id}")
def get_email_contents(user_id: str, campaign_id: str):
    try:
        result = supabase.table("email_contents") \
            .select("id, subject, content, modify_with_ai, created_at") \
            .eq("user_id", user_id) \
            .eq("campaign_id", campaign_id) \
            .order("created_at", desc=True) \
            .execute()
        return {"email_contents": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email_contents/{user_id}")
def create_email_content(user_id: str, campaign_id: str, payload: EmailContentCreate):
    try:
        if not payload.subject or not payload.body:
            raise HTTPException(status_code=400, detail="subject and body are required")

        email_data = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "subject": payload.subject,
            "content": payload.body,
            "modify_with_ai": payload.modify_with_ai,
        }

        email_result = supabase.table("email_contents").insert(email_data).execute()

        if not email_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert email content")

        return {"email_content": email_result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))