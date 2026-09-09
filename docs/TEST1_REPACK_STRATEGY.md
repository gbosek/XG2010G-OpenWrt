# XG2010G Test-1 safe repack strategy

## Why we are not replacing the whole kernel yet

The user's known-good XG2010G 6.18.44 image contains a newer PON-aware Ethernet/PPE ABI (`airoha_eth_pon_*`, `airoha_ppe_pon_lookup_tag`, `airoha,pon-data-path`) that is not yet found in normal public upstream source. Replacing the whole kernel with a public tree would risk breaking the currently working xPON/PPE stack.

Therefore Test-1 uses the known-good 6.18.44 image as the golden base and changes the smallest possible components required for the RTL8261BE host-side USXGMII fix.

## Test-1 plan

1. Build a replacement `realtek.ko` from a pinned Linux 6.18 XG2010G reference tree that carries patches 743 and 744.
2. Require vermagic `6.18.44 SMP mod_unload aarch64` before considering module transplantation.
3. Keep the original XG2010G kernel Image and original xPON/EN7572/NPU modules.
4. Patch only the XG2010G DTB nodes for the two RTL8261BE PHYs to opt into `realtek,patch-rtk-serdes`.
5. Preserve the golden board wiring:
   - MDIO 0x08 -> reset GPIO27 -> PCS 0x1fa04000
   - MDIO 0x05 -> reset GPIO29 -> PCS 0x1fa09000
6. Rebuild the original FIT/sysupgrade container with the patched DTB/rootfs while preserving sysupgrade metadata and XG2010G UBI layout.
7. Run structural validation and `sysupgrade -T` on-device before flashing.

## Explicitly not in Test-1

- no BL2/preloader change
- no FIP/U-Boot change
- no whole DSD/factory write
- no `wan_mode=2` change
- no XR1710G/XG-140G reset GPIO copied into XG2010G
- no polarity/sds-mode guessing in the same first test

## Acceptance

After flashing:

- both RTL8261BE copper sides negotiate 10G
- AN7581 PCS reports carrier
- `lan3` / `lan4` carrier becomes 1
- DHCP/bridge traffic passes
- repeated cold boots retain carrier
- iperf3 exceeds 1 Gbit/s and scales toward line rate
- PPE FOE BIND entries and hardware byte counters grow
- QDMA no_mapping/hw_dropped remain sane
- CPU softirq is not the primary datapath

The first candidate remains experimental until these checks pass on the actual XG2010G hardware.
