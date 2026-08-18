from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import AsientoAsignado, EstadoAsiento, Pasajero, Vuelo
from app.schemas import (
    AsientoAsignadoCreate,
    AsientoAsignadoQuery,
    AsientoAsignadoRead,
    AsientoAsignadoUpdate,
    PasajeroCreate,
    PasajeroQuery,
    PasajeroRead,
    PasajeroUpdate,
    VueloCreate,
    VueloQuery,
    VueloRead,
    VueloUpdate,
)
from app.services import confirm_asiento, expire_holds, prepare_asiento_create, query_asientos, query_pasajeros, query_vuelos

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    expire_holds(db)
    return {"status": "ok", "service": "clic-kiusys-pss"}


# --- Vuelos ---


@router.post("/vuelos", response_model=VueloRead, status_code=status.HTTP_201_CREATED)
def create_vuelo(payload: VueloCreate, db: Session = Depends(get_db)):
    vuelo = Vuelo(**payload.model_dump())
    db.add(vuelo)
    db.commit()
    db.refresh(vuelo)
    return vuelo


@router.get("/vuelos", response_model=list[VueloRead])
def list_vuelos(db: Session = Depends(get_db)):
    return db.query(Vuelo).order_by(Vuelo.id).all()


@router.get("/vuelos/{vuelo_id}", response_model=VueloRead)
def get_vuelo(vuelo_id: int, db: Session = Depends(get_db)):
    vuelo = db.get(Vuelo, vuelo_id)
    if not vuelo:
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    return vuelo


@router.put("/vuelos/{vuelo_id}", response_model=VueloRead)
def update_vuelo(vuelo_id: int, payload: VueloUpdate, db: Session = Depends(get_db)):
    vuelo = db.get(Vuelo, vuelo_id)
    if not vuelo:
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vuelo, key, value)
    db.commit()
    db.refresh(vuelo)
    return vuelo


@router.delete("/vuelos/{vuelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vuelo(vuelo_id: int, db: Session = Depends(get_db)):
    vuelo = db.get(Vuelo, vuelo_id)
    if not vuelo:
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    db.delete(vuelo)
    db.commit()


@router.post("/vuelos/query", response_model=list[VueloRead])
def query_vuelos_endpoint(payload: VueloQuery, db: Session = Depends(get_db)):
    return query_vuelos(db, payload.model_dump(exclude_none=True))


# --- Pasajeros ---


@router.post("/pasajeros", response_model=PasajeroRead, status_code=status.HTTP_201_CREATED)
def create_pasajero(payload: PasajeroCreate, db: Session = Depends(get_db)):
    pasajero = Pasajero(**payload.model_dump())
    db.add(pasajero)
    db.commit()
    db.refresh(pasajero)
    return pasajero


@router.get("/pasajeros", response_model=list[PasajeroRead])
def list_pasajeros(db: Session = Depends(get_db)):
    return db.query(Pasajero).order_by(Pasajero.id).all()


@router.get("/pasajeros/{pasajero_id}", response_model=PasajeroRead)
def get_pasajero(pasajero_id: int, db: Session = Depends(get_db)):
    pasajero = db.get(Pasajero, pasajero_id)
    if not pasajero:
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")
    return pasajero


@router.put("/pasajeros/{pasajero_id}", response_model=PasajeroRead)
def update_pasajero(pasajero_id: int, payload: PasajeroUpdate, db: Session = Depends(get_db)):
    pasajero = db.get(Pasajero, pasajero_id)
    if not pasajero:
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pasajero, key, value)
    db.commit()
    db.refresh(pasajero)
    return pasajero


@router.delete("/pasajeros/{pasajero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pasajero(pasajero_id: int, db: Session = Depends(get_db)):
    pasajero = db.get(Pasajero, pasajero_id)
    if not pasajero:
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")
    db.delete(pasajero)
    db.commit()


@router.post("/pasajeros/query", response_model=list[PasajeroRead])
def query_pasajeros_endpoint(payload: PasajeroQuery, db: Session = Depends(get_db)):
    return query_pasajeros(db, payload.model_dump(exclude_none=True))


# --- Asientos asignados ---


@router.post("/asientos-asignados", response_model=AsientoAsignadoRead, status_code=status.HTTP_201_CREATED)
def create_asiento(payload: AsientoAsignadoCreate, db: Session = Depends(get_db)):
    expire_holds(db)
    if not db.get(Vuelo, payload.vuelo_id):
        raise HTTPException(status_code=404, detail="Vuelo no encontrado")
    if payload.pasajero_id and not db.get(Pasajero, payload.pasajero_id):
        raise HTTPException(status_code=404, detail="Pasajero no encontrado")

    exists = (
        db.query(AsientoAsignado)
        .filter(
            AsientoAsignado.vuelo_id == payload.vuelo_id,
            AsientoAsignado.fila == payload.fila,
            AsientoAsignado.columna == payload.columna.upper(),
            AsientoAsignado.estado.in_([EstadoAsiento.SELECCIONADO, EstadoAsiento.ASIGNADO]),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Asiento no disponible")

    data = prepare_asiento_create(payload.model_dump())
    data["columna"] = data["columna"].upper()
    asiento = AsientoAsignado(**data)
    db.add(asiento)
    db.commit()
    db.refresh(asiento)
    return asiento


@router.get("/asientos-asignados", response_model=list[AsientoAsignadoRead])
def list_asientos(db: Session = Depends(get_db)):
    expire_holds(db)
    return db.query(AsientoAsignado).order_by(AsientoAsignado.id).all()


@router.get("/asientos-asignados/{asiento_id}", response_model=AsientoAsignadoRead)
def get_asiento(asiento_id: int, db: Session = Depends(get_db)):
    expire_holds(db)
    asiento = db.get(AsientoAsignado, asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return asiento


@router.put("/asientos-asignados/{asiento_id}", response_model=AsientoAsignadoRead)
def update_asiento(asiento_id: int, payload: AsientoAsignadoUpdate, db: Session = Depends(get_db)):
    expire_holds(db)
    asiento = db.get(AsientoAsignado, asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if data.get("estado") == "asignado":
        if not data.get("pasajero_id") and not asiento.pasajero_id:
            raise HTTPException(status_code=400, detail="Se requiere pasajero_id para asignar")
        pasajero_id = data.get("pasajero_id") or asiento.pasajero_id
        if not db.get(Pasajero, pasajero_id):
            raise HTTPException(status_code=404, detail="Pasajero no encontrado")
        confirm_asiento(asiento, pasajero_id)
        db.commit()
        db.refresh(asiento)
        return asiento

    for key, value in data.items():
        setattr(asiento, key, value)
    db.commit()
    db.refresh(asiento)
    return asiento


@router.delete("/asientos-asignados/{asiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asiento(asiento_id: int, db: Session = Depends(get_db)):
    asiento = db.get(AsientoAsignado, asiento_id)
    if not asiento:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    db.delete(asiento)
    db.commit()


@router.post("/asientos-asignados/query", response_model=list[AsientoAsignadoRead])
def query_asientos_endpoint(payload: AsientoAsignadoQuery, db: Session = Depends(get_db)):
    return query_asientos(db, payload.model_dump(exclude_none=True))
