#!/usr/bin/env python3
"""Crea o actualiza en Grafana Cloud el tablero RED, el canal de correo y la alerta de errores.

Uso:
  GRAFANA_URL=https://browngecko19.grafana.net GRAFANA_TOKEN=glsa_... python3 scripts/grafana_apply.py
El token es de un Service Account con rol Editor y no se guarda en el repo.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "observability" / "grafana"
FOLDER_UID = "clic-s2"
FOLDER_TITLE = "Multicloud S2"
RULE_GROUP_INTERVAL_SECONDS = 30

GRAFANA_URL = os.environ.get("GRAFANA_URL", "").rstrip("/")
GRAFANA_TOKEN = os.environ.get("GRAFANA_TOKEN", "")


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {GRAFANA_TOKEN}",
            "Content-Type": "application/json",
            "X-Disable-Provenance": "true",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"message": raw.decode(errors="replace")}


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def ensure_folder() -> None:
    status, _ = call("GET", f"/api/folders/{FOLDER_UID}")
    if status == 200:
        print(f"carpeta {FOLDER_TITLE}: ya existe")
        return
    status, body = call("POST", "/api/folders", {"uid": FOLDER_UID, "title": FOLDER_TITLE})
    print(f"carpeta {FOLDER_TITLE}: {status} {body.get('message', '')}")
    if status >= 300:
        sys.exit(1)


def apply_dashboard() -> str:
    dashboard = load("dashboard-red.json")
    status, body = call(
        "POST",
        "/api/dashboards/db",
        {"dashboard": dashboard, "folderUid": FOLDER_UID, "overwrite": True, "message": "grafana_apply.py"},
    )
    print(f"tablero: {status} {body.get('status', body.get('message', ''))}")
    if status >= 300:
        sys.exit(1)
    return f"{GRAFANA_URL}{body['url']}"


def apply_contact_point() -> None:
    cp = load("contact-point.json")
    status, body = call("PUT", f"/api/v1/provisioning/contact-points/{cp['uid']}", cp)
    if status == 404 or (status >= 400 and "not found" in json.dumps(body).lower()):
        status, body = call("POST", "/api/v1/provisioning/contact-points", cp)
    print(f"canal de correo: {status} {body.get('message', '')}")
    if status >= 300:
        sys.exit(1)


def apply_alert() -> None:
    rule = load("alert-errores.json")
    rule["folderUID"] = FOLDER_UID
    status, body = call("PUT", f"/api/v1/provisioning/alert-rules/{rule['uid']}", rule)
    if status == 404:
        status, body = call("POST", "/api/v1/provisioning/alert-rules", rule)
    print(f"alerta: {status} {body.get('message', '')}")
    if status >= 300:
        print(json.dumps(body, indent=2))
        sys.exit(1)

    group_path = f"/api/v1/provisioning/folder/{FOLDER_UID}/rule-groups/{rule['ruleGroup']}"
    status, group = call("GET", group_path)
    if status == 200 and group.get("interval") != RULE_GROUP_INTERVAL_SECONDS:
        group["interval"] = RULE_GROUP_INTERVAL_SECONDS
        status, body = call("PUT", group_path, group)
        print(f"intervalo de evaluación {RULE_GROUP_INTERVAL_SECONDS}s: {status} {body.get('message', '')}")


def main() -> None:
    if not GRAFANA_URL or not GRAFANA_TOKEN:
        sys.exit("Faltan GRAFANA_URL y GRAFANA_TOKEN")
    ensure_folder()
    url = apply_dashboard()
    apply_contact_point()
    apply_alert()
    print(f"\nTablero: {url}")
    print(f"Alertas: {GRAFANA_URL}/alerting/list")


if __name__ == "__main__":
    main()
