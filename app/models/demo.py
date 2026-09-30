from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DemoFlag(Base):
    """Interruptores de la demo. Viven en Postgres para que todas las réplicas los vean a la vez."""

    __tablename__ = "demo_flags"

    nombre: Mapped[str] = mapped_column(String(50), primary_key=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=False)
