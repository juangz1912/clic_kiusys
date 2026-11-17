# Experimento: agotamiento del pool de la API de vuelos

Juan José Giraldo. API de vuelos, integrante A. Medición del 16 de noviembre de 2026.
Los números salen de `chaos/results/ronda-0.json` y `chaos/results/ronda-1.json`.

## Estado estable

Sin fallo y sin control de admisión, el perfil P (12 hilos durante 20 segundos, timeout de cliente de 6 segundos) contra `GET /api/v2/entidades/vuelos/random` dio 9758 respuestas, todas 200. El p99 fue 59,5 ms y el p95 32,1 ms. El throughput fue 487,9 peticiones por segundo. No hubo 4xx ni 5xx.

Ese p99 de 59,5 ms es la línea base. El umbral de la hipótesis se fijó antes de inyectar el fallo: el p99 no puede pasar de 2000 ms. La métrica objetivo es solo esa. El throughput y la tasa de error se anotan para explicar el mecanismo, no para decidir.

## Hipótesis

Dado el perfil P, cuando el pool de la ruta random se reduzca a 1 conexión durante esos 20 segundos, la API mantendrá el p99 por debajo de 2000 ms.

## Método y radio de impacto

El fallo es el interruptor propio `POST /internal/chaos` con `tipo=pool`, tamaño 1 y una retención de 700 ms por permiso. El token va en `X-Chaos-Token`. El TTL es 180 segundos y `DELETE /internal/chaos` revierte antes. No se borra ni se altera ninguna fila. AWS y GCP no se tocan. La herramienta declarativa está en `chaos/experiments/agotamiento-pool-vuelos.json`. El mismo perfil está en `chaos/k6/vuelos.js`. Esta corrida usó `chaos/run_rondas.py` porque en la máquina no había binario de k6; el perfil no cambió entre rondas.

El radio es el proceso de la API de vuelos. La base solo presta la fila del vuelo CA100.

## Ronda 0, sin protección

Con el pool en 1 y una espera de hasta 4000 ms por un permiso, en 20 segundos solo cupieron 64 peticiones. 34 fueron 200 y 30 fueron 503. El throughput bajó a 3,2 por segundo. El p99 fue 4705 ms y el p95 4477 ms.

La hipótesis se refuta: 4705 es más del doble del umbral. El mecanismo no es un 500 genérico. Las 12 hebras hacen cola detrás de un solo permiso que se retiene 700 ms. Quien no alcanza permiso en 4 segundos recibe 503. El coordinador, con timeout de 2 segundos, vería la mayoría como timeout. Después de `DELETE /internal/chaos` la misma carga volvió a 9536 respuestas 200, p99 62,6 ms.

## Mejora

Dos patrones, sacados de esa cola:

1. Control de admisión. Como mucho 2 peticiones de `random` en vuelo. El resto recibe 429 de inmediato, con `Retry-After: 1`. No se encola sin límite.
2. Mamparo. En la ronda protegida la espera de un permiso del pool baja de 4000 ms a 400 ms. Una consulta que no consigue conexión falla pronto y no retiene al resto.

No se agregaron reintentos. Reintentar contra un pool de 1 alarga la cola.

## Ronda 1, con la mejora

El mismo perfil, el mismo pool de 1, la misma retención de 700 ms, el mismo instrumento. El p99 fue 44,7 ms. La hipótesis, sobre esa única métrica, se sostiene.

De 26287 peticiones, 11439 fueron 429, 29 fueron 200 y 27 fueron 503 del pool. Otras 14792 ni llegaron a código HTTP: el cliente abrió conexiones más rápido de lo que el sistema acepta, porque la respuesta ya no espera en la cola. Eso no es un timeout de base de datos. El 503 del pool pasó de 30 de 64 (47 %) a 27 de 26287 (0,1 %).

## Comparación

| | Línea base | Ronda 0 | Ronda 1 |
| --- | --- | --- | --- |
| p99 | 59,5 ms | 4705 ms | 44,7 ms |
| Throughput | 487,9 /s | 3,2 /s | 1314 /s |
| 503 de pool | 0 | 30 | 27 |
| Veredicto | — | se refuta | se sostiene |

El p99 baja de 4705 ms a 44,7 ms: un 99 % menos. El sistema deja de quedarse callado y contesta, aunque sea para decir que no hay cupo.

## Hallazgos y backlog

No esperaba tantos fallos de conexión en el cliente cuando el servidor responde rápido. El próximo paso es repetir el perfil desde k6, con menos conexiones nuevas, sobre la VM de OCI cuando haya capacidad. Hoy la URL pública vieja `http://157-137-193-66.sslip.io` no sirve esta ruta. La corrida fue en local.

Queda pendiente subir estas series a Grafana Cloud. El tablero versionado está en `observability/grafana/dashboard-caos-rondas.json`. La comparación que sí se midió es la tabla de arriba y los dos JSON.

La puerta `chaos/gate.py` lee el p99 de la ronda 1 y falla si pasa de 2000 ms. En esta corrida pasó: 44,7. El workflow `chaos-gate.yml` solo corre con la ventana autorizada y siempre intenta revertir.
