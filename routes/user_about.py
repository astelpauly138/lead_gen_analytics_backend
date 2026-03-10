import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from supabase_client import supabase

logger = logging.getLogger(__name__)

router = APIRouter()


class Service(BaseModel):
    name: str
    description: Optional[str] = ''


class AboutUpsert(BaseModel):
    job_title: Optional[str] = None
    company_website: Optional[str] = None
    services_offering: Optional[List[Service]] = None


@router.get("/user-about/{user_id}")
def get_user_about(user_id: str):
    logger.info(f"GET /user-about/{user_id}")

    about_result = supabase.schema("public") \
        .table("user_about") \
        .select("job_title, company_website") \
        .eq("user_id", user_id) \
        .execute()
    logger.info(f"user_about result: {about_result.data}")

    services_result = supabase.schema("public") \
        .table("user_services") \
        .select("service_name, service_description") \
        .eq("user_id", user_id) \
        .execute()
    logger.info(f"user_services result: {services_result.data}")

    about = about_result.data[0] if about_result.data else {}
    services = [
        {"name": s["service_name"], "description": s.get("service_description", "")}
        for s in (services_result.data or [])
    ]

    return {
        "job_title": about.get("job_title"),
        "company_website": about.get("company_website"),
        "services_offering": services,
    }


@router.put("/user-about/{user_id}")
def upsert_user_about(user_id: str, body: AboutUpsert):
    logger.info(f"PUT /user-about/{user_id} body={body}")

    # Upsert user_about
    about_payload = {
        "user_id": user_id,
        "job_title": body.job_title,
        "company_website": body.company_website,
    }
    about_result = supabase.schema("public") \
        .table("user_about") \
        .upsert(about_payload, on_conflict="user_id") \
        .execute()
    logger.info(f"upsert user_about result: {about_result.data}")

    # Replace services: delete existing then insert new
    supabase.schema("public") \
        .table("user_services") \
        .delete() \
        .eq("user_id", user_id) \
        .execute()
    logger.info(f"Deleted existing services for user_id: {user_id}")

    services = body.services_offering or []
    if services:
        services_payload = [
            {
                "user_id": user_id,
                "service_name": s.name,
                "service_description": s.description,
            }
            for s in services
        ]
        services_result = supabase.schema("public") \
            .table("user_services") \
            .insert(services_payload) \
            .execute()
        logger.info(f"Inserted services: {services_result.data}")

    return {
        "job_title": body.job_title,
        "company_website": body.company_website,
        "services_offering": [{"name": s.name, "description": s.description} for s in services],
    }
