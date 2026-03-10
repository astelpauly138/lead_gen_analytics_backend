"""
Email Configuration Service
Handles SMTP credential verification and storage per user.
"""

import os
import smtplib
import logging
import dns.resolver
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    raise RuntimeError("Missing env vars: SUPABASE_URL, SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

TABLE_CLIENTS = "client_emails"

KNOWN_PROVIDERS = {
    "gmail": {
        "mx_keywords": ["google.com", "googlemail.com"],
        "host": "smtp.gmail.com",
        "port": 587,
        "help": "Use an App Password: https://myaccount.google.com/apppasswords (2FA required)"
    },
    "outlook": {
        "mx_keywords": ["outlook.com", "protection.outlook.com"],
        "host": "smtp.office365.com",
        "port": 587,
        "help": "Use your Microsoft password or App Password if MFA is enabled"
    },
    "yahoo": {
        "mx_keywords": ["yahoodns.net", "yahoo.com"],
        "host": "smtp.mail.yahoo.com",
        "port": 587,
        "help": "Use an App Password from Yahoo Account Security settings"
    },
}

router = APIRouter(tags=["Email Config"])


# ── MX LOOKUP ──────────────────────────────────────────────
def lookup_mx_provider(domain: str) -> tuple:
    log.info("MX lookup for domain: %s", domain)
    try:
        records = dns.resolver.resolve(domain, "MX")
        primary_mx = str(sorted(records, key=lambda r: r.preference)[0].exchange).rstrip(".").lower()
        log.info("Primary MX: %s", primary_mx)
    except Exception as e:
        log.error("MX lookup failed for %s: %s", domain, e)
        raise HTTPException(
            status_code=400,
            detail=f"Could not resolve MX records for '{domain}'. Provide smtp_host manually."
        )
    for provider, cfg in KNOWN_PROVIDERS.items():
        if any(kw in primary_mx for kw in cfg["mx_keywords"]):
            log.info("Matched provider: %s → %s:%s", provider, cfg["host"], cfg["port"])
            return provider, cfg["host"], cfg["port"]
    log.info("No known provider matched. Using custom: %s:587", primary_mx)
    return "custom", primary_mx, 587


def detect_smtp(email: str, custom_host: Optional[str], custom_port: Optional[int]) -> tuple:
    if custom_host:
        log.info("Using custom SMTP: %s:%s", custom_host, custom_port or 587)
        return "custom", custom_host, custom_port or 587
    return lookup_mx_provider(email.split("@")[-1].lower())


# ── SMTP TEST ──────────────────────────────────────────────
def test_smtp_credentials(email: str, password: str, smtp_host: str, smtp_port: int, provider: str = "custom"):
    log.info("Testing SMTP for %s via %s:%s", email, smtp_host, smtp_port)
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.starttls()
            s.login(email, password)
            log.info("SMTP login successful for %s", email)
    except smtplib.SMTPAuthenticationError:
        hint = KNOWN_PROVIDERS.get(provider, {}).get("help", "Check your credentials.")
        raise HTTPException(status_code=401, detail=f"Authentication failed. {hint}")
    except smtplib.SMTPConnectError:
        raise HTTPException(status_code=400, detail=f"Cannot connect to {smtp_host}:{smtp_port}.")
    except TimeoutError:
        raise HTTPException(status_code=408, detail=f"Connection to {smtp_host}:{smtp_port} timed out.")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")


# ── DB HELPERS ─────────────────────────────────────────────
def get_client_by_user(user_id: str) -> Optional[dict]:
    log.info("Fetching email config for user_id: %s", user_id)
    res = supabase.table(TABLE_CLIENTS).select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


# ── SCHEMAS ────────────────────────────────────────────────
class CheckDomainRequest(BaseModel):
    email: EmailStr

class AddClientRequest(BaseModel):
    user_id: str
    email: EmailStr
    password: str
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None


# ── ROUTES ─────────────────────────────────────────────────
@router.post("/clients/check-domain")
def check_domain(req: CheckDomainRequest):
    log.info("check-domain for: %s", req.email)
    provider, host, port = detect_smtp(req.email, None, None)
    return {
        "detected_provider": provider,
        "smtp_host": host,
        "smtp_port": port,
        "known_provider": provider in KNOWN_PROVIDERS,
        "hint": KNOWN_PROVIDERS.get(provider, {}).get("help", "Enter your SMTP credentials.")
    }


@router.get("/clients/by-user/{user_id}")
def get_client_config(user_id: str):
    log.info("get-client-config for user_id: %s", user_id)
    client = get_client_by_user(user_id)
    if not client:
        raise HTTPException(status_code=404, detail="No email config found for this user.")
    return {
        "email": client["email"],
        "password": client["password"],
        "provider": client["provider"],
        "smtp_host": client["smtp_host"],
        "smtp_port": client["smtp_port"],
        "is_verified": client["is_verified"],
    }


@router.delete("/clients/by-user/{user_id}")
def delete_client_config(user_id: str):
    log.info("delete-client-config for user_id: %s", user_id)
    client = get_client_by_user(user_id)
    if not client:
        raise HTTPException(status_code=404, detail="No email config found for this user.")
    supabase.table(TABLE_CLIENTS).delete().eq("user_id", user_id).execute()
    log.info("Deleted email config for user_id: %s", user_id)
    return {"message": "Email configuration deleted."}


@router.post("/clients/add")
def add_client(req: AddClientRequest):
    log.info("=== /clients/add for user_id: %s email: %s ===", req.user_id, req.email)

    provider, smtp_host, smtp_port = detect_smtp(req.email, req.smtp_host, req.smtp_port)
    test_smtp_credentials(req.email, req.password, smtp_host, smtp_port, provider)

    existing = get_client_by_user(req.user_id)
    if existing:
        log.info("Updating existing config for user_id: %s", req.user_id)
        supabase.table(TABLE_CLIENTS).update({
            "email": req.email,
            "provider": provider,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "password": req.password,
            "is_verified": True,
        }).eq("user_id", req.user_id).execute()
        return {
            "message": f"Credentials updated for {req.email}.",
            "detected_provider": provider,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
        }

    log.info("Inserting new config for user_id: %s", req.user_id)
    supabase.table(TABLE_CLIENTS).insert({
        "user_id": req.user_id,
        "email": req.email,
        "provider": provider,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "password": req.password,
        "is_verified": True,
    }).execute()
    return {
        "message": f"Credentials verified and saved for {req.email}.",
        "detected_provider": provider,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
    }
