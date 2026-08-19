from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.holds import expire_holds


def with_fresh_holds(db: Session = Depends(get_db)) -> Session:
    expire_holds(db)
    return db
