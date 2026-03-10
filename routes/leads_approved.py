from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase_client import supabase
from routes.activity_log import insert_activity_log
from services.sent_email import send_email
from datetime import datetime
import uuid

router = APIRouter()


# Request model for each lead approval
class LeadApproval(BaseModel):
    lead_id: str
    approved: bool


# Request body model
class LeadsApprovalRequest(BaseModel):
    user_id: str
    campaign_id: str
    type: str  # email event type (dynamic)
    email_content_id: Optional[str] = None
    leads: List[LeadApproval]


@router.post("/leads-approved")
def approve_leads(payload: LeadsApprovalRequest):
    try:
        updated_leads = []

        # 1️⃣ Update leads table
        for lead in payload.leads:
            if lead.approved:
                supabase.table("leads") \
                    .update({"status": "approved"}) \
                    .eq("id", lead.lead_id) \
                    .eq("user_id", payload.user_id) \
                    .execute()

                updated_leads.append({
                    "lead_id": lead.lead_id,
                    "status": "approved"
                })

        # 2️⃣ Insert email events and send emails
        for lead in payload.leads:
            if lead.approved:
                # Fetch email from leads table
                lead_row = supabase.table("leads") \
                    .select("email") \
                    .eq("id", lead.lead_id) \
                    .single() \
                    .execute()
                lead_email = lead_row.data.get("email") if lead_row.data else None

                email_event = {
                    "id": str(uuid.uuid4()),
                    "user_id": payload.user_id,
                    "campaign_id": payload.campaign_id,
                    "lead_id": lead.lead_id,
                    "event_type": payload.type,
                    "email_content_id": payload.email_content_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                supabase.table("email_events").insert(email_event).execute()

        # 3️⃣ Insert activity log
        activity_log = insert_activity_log(
            user_id=payload.user_id,
            campaign_id=payload.campaign_id,
            action="Leads approved",
            metadata={"leads": [lead.dict() for lead in payload.leads]}
        )

        # 4️⃣ Return response
        return {
            "updated_leads": updated_leads,
            "activity_log": {
                "user_id": activity_log["user_id"],
                "campaign_id": activity_log["campaign_id"],
                "action": activity_log["action"],
                "created_at": activity_log["created_at"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
