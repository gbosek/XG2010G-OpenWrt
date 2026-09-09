# XG2010G OpenWrt / ImmortalWrt 6.18

专用于 Gemtek XG2010G（7581PT / AN7581）的 OpenWrt/ImmortalWrt 固件工程。

## Test-1 目标

- Linux 6.18
- 保留 XG2010G 已验证可工作的现代 xPON / EN7572 / OMCI/OAM 数据面
- 修复 RTL8261BE 10G USXGMII/PCS carrier 问题
- 验证 EN8811H 2.5G
- 保持并验证 NPU/PPE/QDMA/FOE 硬件卸载
- 生成可由 LuCI Web 升级的 `squashfs-sysupgrade.itb`

## 板级约束

本仓库唯一目标板是 **XG2010G / 7581PT**。XG-140G、XG-040G、XR1710G、W1700K 只能作为驱动/架构参考，禁止直接复制其分区、GPIO、boot chain、BOSA/DSD 校准或 DTS 板级参数。

第一版保持当前 XG2010G 已工作基线的 NPU `wan_mode = QDMA_WAN_ETHER (1)`，未经实机证据不改成参考机的 `PON_XDSL (2)`。
