from sqlalchemy.orm import Session

from app.config import settings
from app.models import DemoFlag

FALLO_MENSAJE = "fallo_mensaje"


def flag_activo(db: Session, nombre: str) -> bool:
    if not settings.demo_failure_enabled:
        return False
    flag = db.get(DemoFlag, nombre)
    return bool(flag and flag.activo)


def set_flag(db: Session, nombre: str, activo: bool) -> bool:
    flag = db.get(DemoFlag, nombre)
    if flag is None:
        flag = DemoFlag(nombre=nombre, activo=activo)
        db.add(flag)
    else:
        flag.activo = activo
    db.commit()
    return activo
