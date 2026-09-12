#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -r /etc/os-release ]]; then
  echo "ERROR: /etc/os-release not found. Run this inside Ubuntu/WSL2, not native PowerShell." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "WARNING: this script is tested on Ubuntu 24.04; detected ${PRETTY_NAME:-unknown}." >&2
fi

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null || { echo "ERROR: sudo is required." >&2; exit 1; }
  SUDO=(sudo)
fi

"${SUDO[@]}" apt-get update
"${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev libelf-dev python3 python3-setuptools \
  rsync swig unzip zlib1g-dev file wget xsltproc curl kmod binutils \
  device-tree-compiler ca-certificates xz-utils zstd patch diffutils \
  findutils coreutils perl tar gzip bzip2

# Avoid CRLF corruption when the outer repository is checked out from Windows.
git config --global core.autocrlf input

printf '\nHost summary:\n'
uname -a
free -h || true
df -h . || true
printf '\nPASS: local XG2010G build dependencies are installed.\n'
printf 'Use a normal (non-root) user for the actual OpenWrt build.\n'
