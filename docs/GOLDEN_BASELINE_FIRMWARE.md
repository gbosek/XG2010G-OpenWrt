# XG2010G Golden Firmware Baseline

This project treats the user-supplied working image below as the functional golden baseline for Gemtek XG2010G work:

- File: `immortalwrt-airoha-an7581-gemtek_xg2010g-squashfs-sysupgrade (1)(1).itb`
- Size: `14098704` bytes
- SHA-256: `472d1aa72469cd6f173bde70e4ae55d8ac0e00b0af064e5fc2ab236b0501f503`
- FIT kernel description: `ARM64 OpenWrt Linux-6.18.44`
- Device: `gemtek_xg2010g`
- Target: `airoha/an7581`
- Distribution metadata: `ImmortalWrt SNAPSHOT`
- Firmware revision: `r40915+7-d2dc130d7f`

The revision embedded in the FIT maps to the public XG2010G ImmortalWrt source tree at:

- Source repository: `https://github.com/naoki66/ImmortalWrt-for-Gemtek-XG2010G.git`
- Source commit: `d2dc130d7f8341741df04eaaf5fd4c74dcc447d7`

`source.lock` must remain pinned to that exact source commit unless a deliberate baseline migration is made and documented.

## Baseline policy

The uploaded binary is the functional oracle, not a disposable old image. New builds must preserve the working baseline behaviour unless a change is intentional and validated.

Do not upload or redistribute the full golden ITB from CI. This public repository stores only its identity/hash and reproducible source mapping.

The following are regression-sensitive:

- XG2010G NAND/UBI/FIT layout and bootability.
- Airoha AN7581/EN7581 Ethernet/NPU/PPE/QDMA data path.
- EN7572 PON frontend and xPON MAC/PCS integration.
- GPON, XG-PON and XGS-PON control paths, OMCI/OAM, ONU-ID/OMCC/GEM/TCONT behaviour.
- LAN1 internal 1G mapping.
- LAN2 EN8811H at MDIO `0x0f`, `2500base-x`, including 1G compatibility and 2.5G operation.
- LAN3 RTL8261-class PHY at MDIO `0x08`, USXGMII with PCIe PCS lane 1.
- LAN4 RTL8261-class PHY at MDIO `0x05`, USXGMII with ETH PCS.
- PON-to-PPE/NPU/QDMA forwarding and hardware-offload counters.

## Current repair scope

Changes are allowed only to fix or expose known issues while keeping the baseline intact:

1. LAN2 EN8811H 1G/2.5G link and traffic.
2. LAN3/LAN4 RTL8261 host-side USXGMII/PCS/phylink carrier and 10G traffic.
3. Functional PON LuCI backed by the real PON userspace/control stack.
4. NPU LuCI/diagnostics proving PPE/FOE/QDMA offload rather than merely firmware loading.
5. Linux 6.18 build reproducibility from the exact golden source revision.

A CI compile PASS is not a flash approval. Final images still require rootfs/module/DTB/firmware checks followed by initramfs/TFTP runtime validation before any sysupgrade test.
