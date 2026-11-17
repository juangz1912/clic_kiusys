from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_demo() -> None:
    from datetime import date

    from app.models.entities import Vuelo

    db = SessionLocal()
    try:
        if db.query(Vuelo).first() is not None:
            return
        db.add(
            Vuelo(
                numero_vuelo="CA100",
                origen="BOG",
                destino="MDE",
                fecha=date(2026, 11, 18),
                aeronave="A320",
                capacidad=120,
            )
        )
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE vuelos ADD COLUMN IF NOT EXISTS "
                    "estado_operativo VARCHAR(20) DEFAULT 'programado'"
                )
            )
