from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class VueloV3Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_vuelo: str
    origen: str
    destino: str
    fecha: date
    aeronave: str
    capacidad: int
    estado_operativo: str


class EstadoOperativoUpdate(BaseModel):
    estado_operativo: str = Field(pattern="^(programado|demorado|cancelado)$")


class Degradacion(BaseModel):
    modo: str = Field(pattern="^(off|errores|latencia)$")
    porcentaje: int = Field(default=100, ge=0, le=100)
