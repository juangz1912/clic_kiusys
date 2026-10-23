#!/usr/bin/env python3
"""Compara stable y canary y dice promover, pausar o abortar."""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estadistica import decidir

ROOT = Path(__file__).resolve().parent
SLO = json.loads((ROOT / "slo.json").read_text())


def leer(base: str, header: str) -> dict:
    req = urllib.request.Request(
        base.rstrip("/") + "/api/v2/sli" if header == "false" else base.rstrip("/") + "/api/v3/sli",
        headers={"x-canary": header},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1"
    stable = leer(base, "false")
    canary = leer(base, "true")
    decision = decidir(
        stable,
        canary,
        minimo=int(SLO["minimo_muestra"]),
        z_max=float(SLO["z_max"]),
        ratio_5xx_max=float(SLO["ratio_5xx_max"]),
        p95_factor=float(SLO["p95_factor"]),
        p95_piso_ms=float(SLO["p95_piso_ms"]),
    )
    print(json.dumps({"decision": decision, "stable": stable, "canary": canary}, indent=2))
    return 0 if decision == "promover" else 2 if decision == "pausar" else 1


if __name__ == "__main__":
    raise SystemExit(main())
