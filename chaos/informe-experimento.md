# Experimento: agotamiento del pool de la API de vuelos

Juan José Giraldo. API de vuelos, integrante A. Medición del 17 de noviembre de 2026 contra `https://clic-kiusys-vuelos.up.railway.app`.
Los números salen de `chaos/results/ronda-0.json` y `chaos/results/ronda-1.json`.

## Estado estable

Sin fallo y sin control de admisión, el perfil P de k6 0.56.0 (sube a 12 VU en 5 s, sostiene 20 s, baja en 5 s, timeout de 6 s) contra `GET /api/v2/entidades/vuelos/random` en Railway dio 3090 respuestas, todas 200. El p99 fue 203,5 ms y el p95 147,6 ms. El throughput fue 103 peticiones por segundo. No hubo 4xx ni 5xx.

Ese p99 de 203,5 ms es la línea base. El viaje hasta Railway ya está en esa cifra. El umbral de la hipótesis se fijó antes de inyectar el fallo: el p99 no puede pasar de 2000 ms. La métrica objetivo es solo esa. El throughput y la tasa de error se anotan para explicar el mecanismo, no para decidir.

## Hipótesis

Dado el perfil P, cuando el pool de la ruta random se reduzca a 1 conexión durante ese perfil, la API mantendrá el p99 por debajo de 2000 ms.

## Método y radio de impacto

El fallo es el interruptor propio `POST /internal/chaos` con `tipo=pool`, tamaño 1 y una retención de 700 ms por permiso. El token va en `X-Chaos-Token`. El TTL es 180 segundos y `DELETE /internal/chaos` revierte antes. No se borra ni se altera ninguna fila. AWS y GCP no se tocan. La herramienta declarativa está en `chaos/experiments/agotamiento-pool-vuelos.json`. El instrumento de esta corrida es k6 0.56.0, con el script `chaos/k6/vuelos.js`. `chaos/run_rondas.py` lo lanza igual en las dos rondas. El resumen de cada pasada está en `chaos/results/k6-ronda-*.json`.

El radio es el proceso de la API de vuelos. La base solo presta la fila del vuelo CA100.

## Ronda 0, sin protección

Con el pool en 1 y una espera de hasta 4000 ms por un permiso, el perfil solo completó 80 peticiones. 46 fueron 200 y 34 fueron 503. El throughput bajó a 2,45 por segundo. El p99 fue 4683,7 ms y el p95 4506,7 ms. k6 salió con código 99, porque el umbral de 2000 ms no se cumplió.

La hipótesis se refuta: 4683 es más del doble del umbral. El mecanismo no es un 500 genérico. Las 12 VU hacen cola detrás de un solo permiso que se retiene 700 ms. Quien no alcanza permiso en 4 segundos recibe 503. El coordinador, con timeout de 2 segundos, vería la mayoría como timeout. Después de `DELETE /internal/chaos` la misma carga volvió a 3243 respuestas 200, p99 170,8 ms.

## Mejora

Dos patrones, sacados de esa cola:

1. Control de admisión. Como mucho 2 peticiones de `random` en vuelo. El resto recibe 429 de inmediato, con `Retry-After: 1`. No se encola sin límite.
2. Mamparo. En la ronda protegida la espera de un permiso del pool baja de 4000 ms a 400 ms. Una consulta que no consigue conexión falla pronto y no retiene al resto.

No se agregaron reintentos. Reintentar contra un pool de 1 alarga la cola.

## Ronda 1, con la mejora

El mismo perfil, el mismo pool de 1, la misma retención de 700 ms, el mismo k6, contra Railway. La ronda se fijó con `POST /internal/chaos` `tipo=ronda`. El p99 fue 1048,7 ms. La hipótesis, sobre esa única métrica, se sostiene.

De 2556 peticiones, 2472 fueron 429, 43 fueron 200 y 41 fueron 503 del pool. El 503 del pool pasó de 34 de 80 (42 %) a 41 de 2556 (1,6 %).

## Comparación

| | Línea base | Ronda 0 | Ronda 1 |
| --- | --- | --- | --- |
| p99 | 203,5 ms | 4683,7 ms | 1048,7 ms |
| Throughput | 103 /s | 2,45 /s | 83,6 /s |
| 503 de pool | 0 | 34 | 41 |
| Veredicto | — | se refuta | se sostiene |

El p99 baja de 4683,7 ms a 1048,7 ms. Sigue bajo el umbral de 2000 ms. El sistema deja de quedarse callado y contesta, aunque sea para decir que no hay cupo.

## Hallazgos y backlog

Esta corrida ya pegó a Railway, no a la máquina local. El host viejo `http://157-137-193-66.sslip.io` sigue sin ser esta API.

Queda pendiente subir estas series a Grafana Cloud. El tablero versionado está en `observability/grafana/dashboard-caos-rondas.json`. La comparación que sí se midió es la tabla de arriba y los dos JSON.

La puerta `chaos/gate.py` lee el p99 de la ronda 1 y falla si pasa de 2000 ms. En esta corrida pasó: 1048,7. El workflow `chaos-gate.yml` solo corre con la ventana autorizada y siempre intenta revertir.
