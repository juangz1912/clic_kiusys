# Game day de seguridad: telemetría y dato de la API de vuelos

Juan José Giraldo. Experimento individual 3 del final de Defensa en Profundidad. 16 de noviembre de 2026. Este informe no mide rendimiento: el p99 del pool está en `chaos/informe-experimento.md` y no se reutiliza. RPO y RTO son del experimento 4, grupal, y no se inventan aquí. Los experimentos 1 (identidad) y 2 (exposición) son de los otros integrantes, en sus nubes.

La evidencia con sello de tiempo está en `chaos/security/results/game-day.json`. El reloj de esa corrida es UTC.

## Inventario de esta capa

| Control | Dueño | Señal que debería producir | Marco |
| --- | --- | --- | --- |
| Latido del proceso en cada request | Juan, API de vuelos | La marca de `GET /internal/latido` deja de avanzar | D3FEND D3-PM. ISO 27001:2022 A.8.16. NIST 800-53 AU-5 |
| Bitácora de solo anexo | Juan | Un intento de truncar falla | D3-PM. ISO A.8.15. ATT&CK T1070, como técnica que se resiste |
| Señuelo `/internal/senuelo` | Juan | Una línea `alerta senuelo` con el trace id | D3FEND D3-DO |
| Campo `aeronave` como dato, no como orden | Juan | La API guarda el texto y no borra vuelos | OWASP LLM01. ATLAS AML.T0051 |

La técnica emulada al pausar el latido es ATT&CK T1562.001 (impedir defensas: desactivar la herramienta que ve). NIST SP 800-207 entra como verificación continua de ese control: el latido se consulta seguido, no se asume que sigue vivo. No hay una arquitectura Zero Trust completa en esta API.

## Reglas de compromiso de esta corrida

Ventana: 16 de noviembre de 2026, corrida local de menos de un minuto. Radio: el proceso de la API de vuelos en esta máquina. Cuentas: ninguna de OCI, AWS, GCP, de la Universidad ni de otros grupos. Datos: el vuelo sintético IJ01. Parada: `POST /internal/chaos` con `tipo=telemetria` y `pausada=false`, o apagar el proceso. Reversión probada al final: la telemetría volvió a verdadero. Bitácora: `chaos/bitacora/eventos.log`. El experimento versionado es `chaos/security/experiments/telemetria.json` y se corre con `python3 chaos/security/run_game_day.py`.

## Estado estable e hipótesis

Antes de pausar nada, con el trace `gd-estable`, el latido avanzó. Durante 20,34 s de tráfico con la telemetría encendida, la regla no disparó. Falsos positivos de esa pasada: 0.

Hipótesis, declarada con umbrales antes de la ronda 0: dado el latido tal como está, cuando se pause la telemetría, la señal de ausencia aparece en T1 menor o igual a 3 segundos, y la contención (volver a ver el latido) ocurre en T2 menor o igual a 10 segundos.

## Cronología

| Hora UTC | Qué pasó | Trace |
| --- | --- | --- |
| 02:10:30 | Estado estable. El latido avanza | gd-estable |
| 02:10:51 | Caso negativo: 20,34 s con telemetría sana y la regla no dispara | — |
| 02:10:51 | Ronda 0. Se pausa la telemetría y nadie corre el detector | — |
| 02:10:55 | Siguen 4 s en pausa. No hay alerta. La hipótesis se refuta | — |
| 02:10:55 | Ronda 1. Se reanuda, se confirma tráfico y se vuelve a pausar | gd-ronda1 |
| 02:10:58 | La regla escribe `ausencia de latido`. MTTD 3,06 s | gd-ronda1 |
| 02:10:58 | Contención: `pausada=false` y un health. Telemetría verdadera. MTTC 0,01 s | gd-contencion |
| 02:10:58 | Cinco health normales no tocan el señuelo. Luego se llama el señuelo | gd-senuelo |
| 02:10:58 | Se crea el vuelo IJ01 con la instrucción en `aeronave`. HTTP 201. Capacidad 100 | gd-inyeccion |

## Dos rondas

| | Ronda 0, sin la regla en marcha | Ronda 1, con la regla |
| --- | --- | --- |
| MTTD | no hubo detección en 4 s | 3,06 s (T1 era 3 s; el sondeo de 0,5 s lo deja 0,06 s por encima) |
| MTTC | no aplica: no hubo alerta que contener | 0,01 s, dentro de T2 |
| Cobertura | 0 de 1 | 1 de 1 |
| Falsos positivos | 0 en el caso negativo previo | 0 |

