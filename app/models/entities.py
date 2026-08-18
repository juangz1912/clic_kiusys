import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoPasajero(str, enum.Enum):
    ADULTO = "adulto"
    INFANTE = "infante"


class ClaseAsiento(str, enum.Enum):
    Y = "Y"
    J = "J"


class EstadoAsiento(str, enum.Enum):
    SELECCIONADO = "seleccionado"
    ASIGNADO = "asignado"
    EXPIRADO = "expirado"


class Vuelo(Base):
    __tablename__ = "vuelos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_vuelo: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    origen: Mapped[str] = mapped_column(String(3))
    destino: Mapped[str] = mapped_column(String(3))
    fecha: Mapped[date] = mapped_column(Date)
    aeronave: Mapped[str] = mapped_column(String(20))
    capacidad: Mapped[int] = mapped_column(Integer)

    asientos: Mapped[list["AsientoAsignado"]] = relationship(back_populates="vuelo")


class Pasajero(Base):
    __tablename__ = "pasajeros"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    documento: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    frequent_flyer: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tipo: Mapped[TipoPasajero] = mapped_column(Enum(TipoPasajero))

    asientos: Mapped[list["AsientoAsignado"]] = relationship(back_populates="pasajero")


class AsientoAsignado(Base):
    __tablename__ = "asientos_asignados"
    __table_args__ = (
        UniqueConstraint("vuelo_id", "fila", "columna", name="uq_vuelo_asiento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vuelo_id: Mapped[int] = mapped_column(ForeignKey("vuelos.id"))
    pasajero_id: Mapped[int | None] = mapped_column(ForeignKey("pasajeros.id"), nullable=True)
    fila: Mapped[int] = mapped_column(Integer)
    columna: Mapped[str] = mapped_column(String(1))
    clase: Mapped[ClaseAsiento] = mapped_column(Enum(ClaseAsiento))
    estado: Mapped[EstadoAsiento] = mapped_column(Enum(EstadoAsiento))
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    vuelo: Mapped[Vuelo] = relationship(back_populates="asientos")
    pasajero: Mapped[Pasajero | None] = relationship(back_populates="asientos")
