import random
import time

_modo = "off"
_porcentaje = 0


def estado() -> dict:
    return {"modo": _modo, "porcentaje": _porcentaje}


def configurar(modo: str, porcentaje: int) -> dict:
    global _modo, _porcentaje
    _modo = modo
    _porcentaje = porcentaje
    return estado()


def aplicar() -> int | None:
    """Devuelve 500 si toca inyectar error. La latencia se aplica aquí y sigue la petición."""
    if _modo == "off" or _porcentaje <= 0:
        return None
    if random.random() * 100 > _porcentaje:
        return None
    if _modo == "latencia":
        time.sleep(0.8)
        return None
    if _modo == "errores":
        return 500
    return None