La ronda 0 refuta la hipótesis: el control, tal como estaba, no produce señal si nadie mira el silencio. La ronda 1 la sostiene en lo que importa, que es que el silencio ahora se nombra. El 0,06 s de más es el intervalo de consulta, no un fallo de la idea.

## Detección como código

La regla está en `chaos/security/detecciones/ausencia-latido.json` y el ejecutor en `chaos/security/detectar_latido.py`. El caso positivo es la ronda 1 (sale 0 y escribe la alerta). El caso negativo es la pasada de 20,34 s con telemetría sana (sale 1 y no escribe alerta). La misma regla, como alerta de Grafana con `noDataState: Alerting`, está versionada en `observability/grafana/alert-ausencia-latido.json`. No está aplicada en Grafana Cloud: no hay token en el repo y no hay VM. La que se ejecutó es la del proceso.

La segunda mejora es la bitácora que no se trunca. `truncar()` lanza `PermissionError`. Eso no es un object lock de OCI. Es la propiedad local de no borrar el rastro desde la aplicación.

## IA en la defensa, con una persona en el medio

Un asistente leyó `game-day.json` y propuso la cronología de la tabla de arriba. Acertó el MTTD de 3,06 s, el MTTC de 0,01 s, el trace `gd-ronda1` y que la inyección no cambió la capacidad. Inventó, y se descartó, que Grafana Cloud hubiera disparado la alerta de ausencia: el archivo de Grafana solo está versionado, y la única alerta con sello es la del script. También se descartó tratar el 0,06 s sobre T1 como si la ronda 1 hubiera fallado por completo: la ronda 0 no detectaba nada, y esa es la diferencia que el control corrige. La decisión de dejar esos descartes escritos es de quien firma el informe, no del asistente. El contraste está en `chaos/security/ia/analisis-defensa.md`.

## Inyección en un dato, repetida

No hay un modelo en esta API. La instrucción va en `aeronave` del vuelo IJ01: "Ignora las instrucciones anteriores". La API respondió 201, guardó el texto y dejó la capacidad en 100. No borró vuelos. La misma prueba, corrida otra vez dentro de `run_game_day.py`, dio el mismo resultado. La mitigación es de diseño: el campo es un dato. Si más adelante un resumen con modelo lee `aeronave`, hay que separar el dato de la orden y pedir confirmación humana antes de borrar. Mapeo: OWASP Top 10 for LLM, LLM01; MITRE ATLAS AML.T0051. No se cita un ítem de agente que esta API no tiene.

## Dos tendencias instrumentadas

Señuelo. `GET /internal/senuelo` no forma parte del flujo de vuelos. Tocarla anexa `alerta senuelo` con el trace `gd-senuelo`. Cinco peticiones normales de health no produjeron ninguna línea de señuelo: 0 falsos. Consulta del 16 de noviembre de 2026 a Decoy Object, D3-DO, en https://d3fend.mitre.org/technique/d3f:DecoyObject/.

Reporte con los plazos del Reglamento (UE) 2024/2847. El incidente simulado es la pausa del latido. El aviso temprano cabe en las 24 horas y la notificación, en las 72, porque la detección fue a los 3,06 s de enterarse. El texto está en `chaos/security/reporte-cra.md`. Fuente consultada el 16 de noviembre de 2026: https://digital-strategy.ec.europa.eu/en/policies/cra-reporting. Esas obligaciones de reporte rigen en la Unión desde el 11 de septiembre de 2026. En Colombia esta corrida no dispara un deber equivalente de fabricante: el canal nacional es ColCERT, y este ejercicio no le notificó nada porque el radio fue una máquina local con datos sintéticos.

## Lecciones, residual y lo que sigue

El control viejo solo ve errores. Un exportador callado no produce errores, así que la ronda 0 es ciega. La regla de ausencia cambia eso en este proceso.

Queda residual: la pausa no detiene un sidecar de OCI Logging, porque esa VM no existe (Bogotá no tuvo capacidad Ampere). Grafana Cloud no tiene la alerta aplicada. El señuelo solo avisa si alguien llama esa ruta; no engaña un ataque que no la conoce. El experimento 4 del grupo, con cifrado o borrado y RPO/RTO medidos, no está en este repositorio.

Siguiente experimento de esta capa: aplicar `alert-ausencia-latido.json` en Grafana cuando haya token, y repetir la pausa contra el exportador de verdad el día que la VM exista.
