#!/bin/bash
# Copia el API a la VM y lo deja corriendo. Lo llama el pipeline después de terraform apply.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
source ./env.sh
export PATH="$HOME/.local/bin:$PATH"

ROOT="$(cd .. && pwd)"
API_IP="$(terraform output -raw api_public_ip)"
LB_IP="$(terraform output -raw api_url | sed 's|http://||; s|/api/v2/health||')"
KEY="$PWD/.ssh_key"
trap 'rm -f "$KEY"' EXIT
terraform output -raw ssh_private_key > "$KEY"
chmod 600 "$KEY"

SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8 opc@"$API_IP")

echo "Esperando SSH en $API_IP"
for _ in $(seq 1 36); do
  if "${SSH[@]}" 'echo ok' >/dev/null 2>&1; then
    break
  fi
  sleep 10
done
"${SSH[@]}" 'echo ok' >/dev/null

echo "Esperando cloud-init"
"${SSH[@]}" 'sudo cloud-init status --wait'

echo "Esperando Postgres local"
"${SSH[@]}" "python3 - <<'PY'
import socket, time, sys
for _ in range(60):
    try:
        socket.create_connection(('127.0.0.1', 5432), 5).close()
        sys.exit(0)
    except OSError:
        time.sleep(10)
sys.exit('Postgres no abrió el puerto 5432')
PY"

tar -C "$ROOT" -czf /tmp/clic-api.tgz app requirements.txt
scp -i "$KEY" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null /tmp/clic-api.tgz "opc@$API_IP:/tmp/clic-api.tgz"

echo "Instalando dependencias y arrancando uvicorn"
"${SSH[@]}" "sudo bash -s" <<EOF
set -euo pipefail
mkdir -p /opt/clic-kiusys
tar -xzf /tmp/clic-api.tgz -C /opt/clic-kiusys
if ! grep -q '^PUBLIC_API_BASE_URL=' /opt/clic-kiusys/api.env; then
  echo 'PUBLIC_API_BASE_URL=http://${LB_IP}' >> /opt/clic-kiusys/api.env
fi
python3 -m venv /opt/clic-kiusys/venv
/opt/clic-kiusys/venv/bin/pip install --upgrade pip
/opt/clic-kiusys/venv/bin/pip install -r /opt/clic-kiusys/requirements.txt
sed -i 's|^ExecStart=.*|ExecStart=/opt/clic-kiusys/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000|' /etc/systemd/system/clic-api.service
systemctl daemon-reload
systemctl restart clic-api.service
systemctl is-active clic-api.service
EOF

echo "Esperando /api/v2/health"
for _ in $(seq 1 30); do
  if curl -fsS "http://${LB_IP}/api/v2/health"; then
    echo
    exit 0
  fi
  sleep 10
done
echo "El balanceador todavía no responde. Prueba directo:" >&2
curl -fsS "http://${API_IP}:8000/api/v2/health"
echo
