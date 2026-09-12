# XG2010G Golden Firmware Baseline

This project treats the user-supplied working image below as the sole functional golden baseline for Gemtek XG2010G work:

- File: `immortalwrt-airoha-an7581-gemtek_xg2010g-squashfs-sysupgrade (1)(1).itb`
- Size: `14098704` bytes
- SHA-256: `472d1aa72469cd6f173bde70e4ae55d8ac0e00b0af064e5fc2ab236b0501f503`
- FIT kernel description: `ARM64 OpenWrt Linux-6.18.44`
- Device: `gemtek_xg2010g`
- Target: `airoha/an7581`
- Distribution metadata: `ImmortalWrt SNAPSHOT`
- Firmware revision string: `r40915+7-d2dc130d7f`

## Source/framework policy

The revision string embedded in the FIT is provenance, not proof that any public fork at that exact commit contains the complete XG2010G board source. In particular, the public naoki66 tree at `d2dc130d7f8341741df04eaaf5fd4c74dcc447d7` does not yet contain `target/linux/airoha/dts/an7581-gemtek-xg2010g.dts`.

Therefore:

- The uploaded ITB is the functional oracle.
- `naoki66/ImmortalWrt-for-Gemtek-XG2010G` is used only as a source/build framework reference.
- The framework is currently pinned separately in `source.lock` at `b6bd44a7caf1b6979f1cb30433e33637b69e791e`, because that tree contains the XG2010G target needed to run Linux 6.18 builds.
- No behaviour, partition map, DTS topology, PON stack, NPU/PPE/QDMA setup, or package set is accepted merely because it exists in the framework tree. Those must be restored from and checked against the uploaded golden firmware.

Do not upload or redistribute the full golden ITB from CI. This public repository stores its identity/hash plus only the extracted/reconstructed pieces required for reproducible regression work.

## Baseline policy

The uploaded binary is not a disposable old image. New builds must preserve its working behaviour unless a change is intentional and validated.

The following are regression-sensitive:

- XG2010G NAND/UBI/FIT layout and bootability.
- Airoha AN7581/EN7581 Ethernet/NPU/PPE/QDMA data path.
- EN7572 PON frontend and xPON MAC/PCS integration.
- GPON, XG-PON and XGS-PON control paths, OMCI/OAM, ONU-ID/OMCC/GEM/TCONT behaviour.
- LAN1 internal 1G mapping.
- LAN2 EN8811H at MDIO `0x0f`, `2500base-x`, including 1G compatibility and 2.5G operation.
- LAN3 RTL8261BE at MDIO `0x08`, USXGMII with host PCS `0x1fa04000` / PCIe PCS lane 1.
- LAN4 RTL8261BE at MDIO `0x05`, USXGMII with host PCS `0x1fa09000` / ETH PCS.
- PON-to-PPE/NPU/QDMA forwarding and hardware-offload counters.

## Current repair scope

Changes are allowed only to fix or expose known issues while keeping the baseline intact:

1. LAN2 EN8811H 1G/2.5G link and traffic.
2. LAN3/LAN4 RTL8261BE host-side USXGMII/PCS/phylink carrier and 10G traffic.
3. EN7572 PON support for GPON/XG-PON/XGS-PON, including OMCI/OAM and GEM/T-CONT control paths.
4. Functional PON LuCI backed by the real PON userspace/control stack.
5. NPU LuCI/diagnostics proving PPE/FOE/QDMA offload rather than merely firmware loading.
6. Linux 6.18 build reproducibility using the public tree only as a framework.

## Flash gate

A CI compile PASS is not a flash approval. Final images must first pass a regression bundle against the golden ITB: FIT/DTB, rootfs package/module set, firmware blobs, NAND/UBI layout, bootargs, LAN topology/PCS mapping, PON/EN7572 control stack, and NPU/PPE/QDMA configuration. After that, initramfs/TFTP runtime validation is required before any sysupgrade test.
