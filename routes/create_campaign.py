from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List
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


# Email content request model
class EmailContentCreate(BaseModel):
    subject: str
    body: str
    redirect_url: HttpUrl  # validates URL automatically


# Combined request model (campaign + email)
class CampaignWithEmailCreate(BaseModel):
    campaign: CampaignCreate
    email: EmailContentCreate


@router.post("/campaigns/{user_id}")
def create_campaign(user_id: str, payload: CampaignWithEmailCreate):
    try:

        # 1️⃣ Prepare campaign data
        campaign_data = payload.campaign.model_dump(mode='json')
        campaign_data["user_id"] = user_id
        campaign_data["created_at"] = datetime.utcnow().isoformat()

        # 2️⃣ Insert campaign
        campaign_result = supabase.table("campaigns").insert(campaign_data).execute()

        if not campaign_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert campaign")

        inserted_campaign = campaign_result.data[0]
        campaign_id = inserted_campaign["id"]

        # 3️⃣ Prepare email content data
        email_data = payload.email.model_dump(mode='json')
        email_data["campaign_id"] = campaign_id
        email_data["content"] = email_data.pop("body")  # rename body → content
        email_data["redirect_url"] = str(email_data["redirect_url"])  # ensure plain string

        # 4️⃣ Insert email content
        email_result = supabase.table("email_contents").insert(email_data).execute()

        if not email_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert email content")

        inserted_email = email_result.data[0]

        # 5️⃣ Insert activity log
        activity_log = insert_activity_log(
            user_id=user_id,
            campaign_id=campaign_id,
            action="Started lead scraping",
            metadata=campaign_data
        )

        # 6️⃣ Return response
        return {
            "campaign": inserted_campaign,
            "email_content": inserted_email,
            "activity_log": activity_log
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))