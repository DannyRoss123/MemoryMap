#check if app is alive or dead

from fastapi import APIRouter

router = APIRouter(tags=["health"])

#make sure the status of app is ok 
@router.get("/health")
def health():
    return {"status": "ok"}
