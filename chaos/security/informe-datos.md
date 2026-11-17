# Experimento 4: resiliencia de los datos del flujo

Juan José Giraldo, pieza grupal del game day de Defensa en Profundidad. 17 de noviembre de 2026, 21:39:04 a 21:39:05 UTC. Evidencia: `chaos/security/results/datos.json`. Se reproduce con `python3 chaos/security/run_datos.py`.

No es el p99 de DevOps, ni la telemetría (experimento 3), ni la identidad de Daniel Morales, ni la exposición de Sebastián Quintero. Aquí la pregunta es si, al borrar el objeto del flujo, queda un punto de recuperación y cuánto se tarda en volver a tenerlo.

## Control y reglas

El objeto es `flujo/resumen.json`, con el vuelo CA100 y el trace `gd-datos`. El almacén primario es un directorio local que hace de bucket. La copia aislada está en otro directorio. No se usó el bucket de OCI ni una nube de otro grupo. Datos sintéticos. Parada: no se borra la copia. Reversión: el primario se reescribe desde ella.

| Control | Señal | Marco |
| --- | --- | --- |
| Copia aislada al momento de escribir | El primario se puede reconstruir | ISO 27001:2022 A.8.13, NIST CP-9 |
| La copia no se sobrescribe ni se borra | `PermissionError` | Resistencia a borrar el respaldo |

Hipótesis, antes de la ronda 0: dado el almacén tal como está, cuando se borre el objeto, se recupera con RPO menor o igual a 5 segundos y RTO menor o igual a 2 segundos.

## Dos rondas

Ronda 0. El objeto existe y no hay copia. Se borra. La lectura de la copia falla. No hay RPO ni RTO porque no hay punto de recuperación. La hipótesis se refuta.

Ronda 1. Se escribe el objeto y, en el mismo momento, se guarda en la copia aislada. Pasa 1,02 segundos y se borra el primario. Restaurar es leer la copia y reescribir el primario. El contenido vuelve a ser el original. La copia sigue sin dejarse borrar.

| | Ronda 0 | Ronda 1 |
| --- | --- | --- |
| Recuperado | no | sí, igual al original |
| RPO | no hay punto | 1,02 s |
| RTO | no se restauró | 0,0012 s |
| Veredicto | se refuta | se sostiene |

El RPO de 1,02 segundos es el tiempo entre la copia y el borrado: lo escrito después de la copia, y no copiado, se pierde. El RTO es el de leer la copia y volver a escribir el primario.

## Residual

Esto no es un object lock de OCI ni una copia en otra región. Es la propiedad local de tener otro directorio que el borrado del primario no toca y que la aplicación no puede vaciar. El siguiente paso, si el bucket de OCI vuelve a estar en uso, es la misma prueba con retención del objeto y una copia en otro compartimento.
