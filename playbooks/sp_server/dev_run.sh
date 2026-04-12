#!/usr/bin/env bash
set -e

# Defaults (optional)
OS=""
MODE=""

INVENTORY="inventory.ini"
MODULE_DIR="/Users/nikhil/Downloads/Nikk-dev/omni-my-dev/ansible-storage-protect-shalu-fork/ansible-storage-protect/plugins"

usage() {
  echo "Usage: $0 --os=<linux|windows|aix> --mode=<install|config|all>"
  exit 1
}

# -------------------------
# Parse flags
# -------------------------
for arg in "$@"; do
  case $arg in
    --os=*)
      OS="${arg#*=}"
      ;;
    --mode=*)
      MODE="${arg#*=}"
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $arg"
      usage
      ;;
  esac
done

# -------------------------
# Validate inputs
# -------------------------
if [[ -z "$OS" || -z "$MODE" ]]; then
  echo "ERROR: --os and --mode are required"
  usage
fi

case "$OS" in
  linux)
    LIMIT="sp_server_linux"
    ;;
  windows)
    LIMIT="sp_server_windows"
    ;;
  aix)
    LIMIT="sp_server_aix"
    ;;
  *)
    echo "ERROR: Invalid OS: $OS"
    usage
    ;;
esac

# -------------------------
# Functions
# -------------------------
run_install() {
  echo "Running INSTALL for $OS"
  ansible-playbook playbook.yml -i "$INVENTORY" \
    -e sp_source_module_dir="$MODULE_DIR" -v \
    --limit "$LIMIT"
}

run_config() {
  echo "Running CONFIG for $OS"
  ansible-playbook playbook_configure.yml -i "$INVENTORY" \
    -e sp_source_module_dir="$MODULE_DIR" -v \
    --limit "$LIMIT"
}

# -------------------------
# Execute based on mode
# -------------------------
case "$MODE" in
  install)
    run_install
    ;;
  config)
    run_config
    ;;
  all)
    run_install
    run_config
    ;;
  *)
    echo "ERROR: Invalid mode: $MODE"
    usage
    ;;
esac