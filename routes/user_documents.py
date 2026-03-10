import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from supabase_client import supabase

logger = logging.getLogger(__name__)
router = APIRouter()

BUCKET = "user_about"
ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/user-documents/{user_id}/upload")
async def upload_document(user_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Accepted: PDF, Word, PowerPoint, plain text.",
        )

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    original_name = file.filename or "document"
    storage_path = f"{user_id}/{original_name}"

    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            content,
            {"content-type": file.content_type, "x-upsert": "true"},
        )
    except Exception as e:
        logger.error(f"Storage upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file to storage.")

    return {
        "path": storage_path,
        "file_name": original_name,
        "size": len(content),
    }


@router.get("/user-documents/{user_id}")
def list_documents(user_id: str):
    try:
        files = supabase.storage.from_(BUCKET).list(user_id)
    except Exception as e:
        logger.error(f"Storage list error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents.")

    if not files:
        return []

    result = []
    for f in files:
        name = f.get("name", "")
        if not name:
            continue
        path = f"{user_id}/{name}"
        url = ""
        try:
            signed = supabase.storage.from_(BUCKET).create_signed_url(path, 3600)
            url = signed.get("signedURL") or signed.get("signed_url") or ""
        except Exception as e:
            logger.warning(f"Could not create signed URL for {path}: {e}")

        result.append({
            "path": path,
            "file_name": f.get("metadata", {}).get("httpsMd5") and name or name,
            "size": f.get("metadata", {}).get("size"),
            "created_at": f.get("created_at"),
            "url": url,
        })

    return result


@router.delete("/user-documents/{user_id}")
def delete_document(user_id: str, file_path: str = Query(...)):
    if not file_path.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Forbidden.")

    try:
        supabase.storage.from_(BUCKET).remove([file_path])
    except Exception as e:
        logger.error(f"Storage delete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document.")

    return {"deleted": file_path}
