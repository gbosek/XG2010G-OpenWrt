#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 6:
    raise SystemExit(
        f"usage: {sys.argv[0]} <xmcs_gpon.c> <xmcs_fdet.c> <xmcs_if.c> <xmcs_mci.c> <xmcs_phy.c>"
    )

gpon, fdet, ifc, mci, phy = map(Path, sys.argv[1:])


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one {label}, found {count}")
    path.write_text(text.replace(old, new, 1))


replace_once(fdet, "#if 0\nint fdet_cmd_proc", "int fdet_cmd_proc", "fdet #if 0")
replace_once(
    fdet,
    "#endif\n\nint fdet_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n",
    "",
    "fdet stub",
)

replace_once(gpon, "#if 0\nint gpon_10g_cmd_proc", "int gpon_10g_cmd_proc", "GPON #if 0")
gpon_tail = (
    "#endif\n\n"
    "int gpon_10g_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n\n"
    "int gpon_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n\n"
    "int rdkb_10g_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n"
)
replace_once(gpon, gpon_tail, "", "GPON ioctl stubs")

replace_once(ifc, "#if 0\nint if_cmd_proc", "int if_cmd_proc", "interface #if 0")
replace_once(
    ifc,
    "#endif\n\nint if_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n",
    "",
    "interface stub",
)

replace_once(phy, "#if 0\nint phy_cmd_proc", "int phy_cmd_proc", "PHY #if 0")
replace_once(
    phy,
    "#endif\n\nint phy_cmd_proc(uint cmd, ulong arg)\n{\n\treturn -EOPNOTSUPP;\n}\n",
    "",
    "PHY stub",
)

replace_once(mci, "#if 0\nlong pon_mci_ioctl", "long pon_mci_ioctl", "MCI #if 0")
mci_stub = (
    "#endif\n\n"
    "long pon_mci_ioctl(struct file *filp, uint cmd, ulong arg)\n{\n"
    "\tif (_IOC_TYPE(cmd) == EPON_MAGIC)\n"
    "\t\treturn epon_cmd_proc(cmd, arg);\n\n"
    "\treturn -ENOTTY;\n}\n"
)
replace_once(mci, mci_stub, "", "MCI EPON-only stub")

checks = {
    gpon: ["int gpon_10g_cmd_proc", "int gpon_cmd_proc", "int rdkb_10g_cmd_proc"],
    fdet: ["int fdet_cmd_proc"],
    ifc: ["int if_cmd_proc"],
    mci: ["long pon_mci_ioctl"],
    phy: ["int phy_cmd_proc"],
}
for path, symbols in checks.items():
    text = path.read_text()
    for symbol in symbols:
        count = text.count(symbol)
        if count != 1:
            raise SystemExit(f"{path}: {symbol} count is {count}, expected 1")

print("PASS: restored original GPON/XG-PON/XGS-PON/IF/PHY ioctl handlers")
