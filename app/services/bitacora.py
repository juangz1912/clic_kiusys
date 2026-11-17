"""Bitácora de solo anexo. No se trunca desde la aplicación."""

from pathlib import Path

RUTA = Path("chaos/bitacora/eventos.log")


def anexar(linea: str) -> None:
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    with RUTA.open("a", encoding="utf-8") as archivo:
        archivo.write(linea.strip() + "\n")


def truncar() -> None:
    raise PermissionError("la bitacora no se trunca")
