# Experimento 1: identidad de máquinas

Daniel Morales. Capa de identidad del game day de Defensa en Profundidad 2026-2. Repositorio: https://github.com/CodeNomad-01/defensa-caos-identidad-exp1 (derivado del proyecto del grupo `clic_kiusys`). Corrida del 17 de noviembre de 2026, de 17:18:01 a 17:18:25 UTC (12:18 en Bogotá), archivo `chaos/security/results/identidad.json`. Se reproduce con `python chaos/security/run_identidad.py`.

Este experimento mide si el plano de control detecta y contiene el uso indebido de la credencial de una máquina. No mide velocidad del servicio.

## 1. Inventario de controles de la capa de identidad

| Control | Dueño | Señal esperada | Marco |
| --- | --- | --- | --- |
| Credencial del plano de control `/internal/*` | Daniel | 401 o 403 y línea `identidad rechazo` con trace id | D3FEND D3-CRO, ISO A.5.17, NIST IA-5 |
| Alcance por acción (`chaos:leer`, `chaos:telemetria`, `chaos:pool`, `chaos:revertir`, `identidad:revocar`) | Daniel | 403 `motivo=alcance` | D3-AZET, ISO A.8.2, NIST AC-6 |
| Lista de orígenes del coordinador | Daniel | 403 `motivo=origen` | D3-ANET, ISO A.8.5, NIST 800-207 |
| Revocación por `jti` | Daniel | `contencion identidad ... revocado` y reuso en 401 | D3-CR, NIST IA-5 |
| Regla `uso-credencial-no-previsto` | Daniel | Alerta con motivo, origen, jti y trace | D3-ANET, ISO A.8.16, NIST AU-6 |

La técnica emulada es ATT&CK T1550.001, Application Access Token: una credencial de aplicación robada se usa en lugar de autenticarse. Como es la credencial de la cuenta de servicio del coordinador, también aplica T1078.004, Cloud Accounts. Las técnicas y contramedidas se consultaron el 17 de noviembre de 2026 en attack.mitre.org y d3fend.mitre.org.

Es una identidad de máquina y no de persona. Nadie escribe una contraseña ni hay MFA. El coordinador presenta un secreto en cada llamada. Por eso, si alguien copia ese secreto, puede hacerse pasar por el coordinador sin que nadie lo note.

## 2. Reglas de compromiso

- **Ventana:** el 17 de noviembre de 2026, menos de un minuto por corrida.
- **Radio:** solo el plano de control `/internal/*` de un proceso local de la API en `127.0.0.1:8015`, con una base SQLite desechable (`chaos/runtime/identidad.db`). No se tocó OCI, AWS, GCP ni ningún recurso de la Universidad o de otro grupo.
- **Datos:** sintéticos.
- **Origen adverso:** `127.0.0.2`, la misma máquina con otra dirección de loopback. La API arranca con `--no-proxy-headers`, así que el origen es el del socket y no una cabecera que cualquiera pueda falsificar.
- **Parada:** Ctrl+C, o que el health deje de responder antes de un uso adverso.
- **Reversión:** está en el `finally`. Manda `POST /internal/chaos {"tipo":"off"}` y apaga el proceso. Al final de cada ronda se verifica que la telemetría esté en `true` y el pool inactivo.
- **Bitácora:** `chaos/bitacora/eventos.log`, de solo anexo.

## 3. Estado estable e hipótesis

Antes de cualquier uso adverso, el coordinador lee `/internal/chaos` desde `127.0.0.1` una vez y luego diez veces en 5 s, con la regla corriendo. En las dos rondas, los 10 usos respondieron 200 y la regla no disparó, así que hay 0 falsos positivos. La cobertura de telemetría de identidad fue de 0 % en la ronda 0, porque no quedó ninguna línea de quién usó la credencial, y de 100 % en la ronda 1, con 11 de 11 usos registrados.

**Hipótesis:** dado el control de credencial tal como está configurado, cuando la credencial del coordinador se use desde un origen no previsto, con un alcance que no le toca o fuera de su ventana de vida, esperamos la alerta de la regla en un tiempo T1 menor o igual a 2 s y la contención (credencial revocada y reuso rechazado) en un tiempo T2 menor o igual a 10 s. La métrica objetivo es el MTTD y se declaró antes de la ronda 0.

## 4. Método

El método es el mismo en las dos rondas. Solo cambia el control (`IDENTIDAD_ESTRICTA`):

1. **Origen:** la credencial robada pide pausar la telemetría desde `127.0.0.2`.
2. **Alcance:** la misma credencial pide activar el pool, una acción que no le corresponde.
3. **Ventana:** se usa una credencial vieja, emitida al inicio con 1 s de vida.
4. **Contención:** se intenta revocar la credencial robada y se verifica si el reuso falla.
5. **Reversión:** se apaga el experimento y se verifica el estado inicial.

En la ronda 0, la "credencial robada" es el token estático `CHAOS_TOKEN`, porque es lo único que tiene el coordinador. En la ronda 1 es un JWT de 60 s.

