"""Copia aislada del objeto del flujo. No se sobrescribe ni se borra."""

from pathlib import Path


class CopiaAislada:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _ruta(self, nombre: str) -> Path:
        destino = (self.root / nombre).resolve()
        if not str(destino).startswith(str(self.root.resolve())):
            raise ValueError("ruta fuera de la copia aislada")
        destino.parent.mkdir(parents=True, exist_ok=True)
        return destino

    def guardar(self, nombre: str, data: bytes) -> None:
        destino = self._ruta(nombre)
        if destino.exists():
            raise PermissionError("la copia aislada no se sobrescribe")
        destino.write_bytes(data)

    def leer(self, nombre: str) -> bytes:
        destino = self._ruta(nombre)
        if not destino.exists():
            raise FileNotFoundError(nombre)
        return destino.read_bytes()

    def borrar(self, nombre: str) -> None:
        raise PermissionError("la copia aislada no se borra")
