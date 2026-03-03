from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from supabase_client import supabase
import os


# --- FastAPI router ---
router = APIRouter(prefix="/auth")

# --- Pydantic models for request ---
class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    company_name: str = None
    email: EmailStr
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Signup endpoint ---
@router.post("/signup")
def signup(data: SignupRequest):
    # Password match check
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Create user in Supabase Auth
    try:
        auth_response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_response.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_response.user.id

    # 2️⃣ Insert extra profile info into 'profiles' table
    try:
        supabase.table("profiles").insert({
            "id": user_id,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "company_name": data.company_name,
            "is_approved": False
        }).execute()
    except Exception as e:
        # Optional: rollback user creation if profile fails
        raise HTTPException(status_code=500, detail=f"Profile creation failed: {e}")

    # 3️⃣ Send approval email to admin
    try:
        from routes.email_service import send_admin_approval_email
        send_admin_approval_email(
            user_id,
            data.first_name,
            data.last_name,
            data.email
        )
    except Exception as e:
        # Log error but don't fail signup if email fails
        print(f"Failed to send admin approval email: {e}")

    return {
        "message": "User created successfully. Awaiting admin approval.",
        "user_id": user_id,
        "email": data.email
    }

# --- Approve endpoint (GET - Auto approves and shows status) ---
@router.get("/approve/{user_id}")
def approve_user(user_id: str):
    """
    Automatically approves the user and shows their approval status.
    This is called from the admin approval email link.
    """
    try:
        # First, fetch the user to verify they exist
        print(f"Looking for user_id: {user_id}")  # Debug log
        result = supabase.table("profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        print(f"Query result: {result}")  # Debug log
        print(f"Result data: {result.data}")  # Debug log

        if not result.data or len(result.data) == 0:
            return HTMLResponse(content="""
                <html>
                    <head>
                        <title>User Not Found</title>
                        <style>
                            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
                            .container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
                            .error { color: #d32f2f; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h2 class="error">⚠️ User Not Found</h2>
                            <p>The user ID provided does not exist in the system.</p>
                        </div>
                    </body>
                </html>
            """, status_code=404)

        user = result.data[0]
        was_already_approved = user.get("is_approved", False)

        # If not approved yet, approve them now
        if not was_already_approved:
            print(f"Approving user {user_id}...")  # Debug log
            supabase.table("profiles")\
                .update({"is_approved": True})\
                .eq("id", user_id)\
                .execute()
            print(f"User {user_id} approved successfully")  # Debug log

        # Fetch email from auth.users
        email = "N/A"
        try:
            auth_user = supabase.auth.admin.get_user_by_id(user_id)
            if auth_user and auth_user.user:
                email = auth_user.user.email or "N/A"
        except Exception as e:
            print(f"Could not fetch email: {e}")

        # Create status page showing user info and approval status
        status_message = "was already approved" if was_already_approved else "has been approved successfully"

        html_content = f"""
        <html>
            <head>
                <title>User Approved</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(170deg, black, #1db5bf);
                        padding: 20px;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                        max-width: 500px;
                        width: 100%;
                    }}
                    .success-icon {{
                        color: #4CAF50;
                        font-size: 30px;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    h2 {{
                        color: #333;
                        text-align: center;
                        margin-bottom: 10px;
                    }}
                    .status {{
                        text-align: center;
                        color: #4CAF50;
                        font-weight: 600;
                        font-size: 18px;
                        margin-bottom: 30px;
                        padding: 15px;
                        background: #e8f5e9;
                        border-radius: 8px;
                    }}
                    .user-info {{
                        background: #f9f9f9;
                        padding: 25px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .user-info h3 {{
                        color: #333;
                        margin-top: 0;
                        margin-bottom: 20px;
                        font-size: 16px;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }}
                    .info-row {{
                        display: flex;
                        padding: 12px 0;
                        border-bottom: 1px solid #e0e0e0;
                    }}
                    .info-row:last-child {{
                        border-bottom: none;
                    }}
                    .info-label {{
                        font-weight: 600;
                        color: #666;
                        min-width: 120px;
                    }}
                    .info-value {{
                        color: #333;
                        flex: 1;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✅</div>
                    <h2>User Approval Status</h2>
                    <div class="status">
                        This user {status_message}
                    </div>

                    <div class="user-info">
                        <h3>User Details</h3>
                        <div class="info-row">
                            <div class="info-label">Name:</div>
                            <div class="info-value">{user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Email:</div>
                            <div class="info-value">{email}</div>
                        </div>
                        {'<div class="info-row"><div class="info-label">Company:</div><div class="info-value">' + user.get('company_name', 'N/A') + '</div></div>' if user.get('company_name') else ''}
                        <div class="info-row">
                            <div class="info-label">Status:</div>
                            <div class="info-value" style="color: #4CAF50; font-weight: 600;">✓ Approved</div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in approve endpoint: {str(e)}")  # Debug log
        return HTMLResponse(content=f"""
            <html>
                <head>
                    <title>Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                        .container {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                        .error {{ color: #d32f2f; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2 class="error">⚠️ Error</h2>
                        <p>{str(e)}</p>
                    </div>
                </body>
            </html>
        """, status_code=500)

# --- Login endpoint ---
@router.post("/login")
def login(data: LoginRequest):
    try:
        login_response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
    except Exception as e:
        msg = str(e)
        if 'timed out' in msg.lower() or 'timeout' in msg.lower() or 'read' in msg.lower():
            raise HTTPException(status_code=504, detail="Upstream auth request timed out")
        raise HTTPException(status_code=400, detail=msg)

    if not login_response or getattr(login_response, 'user', None) is None:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Fetch user profile info from profiles table
    user_id = login_response.user.id
    try:
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        profile = profile_response.data if profile_response.data else {}
    except Exception:
        profile = {}

    # Check if user is approved
    if not profile.get("is_approved", False):
        raise HTTPException(
            status_code=403,
            detail="Account pending admin approval. Please contact the administrator."
        )

    # Return access token and user info
    return {
        "access_token": login_response.session.access_token,
        "user": {
            "user_id": login_response.user.id,
            "email": login_response.user.email,
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "company_name": profile.get("company_name", "")
        }
    }
