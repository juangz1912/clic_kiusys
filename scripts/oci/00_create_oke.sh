#!/usr/bin/env bash
# Crea VCN + cluster OKE Basic + node pool.
# Por defecto E5.Flex (x86): Ampere A1 gratis suele dar "Out of host capacity" en sa-bogota-1.
# Idempotente: guarda los OCID creados en scripts/oci/.oke_ids y los reutiliza.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/scripts/oci/oci.env"

IDS="$ROOT/scripts/oci/.oke_ids"
touch "$IDS"
# shellcheck source=/dev/null
source "$IDS"

C="$OCI_COMPARTMENT_ID"
K8S_VERSION="${K8S_VERSION:-v1.36.1}"
NODE_SHAPE="${NODE_SHAPE:-VM.Standard.E5.Flex}"
NODE_OCPUS="${NODE_OCPUS:-1}"
NODE_MEMORY_GB="${NODE_MEMORY_GB:-8}"
NODE_COUNT="${NODE_COUNT:-2}"
VCN_CIDR="10.0.0.0/16"

save() {
  if [ -z "$2" ]; then
    echo "No se obtuvo $1." >&2
    exit 1
  fi
  echo "$1=$2" >> "$IDS"
  export "$1=$2"
  echo "  $1=$2"
}

# La CLI no parsea bien JSON inline; los tipos complejos van por file://
json_arg() {
  local f
  f="$(mktemp)"
  printf '%s' "$1" > "$f"
  echo "file://$f"
}

# Ejecuta un "oci ... create" y devuelve el OCID creado (recurso o work request).
# La CLI a veces termina sin salida detrás del proxy; se reintenta.
create() {
  local kind="$1" out attempt
  shift
  for attempt in 1 2 3; do
    if out="$("$@")" && [ -n "$out" ]; then
      printf '%s' "$out" | python3 -c '
import json, sys
data = json.load(sys.stdin)["data"]
if "resources" in data:
    ids = [r["identifier"] for r in data["resources"]
           if r.get("entity-type", "").lower() == sys.argv[1] and r.get("action-type") == "CREATED"]
    print(ids[0] if ids else "")
else:
    print(data["id"])
' "$kind"
      return 0
    fi
    echo "  sin respuesta de la CLI ($kind), reintento $attempt/3..." >&2
    sleep 5
  done
  echo "No se pudo crear $kind." >&2
  exit 1
}

echo "=== Red ==="
[ -n "${VCN_ID:-}" ] || save VCN_ID "$(create vcn oci network vcn create -c "$C" \
  --display-name clic-kiusys-vcn --dns-label clickiusys \
  --cidr-blocks "$(json_arg "[\"$VCN_CIDR\"]")" \
  --wait-for-state AVAILABLE)"

[ -n "${IGW_ID:-}" ] || save IGW_ID "$(create igw oci network internet-gateway create -c "$C" \
  --vcn-id "$VCN_ID" --display-name clic-kiusys-igw --is-enabled true \
  --wait-for-state AVAILABLE)"

[ -n "${RT_ID:-}" ] || save RT_ID "$(create rt oci network route-table create -c "$C" \
  --vcn-id "$VCN_ID" --display-name clic-kiusys-public-rt \
  --route-rules "$(json_arg "[{\"destination\":\"0.0.0.0/0\",\"destinationType\":\"CIDR_BLOCK\",\"networkEntityId\":\"$IGW_ID\"}]")" \
  --wait-for-state AVAILABLE)"

