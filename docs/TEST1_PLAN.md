# XG2010G Test-1 Build Plan

## Hardware baseline

- SoC: 7581PT / AN7581
- PON frontend: EN7572
- 10G LAN: RTL8261BE @ MDIO 0x08, PCS 0x1fa04000, reset GPIO 27
- 10G WAN/LAN: RTL8261BE @ MDIO 0x05, PCS 0x1fa09000, reset GPIO 29
- 2.5G: EN8811H @ MDIO 0x0f, 2500BASE-X, PCS 0x1fa07000

## PON

Preserve the modern XG2010G 6.18 data path:

EN7572 -> PON PCS -> airoha-xpon -> GEM/T-CONT service mapping -> GDM2 -> PPE/FOE -> QDMA/NPU.

Board calibration must be read from the XG2010G factory/DSD-compatible 512-byte calibration cell at offset 0x12000. Never overwrite a complete factory/DSD partition to import calibration.

## 10G Test-1

Keep XG2010G GPIO/MDIO/PCS mapping. Integrate the RTL8261 host-SerDes/flow_s repair corresponding to the identified 743/744 repair path. Do not blindly copy XR1710G polarity, reset GPIO or board DTS properties.

Acceptance: 10G copper negotiation + phylink carrier=1 + DHCP/bridge + iperf >1Gbps, then hardware-offload validation.

## NPU/PPE acceptance

A speed test alone is insufficient. Validate NPU firmware, HWNAT init, FOE BIND entries and byte counters, QDMA channel counters, XGEM counters and `qdma_tx_no_mapping` / hardware drops.
