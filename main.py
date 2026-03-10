from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.campaign_kpi import router as campaign_router
from routes.leads_analytics import router as lead_router
from routes.create_campaign import router as campaign_create_router
from routes.lead_scraping import router as lead_scraping_router
from routes.leads_approved import router as leads_approved_router
from routes.profile import router as profile_router
from services.export_leads import router as export_router
from routes.delete_leads import router as delete_leads_router
from services.email_verification import router as email_config_router
from services.save_signature import router as signature_router
from routes.user_subscriptions import router as user_subscriptions_router
from routes.user_about import router as user_about_router
from routes.user_documents import router as user_documents_router
from routes.modify_content_check import router as modify_content_check_router

app = FastAPI()

# Middleware to log POST request bodies and 422 errors
@app.middleware("http")
async def log_post_bodies(request: Request, call_next):
    if request.method == "POST":
        body = await request.body()
        print(f"\n>>> POST {request.url.path}")
        print(f">>> BODY: {body.decode('utf-8', errors='replace')}")
    response = await call_next(request)
    if response.status_code == 422:
        print(f">>> 422 on {request.url.path} - check body above")
    return response

# CORS middleware - allow all origins (suitable for Render deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins
    allow_credentials=False,   # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(campaign_router)
app.include_router(lead_router)
app.include_router(campaign_create_router)
app.include_router(lead_scraping_router)
app.include_router(leads_approved_router)
app.include_router(profile_router)
app.include_router(export_router)
app.include_router(delete_leads_router)
app.include_router(email_config_router)
app.include_router(signature_router)
app.include_router(user_subscriptions_router)
app.include_router(user_about_router)
app.include_router(user_documents_router)
app.include_router(modify_content_check_router)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Run Uvicorn with Render-compatible port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use Render's PORT or default 8000
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)