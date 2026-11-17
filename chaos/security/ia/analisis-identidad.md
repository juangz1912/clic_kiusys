# Contraste del asistente contra la telemetría, experimento 1

Fuentes: `chaos/security/results/identidad.json` (corrida de 17:18:01 a 17:18:25 UTC del 17 de noviembre de 2026) y `chaos/bitacora/eventos.log`.

Se le dieron al asistente el JSON y la bitácora. Agrupó las alertas por `jti`, propuso la causa y redactó la cronología.

Lo que acertó, y la evidencia confirma:

- Las tres alertas de la ronda 1 son dos credenciales. El jti `74fb1d2c329b` aparece en `origen` y en `alcance`, así que es la misma credencial robada usada dos veces. El jti `1fe19b618f8d` es la credencial vieja. Por eso priorizó revocar `74fb1d2c329b`, y fue el jti que se revocó.
- La causa de la ronda 0 es que el token estático no tiene vencimiento, alcance ni origen, y que la API no registra la identidad. La bitácora de la ronda 0 tiene `telemetria pausada=True` y `pool tamano=1` sin una sola línea `identidad`.
- Los números: MTTD de 0,25 s en el peor caso, MTTC de 0,02 s, cobertura de 3/3 y 0 falsos positivos en 10 usos.

Lo que no sostiene la evidencia, y quedó fuera de la conclusión:

- Que la ronda 1 "bloquea cualquier robo de la credencial". Es falso. Un JWT robado y usado desde 127.0.0.1, con su alcance y dentro de sus 60 s, se acepta. Queda como riesgo residual en el informe.
- Que la alerta "llegó al SIEM". Solo existe la salida de `detectar_identidad.py`. No hay alerta aplicada en Grafana Cloud ni en Cloud Logging.
- Que el MTTD de 0,25 s "es el MTTD de producción". Lo acota el sondeo local de 0,25 s, y en una nube dependería de la ingesta del log.

Quien firma el informe dejó esos descartes fuera de la conclusión. El asistente no revocó nada: la revocación la ejecuta el script con una credencial de alcance `identidad:revocar`.
