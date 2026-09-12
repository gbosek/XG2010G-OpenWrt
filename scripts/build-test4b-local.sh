#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/src"
OUT="$REPO_ROOT/output/test4b"
LOG="$OUT/logs"
SOURCE_REPO="${SOURCE_REPO:-https://github.com/naoki66/ImmortalWrt-for-Gemtek-XG2010G.git}"
SOURCE_COMMIT="${SOURCE_COMMIT:-b6bd44a7caf1b6979f1cb30433e33637b69e791e}"
JOBS="${JOBS:-2}"
PON_MODE="${PON_MODE:-strict}"   # strict = final target; off = LAN/NPU smoke image only

if [[ ${EUID} -eq 0 ]]; then
  echo "ERROR: OpenWrt must be built as a normal user, not root." >&2
  exit 1
fi
case "$PON_MODE" in strict|off) ;; *) echo "ERROR: PON_MODE must be strict or off" >&2; exit 1;; esac

mkdir -p "$OUT" "$LOG"

stage() {
  local name="$1"; shift
  echo "==== $name ===="
  set +e
  "$@" >"$LOG/$name.log" 2>&1
  local rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "ERROR: $name failed (rc=$rc). Last 180 lines:" >&2
    tail -n 180 "$LOG/$name.log" >&2 || true
    return "$rc"
  fi
  tail -n 30 "$LOG/$name.log" || true
}

if [[ ! -d "$SRC/.git" ]]; then
  git clone --filter=blob:none "$SOURCE_REPO" "$SRC"
fi
git -C "$SRC" remote set-url origin "$SOURCE_REPO"
git -C "$SRC" fetch --prune origin "$SOURCE_COMMIT"
git -C "$SRC" reset --hard "$SOURCE_COMMIT"
git -C "$SRC" clean -fd
test "$(git -C "$SRC" rev-parse HEAD)" = "$SOURCE_COMMIT"
printf '%s\n' "$SOURCE_COMMIT" > "$OUT/source-commit.txt"

# Inject our package only for the strict PON-capable target. The package depends
# on the real PON control stack and is intentionally not used in smoke mode.
if [[ "$PON_MODE" == strict ]]; then
  cp -a "$REPO_ROOT/packages/luci-app-xg2010g" "$SRC/package/luci-app-xg2010g"
  chmod +x "$SRC/package/luci-app-xg2010g/root/usr/libexec/xg2010g-status"
  chmod +x "$SRC/package/luci-app-xg2010g/root/usr/libexec/xg2010g-dsd"
  chmod +x "$SRC/package/luci-app-xg2010g/root/usr/libexec/xg2010g-pon"
fi

# RTL8261 host-side USXGMII/SerDes recovery + opt-in for MDIO 0x08/0x05.
cp "$REPO_ROOT/patches/743-net-phy-realtek-xg2010g-d2dc-rtk-serdes.patch" \
  "$SRC/target/linux/generic/pending-6.18/744-net-phy-realtek-xg2010g-serdes-tuning.patch"
(
  cd "$SRC"
  patch -p1 < "$REPO_ROOT/patches/746-airoha-xg2010g-enable-rtl8261-serdes-tuning.patch"
)

DTS_REL="target/linux/airoha/dts/an7581-gemtek-xg2010g.dts"
DTS="$SRC/$DTS_REL"
python3 "$REPO_ROOT/scripts/prepare-test4b-dts.py" "$DTS"
(
  cd "$SRC"
  git diff --check
  git diff -- "$DTS_REL" > "$OUT/test4b-dts.diff"
)

cd "$SRC"
stage feeds-update ./scripts/feeds update -a
stage feeds-install ./scripts/feeds install -a

cat > .config <<'EOF'
CONFIG_TARGET_airoha=y
CONFIG_TARGET_airoha_an7581=y
CONFIG_TARGET_airoha_an7581_DEVICE_gemtek_xg2010g=y
CONFIG_PACKAGE_luci=y
CONFIG_PACKAGE_ubi-utils=y
CONFIG_PACKAGE_nftables-json=y
CONFIG_PACKAGE_mwan3=y
CONFIG_PACKAGE_luci-app-mwan3=y
CONFIG_VERSION_DIST="XG2010G-Test4B"
CONFIG_VERSION_NUMBER="6.18.44-basefw-local"
EOF

if [[ "$PON_MODE" == strict ]]; then
  printf '%s\n' 'CONFIG_PACKAGE_luci-app-xg2010g=y' >> .config
  cat "$REPO_ROOT/configs/test4b-basefw-full-packages.config" >> .config
