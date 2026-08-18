from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import ClaseAsiento, EstadoAsiento, TipoPasajero


class VueloBase(BaseModel):
    numero_vuelo: str = Field(min_length=3, max_length=10)
    origen: str = Field(min_length=3, max_length=3)
    destino: str = Field(min_length=3, max_length=3)
    fecha: date
    aeronave: str
    capacidad: int = Field(gt=0)


class VueloCreate(VueloBase):
    pass


class VueloUpdate(BaseModel):
    numero_vuelo: str | None = None
    origen: str | None = None
    destino: str | None = None
    fecha: date | None = None
    aeronave: str | None = None
    capacidad: int | None = Field(default=None, gt=0)


class VueloRead(VueloBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PasajeroBase(BaseModel):
    nombre: str
    documento: str
    frequent_flyer: str | None = None
    tipo: TipoPasajero


class PasajeroCreate(PasajeroBase):
    pass


class PasajeroUpdate(BaseModel):
    nombre: str | None = None
    documento: str | None = None
    frequent_flyer: str | None = None
    tipo: TipoPasajero | None = None


class PasajeroRead(PasajeroBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AsientoAsignadoBase(BaseModel):
    vuelo_id: int
    pasajero_id: int | None = None
    fila: int = Field(gt=0)
    columna: str = Field(min_length=1, max_length=1)
    clase: ClaseAsiento
    estado: EstadoAsiento = EstadoAsiento.SELECCIONADO


class AsientoAsignadoCreate(AsientoAsignadoBase):
    pass


class AsientoAsignadoUpdate(BaseModel):
    pasajero_id: int | None = None
    estado: EstadoAsiento | None = None


class AsientoAsignadoRead(AsientoAsignadoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hold_expires_at: datetime | None = None


class VueloQuery(BaseModel):
    origen: str | None = None
    destino: str | None = None
    fecha: date | None = None
    numero_vuelo: str | None = None


class PasajeroQuery(BaseModel):
    documento: str | None = None
    nombre: str | None = None
    tipo: TipoPasajero | None = None


class AsientoAsignadoQuery(BaseModel):
    vuelo_id: int | None = None
    pasajero_id: int | None = None
    estado: EstadoAsiento | None = None
    clase: ClaseAsiento | None = None
