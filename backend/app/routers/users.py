from fastapi import APIRouter


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/status")
def users_status():
    return {"status": "ready", "message": "User endpoints will expand as Streamlit migrates to FastAPI."}
