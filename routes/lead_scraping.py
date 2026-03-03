from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase_client import supabase
from routes.activity_log import insert_activity_log
from datetime import datetime
import uuid

router = APIRouter()


# Request model for each lead
class Lead(BaseModel):
    Employee_Name: str
    Work_Email: Optional[str] = None
    Company: str
    Work_Mobile_No: Optional[str] = None
    Category: Optional[str] = None
    Position: Optional[str] = None
    Email_Status: Optional[str] = None
    Website: Optional[str] = None
    Domain: Optional[str] = None
    Location: Optional[str] = None
    Address: Optional[str] = None
    Promotion_Status: Optional[str] = None


# Request body model
class ScrapedLeads(BaseModel):
    campaign_id: str
    user_id: str
    leads: List[Lead]


@router.post("/lead-scraping")
def insert_scraped_leads(payload: ScrapedLeads):
    try:
        inserted_leads = []

        # 1️⃣ Insert each lead
        for lead in payload.leads:
            lead_row = {
                "id": str(uuid.uuid4()),
                "campaign_id": payload.campaign_id,
                "user_id": payload.user_id,
                "name": lead.Employee_Name,
                "email": lead.Work_Email,
                "company": lead.Company,
                "phone": lead.Work_Mobile_No,
                "status": "pending",
                "quality_score": None,
                "last_contacted": None,
                "created_at": datetime.utcnow().isoformat(),
                "category": lead.Category,
                "position": lead.Position,
                "email_status": lead.Email_Status,
                "website": lead.Website,
                "domain": lead.Domain,
                "location": lead.Location,
                "address": lead.Address,
                "promotion_status": lead.Promotion_Status
            }

            supabase.table("leads").insert(lead_row).execute()
            inserted_leads.append(lead_row)  # keep track of inserted leads

        # 2️⃣ Insert activity log for lead scraping
        activity_log = insert_activity_log(
            user_id=payload.user_id,
            campaign_id=payload.campaign_id,
            action="Leads scraped",
            metadata={"leads_count": len(payload.leads)}  # optional metadata
        )

        # 3️⃣ Return both inserted leads and activity log
        return {
            "inserted_leads": inserted_leads,
            "activity_log": {
                "user_id": activity_log["user_id"],
                "campaign_id": activity_log["campaign_id"],
                "action": activity_log["action"],
                "created_at": activity_log["created_at"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
