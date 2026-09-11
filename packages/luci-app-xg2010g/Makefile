include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI support for Gemtek XG2010G PON/NPU management
LUCI_DEPENDS:=+luci-base +rpcd +mwan3 +luci-app-mwan3 +airoha-ponctl +airoha-omcid +airoha-oamd +airoha-pon-debug
LUCI_PKGARCH:=all
PKG_LICENSE:=Apache-2.0

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
