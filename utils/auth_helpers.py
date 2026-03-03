from fastapi import Header, HTTPException
from supabase_client import supabase


def get_current_user(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]

    # supabase-python client exposes auth on the client. Older examples used
    # `supabase.auth.api.get_user(token)` but newer versions provide
    # `supabase.auth.get_user(token)` — handle possible return shapes.
    try:
        user_response = None
        if hasattr(supabase.auth, 'get_user'):
            user_response = supabase.auth.get_user(token)
        elif hasattr(supabase.auth, 'api') and hasattr(supabase.auth.api, 'get_user'):
            user_response = supabase.auth.api.get_user(token)
        else:
            raise Exception('Supabase auth client does not support get_user')

        # user_response may be an object with .user, or a dict with keys 'user' or 'data'
        user = None
        if hasattr(user_response, 'user') and user_response.user:
            user = user_response.user
        elif isinstance(user_response, dict):
            user = user_response.get('user') or (user_response.get('data') and user_response['data'].get('user'))

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if user is approved
        try:
            profile_response = supabase.table("profiles")\
                .select("is_approved")\
                .eq("id", user.id)\
                .single()\
                .execute()

            profile = profile_response.data

            if not profile or not profile.get("is_approved", False):
                raise HTTPException(
                    status_code=403,
                    detail="Account not approved. Please contact the administrator."
                )
        except HTTPException:
            raise
        except Exception as e:
            # If profile check fails, deny access for security
            raise HTTPException(
                status_code=403,
                detail=f"Unable to verify account approval status: {str(e)}"
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
