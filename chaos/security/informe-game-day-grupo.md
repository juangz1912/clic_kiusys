# Game day de seguridad del grupo

Defensa en Profundidad 2026-2. 17 de noviembre de 2026. Repositorio `juangz1912/clic_kiusys`, rama `develop`. Este informe no es el de rendimiento: el p99 del pool está en `chaos/informe-experimento.md` y no se reutiliza.

Cuatro experimentos, uno por capa. Daniel Morales, identidad. Sebastián Quintero Granada, exposición. Juan José Giraldo, telemetría y dato, y la pieza de datos del grupo. Cada número sale del JSON de esa corrida.

## Inventario

| Capa | Dueño | Control | Señal | Marco |
| --- | --- | --- | --- | --- |
| Identidad | Daniel | JWT de 60 s, alcance, origen y revocación | 401 o 403 y línea `identidad rechazo` | ATT&CK T1550.001, D3-CRO, ISO A.5.17, NIST IA-5 |
| Borde | Sebastián | Allowlist y rechazo del token público | La ruta administrativa responde 404 | D3-ITF, NIST SC-7, ISO A.8.20 |
| Telemetría | Juan | Latido y alerta de ausencia | La marca deja de avanzar | T1562.001, D3-PM, ISO A.8.16, NIST AU-5 |
| Dato | Juan | El campo `aeronave` no es una orden | Se guarda el texto y no se borra nada | OWASP LLM01, ATLAS AML.T0051 |
| Datos del flujo | Grupo | Copia aislada | El objeto se restaura y la copia no se borra | ISO A.8.13, NIST CP-9 |

## Reglas de compromiso

Ventana: 17 de noviembre de 2026. Radio: procesos locales del grupo, más la URL pública de la API de vuelos. No se usaron cuentas de la Universidad ni de otros grupos. Datos sintéticos, el vuelo CA100. Parada: apagar el proceso, cerrar el borde o no tocar la copia aislada. Reversión probada en cada script. Bitácora: `chaos/bitacora/eventos.log`.

## Las cuatro hipótesis y las dos rondas

| Exp. | Hipótesis | Ronda 0 | Ronda 1 |
| --- | --- | --- | --- |
| 1 | Un uso no previsto de la credencial se ve en ≤ 2 s y se contiene en ≤ 10 s | 3 de 3 usos adversos aceptados. Sin detección | 0 de 3 aceptados. MTTD 0,25 s. MTTC 0,02 s. 0 falsos |
| 2 | Una ruta administrativa abierta se ve en ≤ 2 s y se cierra en ≤ 10 s | El tercero activa el pool con `caos-local`. Sin alerta. Ventana 6,13 s | MTTD 0,236 s. MTTC 0,126 s. El tercero recibe 404 y luego 403. 0 impactos |
| 3 | La pausa del latido se nombra en ≤ 3 s y se contiene en ≤ 10 s | 4 s en pausa y ninguna alerta | MTTD 3,06 s. MTTC 0,01 s. 0 falsos en 20,34 s de tráfico sano |
| 4 | Al borrar el objeto, RPO ≤ 5 s y RTO ≤ 2 s | No hay copia. No se recupera | RPO 1,02 s. RTO 0,0012 s. El contenido vuelve a ser el original |

## Experimento 1, Daniel Morales

Corrida 17:18:01 a 17:18:25 UTC. Evidencia: `chaos/security/results/identidad.json`. Informe largo: `chaos/security/informe-identidad.md`.

Estado estable: diez usos legítimos desde 127.0.0.1, sin falsos positivos. En la ronda 0 el plano de control acepta el token estático desde 127.0.0.2, con un alcance que no corresponde y sin vencimiento. No queda quién lo usó. La hipótesis se refuta.

La mejora es una credencial de máquina, no de persona: JWT de 60 segundos, audiencia, alcance por acción, lista de orígenes tomada del socket y revocación por `jti`. En la ronda 1 los tres usos adversos se rechazan. El peor MTTD es 0,25 s. Contener, revocar el `jti`, tarda 0,02 s. Diez usos legítimos siguen pasando. La regla `uso-credencial-no-previsto` tiene caso positivo y caso negativo.

## Experimento 2, Sebastián Quintero Granada

Corrida 21:30:56 a 21:31:26 UTC. Evidencia: `chaos/security/results/exposicion.json`. Informe: `chaos/security/informe-game-day-exposicion.md`.

