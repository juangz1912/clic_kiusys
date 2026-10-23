"""Comparación canary contra baseline.

Prueba z de dos proporciones (errores 5xx), con un mínimo de muestra
para no decidir con ruido. z > 1.96 rechaza, al 95%, que el canary
falle igual o menos que stable.
"""

from __future__ import annotations

import math


def prueba_z(errores_stable: int, n_stable: int, errores_canary: int, n_canary: int) -> float | None:
    if n_stable <= 0 or n_canary <= 0:
        return None
    p1 = errores_stable / n_stable
    p2 = errores_canary / n_canary
    p = (errores_stable + errores_canary) / (n_stable + n_canary)
    if p <= 0 or p >= 1:
        return 0.0 if p2 <= p1 else 99.0
    se = math.sqrt(p * (1 - p) * (1 / n_stable + 1 / n_canary))
    if se == 0:
        return 0.0
    return (p2 - p1) / se


def decidir(
    stable: dict,
    canary: dict,
    *,
    minimo: int,
    z_max: float,
    ratio_5xx_max: float,
    p95_factor: float,
    p95_piso_ms: float,
) -> str:
    n_s = int(stable["requests"])
    n_c = int(canary["requests"])
    if n_s < minimo or n_c < minimo:
        return "pausar"
    ratio = float(canary["error_ratio_5xx"])
    if ratio > ratio_5xx_max:
        return "abortar"
    z = prueba_z(int(stable["errors_5xx"]), n_s, int(canary["errors_5xx"]), n_c)
    if z is not None and z > z_max and int(canary["errors_5xx"]) > int(stable["errors_5xx"]):
        return "abortar"
    p95_s = float(stable["latency_p95_ms"])
    p95_c = float(canary["latency_p95_ms"])
    if p95_c > p95_piso_ms and p95_s > 0 and p95_c > p95_s * p95_factor:
        return "abortar"
    return "promover"
