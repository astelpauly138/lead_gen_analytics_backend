from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI()

# Middleware to log POST request bodies and 422 errors
@app.middleware("http")
async def log_post_bodies(request: Request, call_next):
    if request.method == "POST":
        body = await request.body()
        print(f"\n>>> POST {request.url.path}")
        print(f">>> BODY: {body.decode('utf-8')}")
    response = await call_next(request)
    if response.status_code == 422:
        print(f">>> 422 on {request.url.path} - check body above")
    return response

# CORS middleware - allow all origins (for Render deployment)
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

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}