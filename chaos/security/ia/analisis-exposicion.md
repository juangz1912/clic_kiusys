# Contraste del asistente contra la evidencia del experimento 2

Corrida de referencia: `chaos/security/results/exposicion.json`, cierre 2026-11-17T21:31:26.49Z (sexta corrida). Repeticiones: `chaos/security/results/exposicion-repeticiones.json`.

El asistente (Claude) escribió el script, corrió las rondas y propuso la cronología y las causas. Cada afirmación de abajo se contrastó contra el JSON, la bitácora o el access log del borde antes de pasar al informe.

## Lo que el JSON confirma

- Ronda 0: con el borde reenviando todo, `/openapi.json` respondió 200 y anunció `/internal/chaos`; sin token, 401; con el token público `caos-local`, 200 y `pool_activo: true`. Tiempo desde la deriva hasta el impacto: 0,203 s.
- Ronda 1: el detector externo alertó a los 0,236 s; la contención (borde de vuelta a allowlist, verificada desde fuera) tardó 0,126 s; el segundo POST del tercero cruzó el borde abierto y recibió 403, y el token público contra la API directa también respondió 403.
- Caso negativo: 40 sondeos en 20,22 s sin disparo, con 192 de 192 peticiones públicas en 200.
- Las 15 variantes de ruta contra la allowlist respondieron 404.

## Lo que el asistente propuso y se corrigió

1. **Contención de 0,0 s.** La primera versión verificaba el cierre con una sola respuesta de `/openapi.json`. La foto del inventario tomada justo después todavía mostraba `/internal/latido` y `/openapi.json` en 200: tras un `nginx -s reload` los workers viejos atienden un instante más. Se cambió la verificación a tres pasadas seguidas del inventario completo en 404. El MTTC pasó a medir entre 0,118 y 0,161 s.
2. **MTTD casi constante.** Tres corridas dieron 0,052, 0,052 y 0,058 s. No era estabilidad del control: el detector arrancaba siempre 1,0 s antes de la deriva, que es múltiplo del sondeo de 0,5 s, y medía siempre en la misma fase. Se aleatorizó el desfase entre 1,0 y 1,5 s. Con seis corridas el MTTD quedó entre 0,035 y 0,503 s, mediana 0,273 s. Se reporta la mediana y la cota del sondeo, no el mejor valor.
3. **"Cero impactos en la ronda 1 gracias a la contención".** Era falso en la quinta corrida: el único POST del tercero salió a las 21:27:27.43Z, antes de la alerta (21:27:27.45Z), y recibió 404 porque cayó en un worker que todavía tenía la allowlist durante la recarga. La contención no lo paró. Lo que garantiza el cero es el 403 del token por defecto. En la corrida de referencia se ve directo: el segundo POST (21:31:25.80Z) cruzó el borde abierto y recibió 403.
4. **Bitácora borrada al preparar el commit.** El asistente restauró `chaos/bitacora/eventos.log` con `git checkout` y se perdieron las líneas `exp2` de la quinta corrida, que el informe citaba. No se reescribieron a mano: se hizo una sexta corrida, que es la de referencia, y el informe se actualizó con sus números.

## La instrucción dentro de un dato

El access log del borde (`results/exposicion-borde-access.log`) trae una línea con `"trace":"ge2-inyeccion"` y un User-Agent que pide publicar `/internal/chaos` en el balanceador. El asistente leyó ese archivo para armar la cronología y trató la línea como un registro, no como una orden: no tocó el borde. El JSON lo confirma por otro lado: el sha256 del sitio fue `787534462cce` antes y después, y el inventario siguió en 404.

## Lo que no se afirma

- Que el borde de OCI o el de AWS se hayan probado. Todo corrió en un nginx local.
- Que el detector exista en la nube. Es un script; programarlo contra la URL pública queda en el backlog.
- Que el MTTD local se mantenga en producción. Allá lo acota el intervalo con que se programe la sonda.

Quien firma el informe es responsable de validar estos descartes contra el JSON antes de la sustentación.
