#!/usr/bin/env python3
"""Verify a built XG2010G DTB against facts extracted from the user's golden ITB.

This intentionally parses the binary FDT itself so a textual DTS grep cannot
pass while phy-handle/pcs-handle point at the wrong nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

FDT_BEGIN_NODE = 1
FDT_END_NODE = 2
FDT_PROP = 3
FDT_NOP = 4
FDT_END = 9


def parse_fdt(buf: bytes):
    if len(buf) < 40:
        raise ValueError("file is too small to be a DTB")
    (magic, totalsize, off_struct, off_strings, _off_rsvmap, version,
     _last_comp, _boot_cpuid, size_strings, size_struct) = struct.unpack(">10I", buf[:40])
    if magic != 0xD00DFEED:
        raise ValueError(f"bad FDT magic 0x{magic:08x}")
    if totalsize > len(buf):
        raise ValueError(f"FDT totalsize {totalsize} exceeds file size {len(buf)}")
    if version < 16:
        raise ValueError(f"unsupported FDT version {version}")

    strings = buf[off_strings:off_strings + size_strings]

    def string_at(offset: int) -> str:
        end = strings.index(b"\0", offset)
        return strings[offset:end].decode()

    pos = off_struct
    end = off_struct + size_struct
    stack: list[str] = []
    nodes: dict[str, dict[str, bytes]] = {}

    while pos < end:
        token = struct.unpack(">I", buf[pos:pos + 4])[0]
        pos += 4
        if token == FDT_BEGIN_NODE:
            nul = buf.index(b"\0", pos)
            name = buf[pos:nul].decode(errors="replace")
            pos = (nul + 1 + 3) & ~3
            stack.append(name)
            path = "/" + "/".join(x for x in stack if x)
            nodes.setdefault(path, {})
        elif token == FDT_END_NODE:
            stack.pop()
        elif token == FDT_PROP:
            length, nameoff = struct.unpack(">II", buf[pos:pos + 8])
            pos += 8
            value = buf[pos:pos + length]
            pos = (pos + length + 3) & ~3
            path = "/" + "/".join(x for x in stack if x)
            nodes.setdefault(path, {})[string_at(nameoff)] = value
        elif token == FDT_NOP:
            continue
        elif token == FDT_END:
            break
        else:
            raise ValueError(f"invalid FDT token {token} at 0x{pos - 4:x}")

    phandles: dict[int, str] = {}
    for path, props in nodes.items():
        for key in ("phandle", "linux,phandle"):
            value = props.get(key)
            if value is not None and len(value) == 4:
                phandles[struct.unpack(">I", value)[0]] = path
    return nodes, phandles


def strings(props, key):
    value = props.get(key)
    if value is None:
        return []
    return [x.decode(errors="replace") for x in value.rstrip(b"\0").split(b"\0")]


def one_string(props, key):
    values = strings(props, key)
    return values[0] if values else None


def cells(props, key):
    value = props.get(key)
    if value is None:
        return None
    if len(value) % 4:
        raise ValueError(f"property {key} is not cell-aligned")
    return list(struct.unpack(">" + "I" * (len(value) // 4), value))


def basename(path):
    return path.rsplit("/", 1)[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dtb", type=Path)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "configs/golden-xg2010g-dtb-manifest.json")
    parser.add_argument("--profile", choices=("candidate", "golden"), default="candidate")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    raw = args.dtb.read_bytes()
    nodes, phandles = parse_fdt(raw)
    failures: list[str] = []

    def fail(message):
        failures.append(message)

    def expect(condition, message):
        if not condition:
            fail(message)

    def find_by_prop(key, value):
        matches = []
        for path, props in nodes.items():
            if value in strings(props, key):
                matches.append((path, props))
        return matches

    def unique_by_prop(key, value):
        matches = find_by_prop(key, value)
        if len(matches) != 1:
            fail(f"expected exactly one node with {key}={value!r}, found {len(matches)}")
            return None, None
        return matches[0]

    def resolve_handle(props, key):
        value = cells(props, key)
        if not value:
            fail(f"missing/empty {key}")
            return None, []
        path = phandles.get(value[0])
        if path is None:
            fail(f"{key} phandle 0x{value[0]:x} does not resolve")
            return None, value[1:]
        return path, value[1:]

    if args.profile == "golden":
        expect(len(raw) == manifest["source"]["fdt_size"],
               f"golden FDT size changed: {len(raw)}")
        digest = hashlib.sha256(raw).hexdigest()
        expect(digest == manifest["source"]["fdt_sha256"],
               f"golden FDT SHA256 mismatch: {digest}")

    root = nodes.get("/", {})
    expect(one_string(root, "model") == "Gemtek XG2010G", "model is not Gemtek XG2010G")
    root_compat = strings(root, "compatible")
    for comp in ("gemtek,xg2010g", "airoha,an7581", "airoha,en7581"):
        expect(comp in root_compat, f"root compatible missing {comp}")

    # LAN topology: resolve every PHY/PCS phandle, not just names in decompiled text.
    for ifname in ("lan2", "lan3", "lan4"):
        expected = manifest["ports"][ifname]
        path, props = unique_by_prop("openwrt,netdev-name", ifname)
        if props is None:
            continue
        expect(expected["kind"] in strings(props, "compatible"),
               f"{ifname}: compatible must contain {expected['kind']}")
        expect(cells(props, "reg") == [expected["reg"]],
               f"{ifname}: reg mismatch: {cells(props, 'reg')}")
        expect(one_string(props, "phy-mode") == expected["phy_mode"],
               f"{ifname}: phy-mode mismatch: {one_string(props, 'phy-mode')}")

        phy_path, phy_args = resolve_handle(props, "phy-handle")
        if phy_path:
            expect(basename(phy_path) == expected["phy_node"],
                   f"{ifname}: phy-handle resolves to {phy_path}, expected {expected['phy_node']}")
            expect(phy_args == [], f"{ifname}: unexpected phy-handle args {phy_args}")
            expect(cells(nodes[phy_path], "reg") == [expected["phy_reg"]],
                   f"{ifname}: PHY reg mismatch")

        pcs_path, pcs_args = resolve_handle(props, "pcs-handle")
        if pcs_path:
            expect(basename(pcs_path) == expected["pcs_node"],
                   f"{ifname}: pcs-handle resolves to {pcs_path}, expected {expected['pcs_node']}")
            expected_args = [] if expected["pcs_lane"] is None else [expected["pcs_lane"]]
            expect(pcs_args == expected_args,
                   f"{ifname}: PCS args {pcs_args}, expected {expected_args}")

    # Internal 1G port remains the switch port labelled lan1.
    lan1_matches = find_by_prop("label", "lan1")
    expect(len(lan1_matches) == 1, f"expected one lan1 switch label, found {len(lan1_matches)}")
    if len(lan1_matches) == 1:
        _path, props = lan1_matches[0]
        expect(cells(props, "reg") == [4], "lan1 switch port reg must be 4")
        expect(one_string(props, "phy-mode") == "internal", "lan1 phy-mode must be internal")

    # Verify exact PHY facts from the uploaded golden DTB.
    phy_nodes = {}
    for node_name, expected in manifest["phys"].items():
        matches = [(p, pr) for p, pr in nodes.items() if basename(p) == node_name]
        expect(len(matches) == 1, f"expected one {node_name}, found {len(matches)}")
        if len(matches) != 1:
            continue
        path, props = matches[0]
        phy_nodes[node_name] = (path, props)
        expect(expected["compatible"] in strings(props, "compatible"),
               f"{node_name}: compatible mismatch {strings(props, 'compatible')}")
        expect(cells(props, "reg") == [expected["reg"]], f"{node_name}: reg mismatch")

        if expected.get("reset_gpios", "present") is None:
            for key in manifest["candidate_only_requirements"]["en8811_forbidden_inherited_properties"]:
                expect(key not in props,
                       f"{node_name}: foreign framework property {key} must not survive")
        elif "reset_gpio_pin" in expected:
            reset = cells(props, "reset-gpios")
            expect(reset is not None and len(reset) == 3,
                   f"{node_name}: reset-gpios must contain controller,pin,flags")
            if reset and len(reset) == 3:
                controller = phandles.get(reset[0], "")
                expect("pinctrl@" in controller,
                       f"{node_name}: reset controller {controller!r} is not Airoha pinctrl")
                expect(reset[1] == expected["reset_gpio_pin"],
                       f"{node_name}: reset pin {reset[1]}, expected {expected['reset_gpio_pin']}")
                expect(reset[2] == expected["reset_gpio_flags"],
                       f"{node_name}: reset flags {reset[2]}, expected active-low flag {expected['reset_gpio_flags']}")
            expect(cells(props, "reset-assert-us") == [expected["reset_assert_us"]],
                   f"{node_name}: reset-assert-us mismatch")
            expect(cells(props, "reset-deassert-us") == [expected["reset_deassert_us"]],
                   f"{node_name}: reset-deassert-us mismatch")

            if args.profile == "candidate":
                required = manifest["candidate_only_requirements"]["rtl8261_required_property"]
                expect(required in props, f"{node_name}: missing {required}")
                for key in manifest["candidate_only_requirements"]["rtl8261_forbidden_properties_for_first_test"]:
                    expect(key not in props,
                           f"{node_name}: {key} must not be copied from XR1710G in first test")

    # PCS nodes and enable state.
    for node_name, expected in manifest["pcs"].items():
        matches = [(p, pr) for p, pr in nodes.items() if basename(p) == node_name]
        expect(len(matches) == 1, f"expected one {node_name}, found {len(matches)}")
        if len(matches) == 1:
            _path, props = matches[0]
            expect(expected["compatible"] in strings(props, "compatible"), f"{node_name}: compatible mismatch")
            expect(one_string(props, "status") == expected["status"], f"{node_name}: status is not okay")
            expect(cells(props, "#pcs-cells") == [expected["pcs_cells"]], f"{node_name}: #pcs-cells mismatch")

    # PON MAC -> PON PCS, GDM2 datapath, EN7572 and calibration.
    pon = manifest["pon"]
    xpon_path, xpon = unique_by_prop("compatible", pon["xpon_mac_compatible"])
    if xpon is not None:
        reg = cells(xpon, "reg") or []
        expect(len(reg) >= 2 and reg[1] == pon["xpon_mac_reg"], f"xPON MAC base mismatch: {reg}")
        pcs_path, pcs_args = resolve_handle(xpon, "pcs-handle")
        if pcs_path:
            expect(basename(pcs_path) == pon["pon_pcs_node"], "xPON MAC is not bound to PON PCS")
            expect(pcs_args == [], "PON PCS must not have lane args")

    en_path, en7572 = unique_by_prop("compatible", pon["en7572_compatible"])
    if en7572 is not None:
        expect(cells(en7572, "reg") == [pon["en7572_i2c_reg"]], "EN7572 I2C address mismatch")
        txdis = cells(en7572, "tx-disable-gpios")
        expect(txdis is not None and len(txdis) == 3 and txdis[1] == pon["en7572_tx_disable_gpio_pin"],
               f"EN7572 TX_DISABLE GPIO mismatch: {txdis}")
        expect(one_string(en7572, "nvmem-cell-names") == "calibration", "EN7572 calibration nvmem binding missing")

    gdm2_matches = [(p, pr) for p, pr in nodes.items()
                    if cells(pr, "reg") == [pon["gdm2_reg"]] and "airoha,pon-data-path" in pr]
    expect(len(gdm2_matches) == 1, f"expected one GDM2 PON datapath node, found {len(gdm2_matches)}")
    if len(gdm2_matches) == 1:
        pcs_path, pcs_args = resolve_handle(gdm2_matches[0][1], "pcs-handle")
        if pcs_path:
            expect(basename(pcs_path) == pon["pon_pcs_node"], "GDM2 is not bound to PON PCS")
            expect(pcs_args == [], "GDM2 PON PCS must not have lane args")

    cal_matches = [(p, pr) for p, pr in nodes.items()
                   if basename(p) == "calibration@12000" and cells(pr, "reg") == [pon["calibration_offset"], pon["calibration_size"]]]
    expect(len(cal_matches) == 1, "factory calibration@12000 0x200 cell missing")

    # Ethernet/NPU/QDMA reserved memory facts from the golden DTB.
    for section in ("ethernet", "npu"):
        expected = manifest[section]
        path, props = unique_by_prop("compatible", expected["compatible"])
        if props is not None:
            reg = cells(props, "reg") or []
            expect(len(reg) >= 2 and reg[1] == expected["reg"], f"{section}: base address mismatch {reg}")
            expect(one_string(props, "status") == expected["status"], f"{section}: status is not okay")

    reserved = {
        "npu-binary@84000000": (manifest["npu"]["reserved_npu_base"], manifest["npu"]["reserved_npu_size"]),
        "qdma0-buf@87000000": (manifest["npu"]["qdma0_base"], manifest["npu"]["qdma0_size"]),
        "qdma1-buf@89000000": (manifest["npu"]["qdma1_base"], manifest["npu"]["qdma1_size"]),
    }
    for name, (base, size) in reserved.items():
        matches = [(p, pr) for p, pr in nodes.items() if basename(p) == name]
        expect(len(matches) == 1, f"reserved-memory node {name} missing")
        if len(matches) == 1:
            reg = cells(matches[0][1], "reg") or []
            expect(reg == [0, base, 0, size], f"{name}: reg mismatch {reg}")

    # UBI begins at 0x20000 and extends to the end exactly as in the golden DTB.
    ubi_matches = []
    for path, props in nodes.items():
        if "linux,ubi" in strings(props, "compatible") and cells(props, "reg") == [manifest["storage"]["ubi_offset"], 0]:
            ubi_matches.append((path, props))
    expect(len(ubi_matches) == 1, f"expected one linux,ubi partition at 0x20000, found {len(ubi_matches)}")

    if failures:
        print("FAIL: XG2010G DTB diverges from golden board facts:")
        for item in failures:
            print(f"  - {item}")
        raise SystemExit(1)

    print(f"PASS: {args.profile} DTB matches XG2010G golden board facts")
    print(f"DTB: {args.dtb} ({len(raw)} bytes, sha256={hashlib.sha256(raw).hexdigest()})")


if __name__ == "__main__":
    main()
