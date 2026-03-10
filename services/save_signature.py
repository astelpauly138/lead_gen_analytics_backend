"""
Email Signature Service
Handles saving and retrieving per-user email signatures.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    raise RuntimeError("Missing env vars: SUPABASE_URL, SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

router = APIRouter(tags=["Signature"])


class SignatureRequest(BaseModel):
    user_id: str
    signature_html: str


@router.post("/signature/save")
def save_signature(req: SignatureRequest):
    log.info("Saving signature for user_id: %s", req.user_id)
    existing = supabase.table("email_signatures").select("user_id").eq("user_id", req.user_id).execute()
    if existing.data:
        supabase.table("email_signatures").update({"signature_html": req.signature_html}).eq("user_id", req.user_id).execute()
    else:
        supabase.table("email_signatures").insert({"user_id": req.user_id, "signature_html": req.signature_html}).execute()
    return {"message": "Signature saved."}


@router.get("/signature/{user_id}")
def get_signature(user_id: str):
    log.info("Fetching signature for user_id: %s", user_id)
    res = supabase.table("email_signatures").select("signature_html").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No signature found.")
    return {"signature_html": res.data[0]["signature_html"]}


@router.delete("/signature/{user_id}")
def delete_signature(user_id: str):
    log.info("Deleting signature for user_id: %s", user_id)
    res = supabase.table("email_signatures").select("user_id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No signature found.")
    supabase.table("email_signatures").delete().eq("user_id", user_id).execute()
    return {"message": "Signature deleted."}