## 5. Cronología (UTC, 17 de noviembre de 2026)

| Hora UTC | Ronda | Qué pasó | Trace |
| --- | --- | --- | --- |
| 17:18:03.585 | 0 | Estado estable, el coordinador lee y recibe 200 | `id-r0-estable` |
| 17:18:08.676 | 0 | Caso negativo: 10 usos legítimos, 0 alertas, sin líneas de identidad | `id-r0-normal-*` |
| 17:18:08.762 | 0 | Desde 127.0.0.2 se pausa la telemetría: **200** | `id-r0-origen` |
| 17:18:08.779 | 0 | Con la misma credencial se activa el pool: **200** | `id-r0-alcance` |
| 17:18:08.821 | 0 | Credencial "vieja": **200**, porque el token estático no vence | `id-r0-vencido` |
| 17:18:14.748 | 0 | Fin de la ventana de la regla: no disparó | - |
| 17:18:18.740 | 0 | La revocación no existe (404). A los 10 s el reuso sigue en 200: no se contuvo | `id-r0-reuso` |
| 17:18:18.774 | 0 | Reversión: telemetría en `true`, pool apagado | `id-r0-reversion` |
| 17:18:20.360 | 1 | Estado estable con un JWT de alcance `chaos:leer` | `id-r1-estable` |
| 17:18:25.464 | 1 | Caso negativo: 10 usos legítimos, 0 alertas, 11 líneas `identidad ok` | `id-r1-normal-*` |
| 17:18:25.527 | 1 | Desde 127.0.0.2: **403** `motivo=origen` | `id-r1-origen` |
| 17:18:25.534 | 1 | Alcance de pool: **403** `motivo=alcance` | `id-r1-alcance` |
| 17:18:25.541 | 1 | Credencial vencida: **401** `motivo=vencido` | `id-r1-vencido` |
| 17:18:25.774 | 1 | La regla dispara 3 alertas. MTTD de 0,23 a 0,25 s | los tres anteriores |
| 17:18:25.784 | 1 | Se revoca el jti `74fb1d2c329b` y el reuso da 401 `revocado`. MTTC 0,02 s | `id-r1-contencion`, `id-r1-reuso` |
| 17:18:25.796 | 1 | Reversión verificada | `id-r1-reversion` |

En la ronda 0, la bitácora solo dice `telemetria pausada=True` y `pool tamano=1`. No dice quién lo hizo, desde dónde ni con qué trace. Ese es el defecto: el cambio queda registrado, pero no quién lo hizo.

## 6. Dos rondas

| | Ronda 0, token estático | Ronda 1, credencial efímera con política |
| --- | --- | --- |
| Usos adversos aceptados | 3 de 3 | 0 de 3 |
| MTTD | Sin detección en 6 s | 0,25 s, el peor de los tres |
| MTTC | No contenida en T2: no hay revocación | 0,02 s |
| Cobertura de detección | 0/3 | 3/3 |
| Falsos positivos | 0 de 10 | 0 de 10 |
| Cobertura de telemetría de identidad | 0 % | 100 % |

La ronda 0 refuta la hipótesis, y el mecanismo es claro. El token es un secreto compartido que no vence, no tiene alcance ni origen, y su uso no deja registro. Para la API, cualquiera que lo tenga es el coordinador. Contenerlo exige cambiar `CHAOS_TOKEN` y reiniciar, es decir, cortar el servicio.

La ronda 1 sostiene la hipótesis: el MTTD queda por debajo de T1 y el MTTC por debajo de T2, sin falsos positivos. La cobertura de 3/3 se lee junto a la tasa base. Son tres condiciones emuladas en una sola ventana sana de 10 usos, así que no se extrapola a un mes de producción. El MTTD está acotado por el sondeo de 0,25 s de la regla.

## 7. Detección como código

- **Regla:** `chaos/security/detecciones/uso-credencial-no-previsto.json`, con su patrón, motivos, severidad y marcos.
- **Ejecutor:** `chaos/security/detectar_identidad.py`. Lee solo las líneas nuevas de la bitácora y sale con 0 si dispara o con 1 si no.
- **Caso positivo:** los tres usos adversos de la ronda 1, más `tests/test_identidad.py::test_regla_caso_positivo`.
- **Caso negativo:** los 10 usos legítimos con la regla corriendo, más `test_regla_caso_negativo` (`identidad ok`, telemetría y señuelo no disparan).
- **Pruebas:** `tests/test_identidad.py` tiene 12 pruebas. Cubren el rechazo por token estático, origen, alcance, vencimiento, firma alterada y revocación, el tope del TTL y la compatibilidad sin modo estricto.

## 8. Mejoras

