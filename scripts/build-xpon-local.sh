#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/src-xpon"
PON_SRC="$REPO_ROOT/airoha-collection"
OUT="$REPO_ROOT/output/xpon-probe"
LOG="$OUT/logs"

SOURCE_REPO="${SOURCE_REPO:-https://github.com/naoki66/ImmortalWrt-for-Gemtek-XG2010G.git}"
SOURCE_COMMIT="${SOURCE_COMMIT:-b6bd44a7caf1b6979f1cb30433e33637b69e791e}"
PON_REPO="${PON_REPO:-https://github.com/Yuzhii0718/airoha-collection.git}"
PON_COMMIT="${PON_COMMIT:-d9454f2b13fef57a1a325591aff4cf02908a964a}"
JOBS="${JOBS:-2}"

if [[ ${EUID} -eq 0 ]]; then
  echo "ERROR: OpenWrt must be built as a normal user, not root." >&2
  exit 1
fi

mkdir -p "$OUT" "$LOG"

stage() {
  local name="$1"; shift
  echo "==== $name ===="
  set +e
  "$@" >"$LOG/$name.log" 2>&1
  local rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "ERROR: $name failed (rc=$rc). Last 160 lines:" >&2
    tail -n 160 "$LOG/$name.log" >&2 || true
    return "$rc"
  fi
  tail -n 30 "$LOG/$name.log" || true
}

sync_repo() {
  local dir="$1" url="$2" commit="$3"
  if [[ ! -d "$dir/.git" ]]; then
    git clone --filter=blob:none "$url" "$dir"
  fi
  git -C "$dir" remote set-url origin "$url"
  git -C "$dir" fetch --prune origin "$commit"
  git -C "$dir" reset --hard "$commit"
  git -C "$dir" clean -fd
  test "$(git -C "$dir" rev-parse HEAD)" = "$commit"
}

sync_repo "$SRC" "$SOURCE_REPO" "$SOURCE_COMMIT"
sync_repo "$PON_SRC" "$PON_REPO" "$PON_COMMIT"

rm -rf "$SRC/package/kernel/airoha-pon" "$SRC/package/luci-app-xg2010g"
cp -a "$PON_SRC/airoha-pon" "$SRC/package/kernel/airoha-pon"
cp -a "$REPO_ROOT/packages/luci-app-xg2010g" "$SRC/package/luci-app-xg2010g"

test -f "$SRC/package/kernel/airoha-pon/Makefile"
test -f "$SRC/package/kernel/airoha-pon/patches/001-port-vendor-drivers-to-linux-6.18.patch"
grep -q 'TARGET_airoha_an7581' "$SRC/package/kernel/airoha-pon/Makefile"
grep -q 'Linux 6.18' "$SRC/package/kernel/airoha-pon/patches/001-port-vendor-drivers-to-linux-6.18.patch"

cd "$SRC"
stage feeds-update ./scripts/feeds update -a
stage feeds-install ./scripts/feeds install -a

cat > .config <<'EOF'
CONFIG_TARGET_airoha=y
CONFIG_TARGET_airoha_an7581=y
CONFIG_TARGET_airoha_an7581_DEVICE_gemtek_xg2010g=y
CONFIG_PACKAGE_kmod-airoha-xpon-en757x=y
CONFIG_PACKAGE_kmod-i2c-core=y
EOF
stage defconfig make defconfig
grep -q '^CONFIG_PACKAGE_kmod-airoha-xpon-en757x=y$' .config || {
  echo "ERROR: public EN757x xPON package disappeared after defconfig." >&2
  exit 2
}
cp .config "$OUT/xpon.config"
printf '%s\n' "$SOURCE_COMMIT" > "$OUT/source-commit.txt"
printf '%s\n' "$PON_COMMIT" > "$OUT/pon-source-commit.txt"

