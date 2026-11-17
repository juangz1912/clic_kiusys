"""Credencial efímera del coordinador para el plano de control interno.

El token es un JWT HS256: sub, aud, alcance, iat, exp y jti. Lo valida la API
con cuatro preguntas: firma y audiencia, ventana de vida, alcance y origen.
Cada uso, aceptado o rechazado, anexa una línea en la bitácora con el trace id.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from threading import Lock

from app.config import settings
from app.services.bitacora import anexar

_lock = Lock()
_revocados: set[str] = set()


class Rechazo(Exception):
    def __init__(self, motivo: str, status: int) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.status = status


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firma(mensaje: bytes) -> str:
    return _b64(hmac.new(settings.identidad_secreto.encode(), mensaje, hashlib.sha256).digest())


def emitir(sub: str, alcance: str, ttl_s: int | None = None, aud: str | None = None) -> str:
    ahora = int(time.time())
    ttl = min(ttl_s or settings.identidad_ttl_s, settings.identidad_ttl_s)
    cabecera = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    cuerpo = _b64(
        json.dumps(
            {
                "sub": sub,
                "aud": aud or settings.identidad_audiencia,
                "alcance": alcance,
                "iat": ahora,
                "exp": ahora + ttl,
                "jti": uuid.uuid4().hex[:12],
            }
        ).encode()
    )
    return f"{cabecera}.{cuerpo}.{_firma(f'{cabecera}.{cuerpo}'.encode())}"


def leer(token: str) -> dict:
    partes = token.split(".")
    if len(partes) != 3:
        raise Rechazo("token_estatico", 401)
    cabecera, cuerpo, firma = partes
    if not hmac.compare_digest(firma, _firma(f"{cabecera}.{cuerpo}".encode())):
        raise Rechazo("firma", 401)
    return json.loads(_unb64(cuerpo))


def revocar(jti: str) -> None:
    with _lock:
        _revocados.add(jti)


def revocados() -> list[str]:
    with _lock:
        return sorted(_revocados)


def limpiar() -> None:
    with _lock:
        _revocados.clear()


def _origenes() -> set[str]:
    return {o.strip() for o in settings.identidad_origenes.split(",") if o.strip()}


def validar(token: str | None, alcance: str, origen: str, trace_id: str) -> dict:
    """Devuelve los claims o lanza Rechazo. Siempre deja línea en la bitácora."""
    claims: dict = {}
    try:
        if not token:
            raise Rechazo("sin_token", 401)
        claims = leer(token)
        if claims.get("aud") != settings.identidad_audiencia:
            raise Rechazo("audiencia", 401)
        with _lock:
            revocado = claims.get("jti") in _revocados
        if revocado:
            raise Rechazo("revocado", 401)
        if int(claims.get("exp", 0)) < time.time():
            raise Rechazo("vencido", 401)
        if claims.get("alcance") != alcance:
            raise Rechazo("alcance", 403)
        if origen not in _origenes():
            raise Rechazo("origen", 403)
    except Rechazo as exc:
        anexar(
            f"identidad rechazo motivo={exc.motivo} sub={claims.get('sub', '-')} jti={claims.get('jti', '-')} "
            f"alcance_pedido={alcance} alcance_token={claims.get('alcance', '-')} origen={origen} trace_id={trace_id}"
        )
        raise
    anexar(
        f"identidad ok sub={claims['sub']} jti={claims['jti']} alcance={alcance} origen={origen} trace_id={trace_id}"
    )
    return claims
