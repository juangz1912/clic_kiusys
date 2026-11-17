# Contraste del asistente contra la telemetría

Fecha de la corrida en el JSON: 2026-11-17T01:51:26Z. Fuente: `chaos/security/results/game-day.json`.

El asistente agrupó la cronología y propuso esta causa: la ronda 0 no detecta porque no hay una regla mirando el silencio, y la ronda 1 sí porque `detectar_latido.py` compara la marca del latido.

Acertó, y el JSON lo confirma:

- MTTD de la ronda 1: 3,08 s
- MTTC: 0,01 s
- Trace de la pausa de la ronda 1: `gd-ronda1`
- La inyección dejó `capacidad` en 100 y no ejecutó la orden

Inventó, y se descartó:

- Que Grafana Cloud hubiera mostrado la alerta. `observability/grafana/alert-ausencia-latido.json` está en el repo y no se aplicó. La única alerta con sello es la salida del script.
- Que el 0,08 s por encima de T1 anulara la mejora. La ronda 0 no tuvo alerta. Esa diferencia se conserva.

Quien firma el informe dejó esos dos descartes fuera de la conclusión.
