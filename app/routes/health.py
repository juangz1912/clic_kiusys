from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.holds import expire_holds

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    expire_holds(db)
    return {"status": "ok", "service": "clic-kiusys-pss"}