INGRESS_RULES="[
  {\"source\":\"$VCN_CIDR\",\"protocol\":\"all\",\"isStateless\":false},
  {\"source\":\"0.0.0.0/0\",\"protocol\":\"6\",\"isStateless\":false,\"tcpOptions\":{\"destinationPortRange\":{\"min\":6443,\"max\":6443}}},
  {\"source\":\"0.0.0.0/0\",\"protocol\":\"6\",\"isStateless\":false,\"tcpOptions\":{\"destinationPortRange\":{\"min\":80,\"max\":80}}},
  {\"source\":\"0.0.0.0/0\",\"protocol\":\"1\",\"isStateless\":false,\"icmpOptions\":{\"type\":3,\"code\":4}}
]"
[ -n "${SL_ID:-}" ] || save SL_ID "$(create sl oci network security-list create -c "$C" \
  --vcn-id "$VCN_ID" --display-name clic-kiusys-sl \
  --egress-security-rules "$(json_arg '[{"destination":"0.0.0.0/0","protocol":"all","isStateless":false}]')" \
  --ingress-security-rules "$(json_arg "$INGRESS_RULES")" \
  --wait-for-state AVAILABLE)"

create_subnet() {
  create subnet oci network subnet create -c "$C" --vcn-id "$VCN_ID" \
    --display-name "$1" --cidr-block "$2" --dns-label "$3" \
    --route-table-id "$RT_ID" --security-list-ids "$(json_arg "[\"$SL_ID\"]")" \
    --prohibit-public-ip-on-vnic false \
    --wait-for-state AVAILABLE
}

[ -n "${SUBNET_API_ID:-}" ] || save SUBNET_API_ID "$(create_subnet clic-kiusys-api 10.0.0.0/28 api)"
[ -n "${SUBNET_NODES_ID:-}" ] || save SUBNET_NODES_ID "$(create_subnet clic-kiusys-nodes 10.0.10.0/24 nodes)"
[ -n "${SUBNET_LB_ID:-}" ] || save SUBNET_LB_ID "$(create_subnet clic-kiusys-lb 10.0.20.0/24 lb)"

echo "=== Cluster OKE ${K8S_VERSION} (tarda ~7 min) ==="
[ -n "${CLUSTER_ID:-}" ] || save CLUSTER_ID "$(create cluster oci ce cluster create -c "$C" \
  --name clic-kiusys-oke --vcn-id "$VCN_ID" --kubernetes-version "$K8S_VERSION" \
  --type BASIC_CLUSTER \
  --endpoint-subnet-id "$SUBNET_API_ID" --endpoint-public-ip-enabled true \
  --service-lb-subnet-ids "$(json_arg "[\"$SUBNET_LB_ID\"]")" \
  --cluster-pod-network-options "$(json_arg '[{"cniType":"FLANNEL_OVERLAY"}]')" \
  --wait-for-state SUCCEEDED --wait-for-state FAILED --max-wait-seconds 1800)"

echo "=== Node pool ${NODE_COUNT}x ${NODE_SHAPE} (${NODE_OCPUS} OCPU / ${NODE_MEMORY_GB} GB) ==="
if [ -z "${NODE_POOL_ID:-}" ]; then
  AD="$(oci iam availability-domain list -c "$C" --query 'data[0].name' --raw-output)"
  if [[ "$NODE_SHAPE" == *A1* ]]; then
    ARCH_FILTER="contains(\"source-name\", 'aarch64')"
  else
    ARCH_FILTER="!contains(\"source-name\", 'aarch64') && !contains(\"source-name\", 'GPU')"
  fi
  IMAGE_ID="$(oci ce node-pool-options get --node-pool-option-id "$CLUSTER_ID" \
    --query "data.sources[?contains(\"source-name\", 'Oracle-Linux-9') && contains(\"source-name\", 'OKE-${K8S_VERSION#v}') && ${ARCH_FILTER}] | [0].\"image-id\"" \
    --raw-output)"
  echo "  AD=$AD"
  echo "  IMAGE_ID=$IMAGE_ID"
  save NODE_POOL_ID "$(create nodepool oci ce node-pool create -c "$C" --cluster-id "$CLUSTER_ID" \
    --name clic-kiusys-pool --kubernetes-version "$K8S_VERSION" \
    --node-shape "$NODE_SHAPE" \
    --node-shape-config "$(json_arg "{\"ocpus\":$NODE_OCPUS,\"memoryInGBs\":$NODE_MEMORY_GB}")" \
    --node-image-id "$IMAGE_ID" --size "$NODE_COUNT" \
    --placement-configs "$(json_arg "[{\"availabilityDomain\":\"$AD\",\"subnetId\":\"$SUBNET_NODES_ID\"}]")" \
    --wait-for-state SUCCEEDED --wait-for-state FAILED --max-wait-seconds 1800)"
fi

sed -i.bak "s|^OKE_CLUSTER_ID=.*|OKE_CLUSTER_ID=$CLUSTER_ID|" "$ROOT/scripts/oci/oci.env"
rm -f "$ROOT/scripts/oci/oci.env.bak"
echo ""
echo "OKE listo: $CLUSTER_ID"
echo "Siguiente: ./scripts/oci/03_kubeconfig.sh && ./scripts/oci/deploy_all.sh"