Estado estable: el health público responde 200 y el inventario administrativo (`/internal/*`, `/docs`, `/openapi.json`) responde 404 en el borde. Durante 20,22 s y 40 sondeos la regla no dispara. 192 peticiones públicas siguen en 200.

Ronda 0: el borde queda en `abierto.conf` y reenvía todo. En 0,117 s la ruta se ve desde fuera. Con el token `caos-local`, que está en el repositorio, el tercero activa el pool. Nadie avisa. La ventana dura 6,13 s porque el script la cierra al terminar; sin detector seguiría abierta.

Ronda 1: el detector externo avisa a los 0,236 s. La contención, volver a la allowlist, tarda 0,126 s. El tercero recibe 404 en el borde y 403 si pega el token directo a la API en producción. Cero impactos. Quince variantes de la ruta (`..`, codificación, mayúsculas) siguen en 404.

## Experimento 3, Juan José Giraldo

Corrida 02:10:30 a 02:10:58 UTC. Evidencia: `chaos/security/results/game-day.json`. Informe de la capa: `chaos/security/informe-game-day.md`.

Con el trace `gd-estable` el latido avanza. 20,34 s de tráfico sano no disparan la regla. Ronda 0: se pausa la telemetría y no corre el detector. En 4 s no hay alerta. Las alertas viejas miran errores, y un silencio no produce errores.

Ronda 1, trace `gd-ronda1`: la regla escribe ausencia de latido a los 3,06 s. Queda 0,06 s sobre el umbral de 3 s por el sondeo de medio segundo. Reanudar el latido tarda 0,01 s. El señuelo, trace `gd-senuelo`, solo avisa cuando se toca. Cinco health normales no lo tocan.

La inyección, trace `gd-inyeccion`, crea el vuelo IJ01 con la frase en `aeronave`. La API responde 201, guarda el texto y deja la capacidad en 100. No ejecuta la orden. No hay un modelo en esta API. El mapeo, por si otro componente lee ese campo, es OWASP LLM01 y ATLAS AML.T0051.

## Experimento 4, datos del grupo

Corrida 21:39:04 a 21:39:05 UTC. Evidencia: `chaos/security/results/datos.json`. Informe: `chaos/security/informe-datos.md`.

El objeto es `flujo/resumen.json`. Ronda 0: se borra y no hay copia. No existe RPO ni RTO. La hipótesis se refuta.

Ronda 1: al escribir se guarda una copia en otro directorio. Esa copia no se sobrescribe ni se borra. Pasa 1,02 s y se borra el primario. Restaurar es leer la copia y reescribir. El contenido coincide con el original. RPO 1,02 s, dentro de 5. RTO 0,0012 s, dentro de 2. No es un object lock de OCI. Es la propiedad de que el borrado del primario no alcanza a la copia.

## Cronología

| Hora UTC | Qué pasó |
| --- | --- |
| 17:18:01 a 17:18:25 | Identidad. Diez usos legítimos sin falso. Ronda 1: MTTD 0,25 s, MTTC 0,02 s |
| 02:10:30 | Telemetría. Trace `gd-estable`. El latido avanza |
| 02:10:51 | Telemetría. 20,34 s de tráfico sano sin alerta. Empieza la pausa de la ronda 0 |
| 02:10:58 | Telemetría. Alerta, contención, señuelo `gd-senuelo` e inyección `gd-inyeccion` |
| 21:30:56 | Exposición. El borde sano deja las rutas administrativas en 404 |
| 21:31:25 | Exposición. Ronda 1. Alerta a los 0,236 s. El tercero recibe 404 y 403 |
| 21:39:04 | Datos. Ronda 0: el objeto se borra y no hay copia |
| 21:39:05 | Datos. Ronda 1. RPO 1,02 s. RTO 0,0012 s. El contenido original vuelve |

## Lecciones y residual

Un control de errores no ve un silencio, un borde que reenvía todo no es una frontera, y un token que está en el código no es un secreto. La credencial de máquina se contiene revocando el identificador, sin reiniciar. El dato hostil se guarda. Lo que no se copió, no se restaura.

Queda fuera: la VM de OCI y el bucket con retención de verdad, Grafana Cloud con la alerta de ausencia aplicada, y un modelo que lea `aeronave`. Las cuatro corridas se repiten con los scripts `run_identidad.py`, `run_exposicion.py`, `run_game_day.py` y `run_datos.py`.
