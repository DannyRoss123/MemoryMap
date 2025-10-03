#check if app is alive or dead

from fastapi import APIRouter
router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok"}
