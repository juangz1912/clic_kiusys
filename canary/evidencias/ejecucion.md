# Evidencia canary 2026-10-28T19:38:04Z

OCI Bogotá no tenía capacidad Ampere y la cuota E5 estaba en cero. El reparto es el mismo diseño (cabecera `x-canary` y pesos 0/10/50/100), ejecutado con nginx delante de dos contenedores de la imagen `clic-kiusys:canary`.

URL pública mientras el túnel siga abierto: https://fuel-tools-karen-racial.trycloudflare.com

Base: http://127.0.0.1:8080

Muestra extra al 50%, 100 peticiones sin cabecera: stable=55 canary=45.

## Etapa 0: el público cae en stable y la cabecera entra al canary

```
sin cabecera: stable
x-canary false: stable
x-canary true: canary
```
Muestra sana, 50 por track
listo: 50 a cada track
```
{
  "decision": "promover",
  "stable": {
    "version": "v2",
    "track": "stable",
    "requests": 50,
    "errors_5xx": 0,
    "errors_4xx": 0,
    "error_ratio_5xx": 0.0,
    "latency_p50_ms": 5.28,
    "latency_p95_ms": 29.85,
    "latency_p99_ms": 50.11,
    "cpu_percent": 0.0,
    "memory_mb": 97.12,
    "estado_operativo_cambios": 0
  },
  "canary": {
    "version": "v3",
    "track": "canary",
    "requests": 50,
    "errors_5xx": 0,
    "errors_4xx": 0,
    "error_ratio_5xx": 0.0,
    "latency_p50_ms": 5.15,
    "latency_p95_ms": 40.04,
    "latency_p99_ms": 45.84,
    "cpu_percent": 0.0,
    "memory_mb": 97.25,
    "estado_operativo_cambios": 0
  }
}
```
Creando un vuelo y cambiando el estado solo por v3
{"numero_vuelo":"AV910","origen":"BOG","destino":"MDE","fecha":"2026-10-30","aeronave":"A320","capacidad":120,"id":1}
```
{"id":1,"numero_vuelo":"AV910","origen":"BOG","destino":"MDE","fecha":"2026-10-30","aeronave":"A320","capacidad":120,"estado_operativo":"demorado"}[{"numero_vuelo":"AV910","origen":"BOG","destino":"MDE","fecha":"2026-10-30","aeronave":"A320","capacidad":120,"id":1}]```
Pasando a 10%
canary_percent=10
```
stable=37 canary=3 otros=0 de 40
```
Pasando a 50%
canary_percent=50
```
stable=25 canary=15 otros=0 de 40
```
Pasando a 100%
canary_percent=100
```
stable=0 canary=40 otros=0 de 40
```
Inyectando 100% de errores solo en el canary
{"modo":"errores","porcentaje":100}
listo: 40 a cada track
```
{
  "decision": "abortar",
  "stable": {
    "version": "v2",
    "track": "stable",
    "requests": 92,
    "errors_5xx": 0,
    "errors_4xx": 0,
    "error_ratio_5xx": 0.0,
    "latency_p50_ms": 4.58,
    "latency_p95_ms": 24.21,
    "latency_p99_ms": 40.24,
    "cpu_percent": 1.49,
    "memory_mb": 97.12,
    "estado_operativo_cambios": 0
  },
  "canary": {
    "version": "v3",
    "track": "canary",
    "requests": 92,
    "errors_5xx": 40,
    "errors_4xx": 0,
    "error_ratio_5xx": 0.4348,
    "latency_p50_ms": 2.47,
    "latency_p95_ms": 27.65,
    "latency_p99_ms": 43.7,
    "cpu_percent": 1.03,
    "memory_mb": 97.25,
    "estado_operativo_cambios": 1
  }
}
exit=1
```
Abortando a 0%
canary_percent=0
```
stable=20 canary=0 otros=0 de 20
200
500
```
