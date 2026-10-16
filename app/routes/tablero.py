from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Canary vs stable</title>
<style>
  body { font-family: Georgia, serif; margin: 24px; color: #1c1c1c; }
  h1 { font-size: 22px; }
  .cols { display: flex; gap: 16px; }
  section { flex: 1; border: 1px solid #ccc; padding: 12px 16px; }
  .stable { background: #f4f7fb; }
  .canary { background: #fbf6ee; }
  dt { font-weight: bold; }
  dd { margin: 0 0 8px; }
</style>
</head>
<body>
<h1>Stable (v2) y canary (v3)</h1>
<p>El balanceador manda <code>x-canary: false</code> a stable y <code>x-canary: true</code> al canary. Esta página se refresca sola.</p>
<div class="cols">
  <section class="stable"><h2>Stable</h2><dl id="stable"></dl></section>
  <section class="canary"><h2>Canary</h2><dl id="canary"></dl></section>
</div>
<pre id="aviso"></pre>
<script>
const campos = ["version","track","requests","errors_5xx","errors_4xx","error_ratio_5xx","latency_p50_ms","latency_p95_ms","latency_p99_ms","cpu_percent","memory_mb","estado_operativo_cambios"];
function pintar(id, data) {
  const dl = document.getElementById(id);
  dl.innerHTML = campos.map(k => "<dt>" + k + "</dt><dd>" + data[k] + "</dd>").join("");
}
async function cargar() {
  const aviso = document.getElementById("aviso");
  try {
    const [s, c] = await Promise.all([
      fetch("/api/v2/sli", {headers: {"x-canary": "false"}}).then(r => r.json()),
      fetch("/api/v3/sli", {headers: {"x-canary": "true"}}).then(r => r.json())
    ]);
    pintar("stable", s);
    pintar("canary", c);
    aviso.textContent = "";
  } catch (err) {
    aviso.textContent = "No pude leer los dos tracks: " + err;
  }
}
cargar();
setInterval(cargar, 5000);
</script>
</body>
</html>
"""


@router.get("/tablero", response_class=HTMLResponse)
def tablero():
    return HTML