else
  # Smoke mode is deliberately not presented as a final firmware. It is useful
  # for proving the pinned baseline, LAN2/RTL8261 fixes and the basic image build
  # while the xPON driver is being repaired separately.
  grep -Ev '^CONFIG_PACKAGE_(airoha-oamd|airoha-omcid|airoha-pon-debug|airoha-ponctl|kmod-airoha-en7572|kmod-airoha-xpon|luci-app-pon|luci-i18n-pon-zh-cn)=' \
    "$REPO_ROOT/configs/test4b-basefw-full-packages.config" >> .config
  printf '%s\n' 'CONFIG_VERSION_NUMBER="6.18.44-basefw-lan-smoke"' >> .config
fi

stage defconfig make defconfig
cp .config "$OUT/test4b.config"
grep '^CONFIG_PACKAGE_' .config | sort > "$OUT/test4b-package-config.txt"

critical=(
  airoha-en8811h-firmware ethtool-full ip-full iperf3
  kmod-phy-airoha-en8811h kmod-phy-realtek rtl826x-firmware tcpdump wget-ssl
)
if [[ "$PON_MODE" == strict ]]; then
  critical+=(airoha-oamd airoha-omcid airoha-pon-debug airoha-ponctl kmod-airoha-en7572 kmod-airoha-xpon luci-app-pon luci-app-xg2010g)
fi
missing=()
for p in "${critical[@]}"; do
  grep -q "^CONFIG_PACKAGE_${p}=y$" .config || missing+=("$p")
done
if ((${#missing[@]})); then
  printf 'ERROR: required packages disappeared after defconfig:\n' >&2
  printf '  - %s\n' "${missing[@]}" >&2
  if [[ "$PON_MODE" == strict ]]; then
    cat >&2 <<'EOF'
The pinned ImmortalWrt board baseline does not itself provide the complete
working XG2010G xPON kernel package. This is an intentional hard stop: we will
not silently build a firmware that looks complete but has no real PON driver.
Run scripts/build-xpon-local.sh to repair/compile the public EN7581 xPON path.
For LAN/NPU-only build-system smoke testing, run PON_MODE=off.
EOF
  fi
  exit 4
fi

# Ensure the kernel tree is regenerated from the current patches/DTS while
# retaining downloaded sources and host toolchain caches.
make target/linux/clean >/dev/null 2>&1 || true
stage download make download -j"$JOBS"
stage target-linux-prepare make -j1 target/linux/prepare V=s

KBASE="$SRC/build_dir/target-aarch64_cortex-a53_musl/linux-airoha_an7581"
KDIR="$(find "$KBASE" -maxdepth 1 -type d -name 'linux-*' -print -quit)"
test -n "$KDIR" && test -d "$KDIR"
grep -q 'patch_rtk_serdes' "$KDIR/drivers/net/phy/realtek/realtek.h"
grep -q '0x80aa' "$KDIR/drivers/net/phy/realtek/realtek_main.c"
grep -q '0x5078' "$KDIR/drivers/net/phy/realtek/realtek_main.c"
printf '%s\n' "$KDIR" > "$OUT/kernel-dir.txt"

stage world make -j"$JOBS" world V=s

rm -rf "$OUT/artifacts"
mkdir -p "$OUT/artifacts"
find "$SRC/bin/targets/airoha/an7581" -maxdepth 1 -type f -name '*.itb' -exec cp -v {} "$OUT/artifacts/" \; 2>/dev/null || true
find "$SRC/bin" -type f \( -name '*luci-app-xg2010g*.apk' -o -name '*luci-app-xg2010g*.ipk' \) -exec cp -v {} "$OUT/artifacts/" \; 2>/dev/null || true
find "$SRC/build_dir" -type f -name '*xg2010g*.dtb' -exec cp -v {} "$OUT/artifacts/xg2010g-test4b.dtb" \; -quit 2>/dev/null || true

if [[ -f "$OUT/artifacts/xg2010g-test4b.dtb" ]] && command -v dtc >/dev/null; then
  dtc -I dtb -O dts "$OUT/artifacts/xg2010g-test4b.dtb" > "$OUT/artifacts/xg2010g-test4b.decompiled.dts"
  grep -n -E 'ethernet@3|ethernet-port@4|ethernet-port@5|lan1|lan2|lan3|lan4|2500base-x|usxgmii|ethernet-phy@8|ethernet-phy@5|ubi@20000|calibration@12000' \
    "$OUT/artifacts/xg2010g-test4b.decompiled.dts" > "$OUT/artifacts/test4b-dt-check.txt" || true
fi
(
  cd "$OUT/artifacts"
  sha256sum * 2>/dev/null || true
) > "$OUT/artifacts/sha256sums.txt"

if [[ "$PON_MODE" == strict ]]; then
  result="PASS: strict Test-4B image build completed. Runtime validation is still required before flashing."
else
  result="PASS: LAN/NPU smoke image build completed. PON is intentionally absent; DO NOT treat this as the final firmware."
fi
printf '%s\nImmortalWrt baseline: %s\n' "$result" "$SOURCE_COMMIT" | tee "$OUT/RESULT.txt"
