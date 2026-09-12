#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} <an7581-gemtek-xg2010g.dts>")

p = Path(sys.argv[1])
s = p.read_text()

# Keep the NAND/UBI geometry used by the uploaded known-working firmware.
try:
    a = s.index("&spi_nand {")
    b = s.index("&pcie0", a)
except ValueError as exc:
    raise SystemExit(f"DTS layout anchor not found: {exc}")

storage = r'''&spi_nand {
	partitions {
		compatible = "fixed-partitions";
		#address-cells = <1>;
		#size-cells = <1>;
		bl2@0 { label = "bl2"; reg = <0x00000000 0x00020000>; read-only; };
		ubi@20000 {
			label = "ubi"; reg = <0x00020000 0x00000000>; compatible = "linux,ubi";
			volumes {
				ubi-volume-factory { volname = "factory"; nvmem-layout { compatible = "fixed-layout"; #address-cells = <1>; #size-cells = <1>; macaddr_factory_3e: macaddr@3e { compatible = "mac-base"; reg = <0x3e 0x6>; #nvmem-cell-cells = <1>; }; pon_calibration: calibration@12000 { reg = <0x12000 0x200>; }; }; };
				ubi_fit: ubi-volume-fit { volname = "fit"; };
				ubi-volume-fip { volname = "fip"; };
				ubi_env: ubi-volume-ubootenv { volname = "ubootenv"; };
				ubi_env2: ubi-volume-ubootenv2 { volname = "ubootenv2"; };
			};
		};
	};
};
&ubi_env { nvmem-layout { compatible = "u-boot,env-redundant-bool-layout"; }; };
&ubi_env2 { nvmem-layout { compatible = "u-boot,env-redundant-bool-layout"; }; };

'''
s = s[:a] + storage + s[b:]

for old, new in (
    ("ethernet-phy@8 {", "rtl8261_8: ethernet-phy@8 {"),
    ("ethernet-phy@5 {", "rtl8261_5: ethernet-phy@5 {"),
):
    if new not in s:
        if old not in s:
            raise SystemExit(f"DTS PHY anchor missing: {old}")
        s = s.replace(old, new, 1)

marker = "/* Test-4B: topology reconstructed from the user's working base firmware DTB. */"
if marker in s:
    raise SystemExit("DTS already contains the Test-4B topology; reset the pinned framework before preparing it again")

s += r'''

/* Test-4B: topology reconstructed from the user's working base firmware DTB. */
&eth { status = "okay"; };
&gdm1 { status = "okay"; };
&gdm2 { status = "okay"; };

&usb_pcs { status = "okay"; };
&pcie_pcs { status = "okay"; };
&eth_pcs { status = "okay"; };

&gsw_port1 { status = "disabled"; };
&gsw_port2 { status = "disabled"; };
&gsw_port3 { status = "disabled"; };
&gsw_port4 { status = "okay"; label = "lan1"; };

/*
 * The Nokia framework enables board-specific LED pinmux on the internal PHYs.
 * The uploaded XG2010G golden DTB leaves those LED nodes disabled and carries
 * no PHY LED pinctrl properties.  Strip the foreign GPIO44/45/46 setup.
 */
&gsw_phy2 {
  status = "disabled";
  /delete-property/ pinctrl-names;
  /delete-property/ pinctrl-0;
};
&gsw_phy3 {
  status = "disabled";
  /delete-property/ pinctrl-names;
  /delete-property/ pinctrl-0;
};
&gsw_phy4 {
  status = "okay";
  /delete-property/ pinctrl-names;
  /delete-property/ pinctrl-0;
};
&gsw_phy2_led0 { status = "disabled"; };
&gsw_phy3_led0 { status = "disabled"; };
&gsw_phy4_led0 { status = "disabled"; };

/*
 * The framework's Nokia common DTS gives EN8811H GPIO31 reset wiring and an
 * LED child.  Neither exists in the user's golden XG2010G DTB.  Delete those
 * foreign board properties before investigating the real 1G/2.5G link path.
 */
&en8811 {
  /delete-property/ reset-gpios;
  /delete-property/ reset-assert-us;
  /delete-property/ reset-deassert-us;
  /delete-node/ leds;
};

&gdm4 {
  status = "okay";
  openwrt,netdev-name = "lan4";
  phy-handle = <&rtl8261_5>;
  phy-mode = "usxgmii";
  pcs-handle = <&eth_pcs>;
  /delete-property/ nvmem-cells;
  /delete-property/ nvmem-cell-names;
};

&eth {
  gdm3: ethernet@3 {
    compatible = "airoha,eth-mac";
    reg = <3>;
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    ethernet-port@4 {
      compatible = "airoha,eth-port";
      reg = <4>;
      status = "okay";
      openwrt,netdev-name = "lan2";
      phy-handle = <&en8811>;
      phy-mode = "2500base-x";
      pcs-handle = <&usb_pcs>;
    };

    ethernet-port@5 {
      compatible = "airoha,eth-port";
      reg = <5>;
      status = "okay";
      openwrt,netdev-name = "lan3";
      phy-handle = <&rtl8261_8>;
      phy-mode = "usxgmii";
      pcs-handle = <&pcie_pcs 1>;
    };
  };
};
'''

required = (
    'openwrt,netdev-name = "lan2"',
    'openwrt,netdev-name = "lan3"',
    'openwrt,netdev-name = "lan4"',
    'phy-mode = "2500base-x"',
    'pcs-handle = <&usb_pcs>',
    'pcs-handle = <&pcie_pcs 1>',
    'pcs-handle = <&eth_pcs>',
    '/delete-property/ reset-gpios;',
    '/delete-property/ pinctrl-names;',
    'ubi@20000',
    'calibration@12000',
)
for needle in required:
    if needle not in s:
        raise SystemExit(f"prepared DTS is missing required token: {needle}")

# The AN7581 multi-SerDes driver only instantiates GDM3/GDM4 child netdevs
# whose child nodes are explicitly compatible with "airoha,eth-port".
# Without these compatibles it silently falls back to a single parent GDM3
# netdev and lan2/lan3 disappear even though their DTS text exists.
if s.count('compatible = "airoha,eth-port";') < 2:
    raise SystemExit("prepared DTS is missing Airoha multi-SerDes eth-port compatibles")

p.write_text(s)
print(f"PASS: prepared {p}")