1. **Credencial efímera en lugar del secreto estático** (`app/services/identidad.py`): un JWT HS256 con `sub`, `aud`, `alcance`, `iat`, `exp` y `jti`. Su vida máxima es de 60 s y la API la recorta aunque se pida más. Corresponde a D3-CRO, ISO A.5.17 y NIST IA-5. La firma se compara en tiempo constante con `hmac.compare_digest`.
2. **Autorización por política, con mínimo privilegio y alcance por audiencia** (`app/routes/internal_chaos.py`): cada ruta exige su alcance, la audiencia debe ser `clic-kiusys-control` y el origen debe estar en `IDENTIDAD_ORIGENES`. Corresponde a D3-AZET, D3-ANET, NIST AC-6 y NIST 800-207 (cada petición se verifica, no se confía por estar dentro).
3. **Revocación por `jti`** (`POST /internal/identidad/revocar`) para contener sin reiniciar. Corresponde a D3-CR. Además, cada uso, aceptado o no, queda en la bitácora con trace id.

Por qué la contramedida corresponde a la técnica: T1550.001 consiste en usar un token robado. ATT&CK recomienda la mitigación M1036, que es restringir el uso del token fuera de su contexto esperado. Eso es exactamente la lista de orígenes, el alcance y el vencimiento. D3FEND relaciona D3-CR (revocación) con "Use Alternate Authentication Material", la técnica padre de T1550.001.

## 9. Lo que esta capa no afirma

- **No es GCP.** Si el coordinador corre en GCP, la versión de nube de estas mejoras es Workload Identity Federation con tokens de corta vida y la alerta en Cloud Logging. Eso no se ejecutó.
- **El emisor no es un IdP real.** Firma con un secreto HMAC compartido que el script genera en cada corrida. En producción, ese emisor sería el proveedor de identidad.
- **No cubre el robo dentro del origen permitido.** Si alguien roba el JWT desde el propio host del coordinador y lo usa con su alcance correcto dentro de sus 60 s, la API lo acepta. Ese es el riesgo residual, y lo acota la vida corta del token y la revocación. La siguiente mejora sería atar el token a quien lo porta (mTLS o DPoP, ATT&CK M1013).
- **La revocación vive en memoria.** Se pierde al reiniciar el proceso. En producción tendría que persistir, por ejemplo en Redis.
- **La alerta sale del script, no de un SIEM.** No se afirma que haya disparado en Grafana Cloud.

## 10. Tendencias del sector

Las dos tendencias se consultaron el 17 de noviembre de 2026 y las dos quedan implementadas y medidas en la ronda 1, no solo mencionadas.

1. **Identidad de agentes de IA y privilegios de máquina no gestionados.** Gartner, *Gartner Identifies the Top Strategic Technology Trends for 2027*, comunicado del 20 de octubre de 2026 (https://www.gartner.com/en/newsroom/press-releases/2026-10-20-gartner-identifies-the-top-strategic-technology-trends-for-2027). Gartner predice que para 2028 el 25 % de las brechas empresariales vendrá del abuso de agentes de IA, por privilegios de máquina no gestionados y credenciales heredadas, y recomienda cambiar las credenciales estáticas por acceso dinámico controlado por política. **Cómo se implementa:** el coordinador es un componente autónomo que actúa sin una persona. La ronda 1 cambia su `CHAOS_TOKEN` estático por una credencial con `sub`, alcance por acción, audiencia, origen y `jti`. Cada uso queda atado a la acción en la bitácora con su trace id. **Medida:** los usos adversos aceptados bajan de 3/3 a 0/3 y la cobertura de telemetría de identidad sube de 0 % a 100 %.
2. **Credenciales de vida cada vez más corta y emisión automatizada.** CA/Browser Forum, *Ballot SC081v3: Introduce Schedule of Reducing Validity and Data Reuse Periods*, aprobado el 11 de abril de 2025 (https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/). El calendario lo resume DigiCert (https://knowledge.digicert.com/alerts/public-tls-certificates-199-day-validity): 200 días desde el 15 de marzo de 2026, **100 días desde el 15 de marzo de 2027** y 47 días en 2029. Una credencial que vive poco vale poco si la roban, pero eso obliga a automatizar su emisión. **Cómo se implementa:** la credencial del coordinador vive como máximo 60 s, y `identidad.emitir` recorta el TTL aunque se pida más (lo prueba `tests/test_identidad.py`). Se emite por código en cada corrida, sin intervención manual. **Medida:** el uso de la credencial vencida da 401 `motivo=vencido` y la regla lo detecta en 0,23 s. La ronda 0 lo aceptaba con 200. SC-081 aplica a certificados TLS públicos, no a JWT. Aquí se aplica el mismo principio a la credencial de máquina, y el paso literal sería el mTLS con certificados de vida corta de la sección 11.

## 11. Lecciones y siguientes experimentos

Un secreto compartido que no vence convierte cualquier copia en el coordinador. Detectar el abuso exige que cada uso deje quién, desde dónde, con qué alcance y con qué trace. Contenerlo exige poder revocar sin reiniciar.

Los siguientes pasos serían:

- Repetir el experimento con el coordinador real en GCP: Workload Identity, y alerta en Cloud Logging por un `principalEmail` desde un origen no previsto.
- Atar el token con mTLS.
- Persistir la lista de revocados.
