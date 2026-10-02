# Exporta TF_VAR_* desde la config de OCI CLI. No imprime secretos.
# Uso: source ./env.sh

config="${OCI_CLI_CONFIG_FILE:-$HOME/.oci/apikey.config}"
if [[ ! -f "$config" && -f "$HOME/.oci/config" ]]; then
  config="$HOME/.oci/config"
fi

if [[ ! -f "$config" ]]; then
  echo "No está la config de OCI en $config" >&2
  return 1 2>/dev/null || exit 1
fi

_tf_get() {
  awk -F= -v k="$1" '$1==k {sub(/^[^=]*=/, ""); print; exit}' "$config" | tr -d '[:space:]'
}

export TF_VAR_tenancy_ocid="$(_tf_get tenancy)"
export TF_VAR_user_ocid="$(_tf_get user)"
export TF_VAR_fingerprint="$(_tf_get fingerprint)"
export TF_VAR_private_key_path="$(_tf_get key_file)"
export TF_VAR_region="$(_tf_get region)"
export OCI_CLI_AUTH=api_key
export OCI_CLI_CONFIG_FILE="$config"
export OCI_CLI_REGION="${TF_VAR_region}"

unset -f _tf_get
