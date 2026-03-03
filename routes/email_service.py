import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_admin_approval_email(user_id, first_name, last_name, email):
    # Use backend URL from environment variable or default to localhost
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    approve_link = f"{backend_url}/auth/approve/{user_id}"

    admin_email = os.getenv("ADMIN_EMAIL", "a.pauly@analytica-data.com")
    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

    resend.Emails.send({
        "from": from_email,
        "to": admin_email,
        "subject": "New User Approval Required",
        "html": f"""
            <h3>New Signup - Approval Required</h3>
            <p><strong>Name:</strong> {first_name} {last_name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>User ID:</strong> {user_id}</p>
            <br>
            <a href="{approve_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Approve User</a>
            <br><br>
            <p style="color: #666; font-size: 12px;">Click the link above to approve this user and allow them to login.</p>
        """
    })