stage tools-install make -j"$JOBS" tools/install V=s
stage toolchain-install make -j"$JOBS" toolchain/install V=s
stage target-linux-prepare make -j1 target/linux/prepare V=s
stage target-linux-dtb make -j1 target/linux/dtb V=s

KBASE="$SRC/build_dir/target-aarch64_cortex-a53_musl/linux-airoha_an7581"
KDIR="$(find "$KBASE" -maxdepth 1 -type d -name 'linux-*' -print -quit)"
test -n "$KDIR" && test -s "$KDIR/.config"
printf '%s\n' "$KDIR" > "$OUT/kernel-dir.txt"

# Force a fresh package prepare so the source rewrite below is deterministic.
make package/kernel/airoha-pon/clean >/dev/null 2>&1 || true
stage xpon-prepare make -j1 package/kernel/airoha-pon/prepare V=s

GPON="$(find build_dir -type f -path '*/xpon_10g/src/xmcs/xmcs_gpon.c' -print -quit)"
FDET="$(find build_dir -type f -path '*/xpon_10g/src/xmcs/xmcs_fdet.c' -print -quit)"
IFC="$(find build_dir -type f -path '*/xpon_10g/src/xmcs/xmcs_if.c' -print -quit)"
MCI="$(find build_dir -type f -path '*/xpon_10g/src/xmcs/xmcs_mci.c' -print -quit)"
PHY="$(find build_dir -type f -path '*/xpon_10g/src/xmcs/xmcs_phy.c' -print -quit)"
for f in "$GPON" "$FDET" "$IFC" "$MCI" "$PHY"; do
  test -s "$f" || { echo "ERROR: prepared xPON source missing: $f" >&2; exit 3; }
done

python3 "$REPO_ROOT/scripts/restore-xpon-ioctl.py" "$GPON" "$FDET" "$IFC" "$MCI" "$PHY" \
  | tee "$OUT/restored-ioctl.txt"
grep -n -E '^(long pon_mci_ioctl|int (gpon_10g_cmd_proc|gpon_cmd_proc|rdkb_10g_cmd_proc|if_cmd_proc|fdet_cmd_proc|phy_cmd_proc))' \
  "$GPON" "$FDET" "$IFC" "$MCI" "$PHY" > "$OUT/restored-ioctl-symbols.txt"

stage xpon-driver-compile make -j1 package/kernel/airoha-pon/compile V=s

find build_dir -type f \( -name 'xpon_10g.ko' -o -name 'phy_10g.ko' -o -name 'airoha_ecnt_pon_phy.ko' \) \
  -print | tee "$OUT/xpon-modules.txt"
grep -q 'xpon_10g.ko' "$OUT/xpon-modules.txt"
grep -q 'phy_10g.ko' "$OUT/xpon-modules.txt"
grep -q 'airoha_ecnt_pon_phy.ko' "$OUT/xpon-modules.txt"

find bin -type f \( -name 'kmod-airoha-xpon-en757x*.apk' -o -name 'kmod-airoha-xpon-en757x*.ipk' \) \
  -print | tee "$OUT/xpon-package.txt"
test -s "$OUT/xpon-package.txt"

while IFS= read -r f; do cp -v "$f" "$OUT/"; done < "$OUT/xpon-modules.txt"
while IFS= read -r f; do cp -v "$f" "$OUT/"; done < "$OUT/xpon-package.txt"
(
  cd "$OUT"
  sha256sum *.ko *.apk *.ipk 2>/dev/null || true
) > "$OUT/sha256sums.txt"

cat > "$OUT/RESULT.txt" <<EOF
PASS: EN7581 public xPON source compiled with original GPON/XG-PON/XGS-PON ioctl paths restored.
ImmortalWrt baseline: $SOURCE_COMMIT
xPON source: $PON_COMMIT
This is a compile proof only; runtime O5/OMCI/XGEM/datapath validation is still required before flashing a full image.
EOF
cat "$OUT/RESULT.txt"
