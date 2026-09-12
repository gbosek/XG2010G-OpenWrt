# XG2010G Local Build Handoff

This file is the canonical handoff for the local-PC GPT/Codex session.

## Goal
Continue XG2010G OpenWrt/ImmortalWrt Linux 6.18.44 development locally because GitHub Actions private-repo minutes are exhausted. Do not spend Actions minutes unless explicitly requested.

Target device: Gemtek XG2010G, AN7581/EN7581.

Critical hardware requirements:
- LAN1: internal 1G.
- LAN2: Airoha EN8811H at MDIO 0x0f, 2.5G target with 1G fallback, `phy-mode = "2500base-x"`, `pcs-handle = <&usb_pcs>`.
- LAN3: RTL8261-class/RTL8261BE at MDIO 0x08, USXGMII, PCIe PCS lane 1.
- LAN4: RTL8261-class/RTL8261BE at MDIO 0x05, USXGMII, ETH PCS.
- Known 10G bug: copper side can negotiate 10G while host-side USXGMII/PCS/phylink carrier stays down. Preserve the delayed reset/retrain workaround plus project tuning writes `0x80aa` and `0x5078`.
- PON must support GPON + XG-PON/XGS-PON, EN7572 optical frontend, OMCI/OAM, LuCI, and PON datapath to PPE/NPU/QDMA.
- NPU success must be proven by PPE/FOE/QDMA/datapath counters/flow behavior, not just firmware load.

## Current repository state
Repository: `gbosek/XG2010G-OpenWrt`
Starting branch for local work: `work/local-build-handoff`
Parent work branch: `work/test4b-pon-control`
Known head before this handoff: `6eea9260b1b0f7148ec10bb631489380fecd91de`.

The previous GitHub Actions runs failed after long toolchain/kernel preparation. Do not blindly rerun them. Reproduce failures locally with logs preserved.

## Baseline sources
Pinned XG2010G baseline:
- repo: `https://github.com/naoki66/ImmortalWrt-for-Gemtek-XG2010G.git`
- commit: `b6bd44a7caf1b6979f1cb30433e33637b69e791e`

Public xPON source currently under test:
- repo: `https://github.com/Yuzhii0718/airoha-collection.git`
- commit: `d9454f2b13fef57a1a325591aff4cf02908a964a`
- package path: `airoha-pon`

Important: the public 6.18 xPON port compiles partly by disabling several original vendor ioctl/control paths with stubs. A successful build with those stubs is NOT proof of working GPON/XG-PON/XGS-PON. The real vendor handlers need to compile without being replaced by `-EOPNOTSUPP` / `-ENOTTY` stubs.

## Extracted PON userspace already in this private repo
`packages/basefw-parity/xg2010g-parity-v2.tar.xz`
SHA256:
`5d8a87780fbec056c21709ec86520faef93057dbfc9d7a7aeb0ed783542c94f4`

Expected extracted hashes:
- ponctl: `3bd8b7e264f6738de7eff66afa44068a9684fb0dd559b950ad702a2e59f7b01c`
- airoha-oamd: `aee701662d3c25f98c37eb91c600836e1cff1263f0664572eb83d3060f392429`
- airoha-omcid: `6e361fc1be99f64185b62b7e93fde1462d392309774a36af59dd4b1248850b63`
- rtl8261n.bin: `ae1963b2a84a17eaa2fb9052591bdb5152838feda045d7313f45a8608b918533`
- rtl8264b.bin: `7a0bcf605739d6f780e0799bbea0c73acf56c9a4cbba015da5d27589bf4352ca`

Do not publish these extracted proprietary payloads in a public repository.

## Local environment
Recommended host: Windows 11 + WSL2 + Ubuntu 24.04.
Ryzen 9 9950X is more than sufficient. Prefer NVMe and at least ~100 GB free disk.

Install build dependencies inside Ubuntu:
```bash
sudo apt update
sudo apt install -y build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-setuptools rsync swig unzip zlib1g-dev \
  file wget xsltproc curl kmod binutils device-tree-compiler
```

## First local workflow
From the user's working directory:
```bash
git clone https://github.com/gbosek/XG2010G-OpenWrt.git
cd XG2010G-OpenWrt
git checkout work/local-build-handoff
```

Then create a separate build tree from the pinned baseline. Do not compile inside the orchestration repository root.

Suggested layout:
```text
~/xg2010g/
  project/   # this repository
  src/       # pinned naoki66 ImmortalWrt baseline
  logs/
  out/
```

## Immediate task order
1. Reproduce the PON-control gate locally first, not full `make world`.
2. Preserve complete logs for every stage.
3. Build host tools and toolchain once, then reuse them.
4. Prepare/configure the 6.18.44 Airoha kernel tree.
5. Compile extracted PON userspace packages and `luci-app-xg2010g` locally.
6. Inject the Yuzhii0718 `airoha-pon` package and compile its real GPON/XG-PON/XGS-PON ioctl paths, not stub-only paths.
7. Fix the first real compiler/API incompatibility encountered. Do not hide errors behind new stubs.
8. Only after package/xPON gates pass, run the complete Test-4B image build.
9. Inspect final rootfs/kernel/DTB and package/firmware hashes before any device test.
10. Runtime validation must start with initramfs/TFTP temporary boot. Do NOT sysupgrade first.

## Useful local commands
Keep diagnostic builds serial until stable:
```bash
make -j1 target/linux/prepare V=s
make -j1 target/linux/dtb V=s
make -j1 package/luci-app-xg2010g/basefw-parity/compile V=s
make -j1 package/luci-app-xg2010g/compile V=s
make -j1 package/kernel/airoha-pon/compile V=s
```

For a final full build on the 9950X, start conservatively with something like:
```bash
make -j16 world V=s
```
If memory is plentiful and the build is stable, parallelism can be raised later.

## Safety / acceptance criteria
Do not tell the user to flash until a complete image exists and static checks pass.

Required runtime checks after a safe initramfs/TFTP boot:
- LAN2: 1G carrier + traffic, then 2.5G carrier + traffic.
- LAN3/LAN4: 10G copper negotiation AND Linux carrier/PCS/phylink up, then bidirectional iperf.
- PON: frontend detection, requested mode, O5, ONU-ID, OMCI, Alloc-ID/GEM-ID, datapath table, real traffic.
- NPU/PPE/QDMA: FOE bind/counters, PPE1/PPE2 behavior, QDMA counters/errors, PON mapping, XGEM RX/TX, PPPoE/NAT/IPv6 offload where applicable.

## How the local GPT/Codex should work
- Act directly on the local checkout and shell, not just give instructions.
- Keep a concise running log in `LOCAL_BUILD_STATUS.md` with commands, failures, fixes, and current SHA.
- Commit meaningful fixes to `work/local-build-handoff` with small commits.
- Do not rewrite or delete known-good patches just to make CI green.
- Do not use GitHub Actions unless explicitly requested by the user.
- When blocked, report the exact first compiler error and the file/function involved.
