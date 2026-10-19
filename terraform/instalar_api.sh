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

tar -C "$ROOT" -czf /tmp/clic-api.tgz Dockerfile app requirements.txt pytest.ini
scp -i "$KEY" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null /tmp/clic-api.tgz "opc@$API_IP:/tmp/clic-api.tgz"

echo "Construyendo la imagen y levantando stable y canary"
"${SSH[@]}" "sudo bash -s" <<EOF
set -euo pipefail
mkdir -p /opt/clic-kiusys/src
tar -xzf /tmp/clic-api.tgz -C /opt/clic-kiusys/src
if ! grep -q '^PUBLIC_API_BASE_URL=' /opt/clic-kiusys/api.env; then
  echo 'PUBLIC_API_BASE_URL=http://${LB_IP}' >> /opt/clic-kiusys/api.env
fi
systemctl disable --now clic-api.service || true
podman build -t clic-kiusys:canary /opt/clic-kiusys/src
podman image inspect clic-kiusys:canary --format '{{.Digest}}' | tee /opt/clic-kiusys/image-digest.txt
podman rm -f clic-stable clic-canary || true
podman run -d --name clic-stable --network host --restart=always --env-file /opt/clic-kiusys/api.env \
  -e APP_TRACK=stable -e APP_VERSION=v2 -e PORT=8000 clic-kiusys:canary
podman run -d --name clic-canary --network host --restart=always --env-file /opt/clic-kiusys/api.env \
  -e APP_TRACK=canary -e APP_VERSION=v3 -e PORT=8001 clic-kiusys:canary
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
