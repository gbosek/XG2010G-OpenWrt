include $(TOPDIR)/rules.mk

PKG_NAME:=xg2010g-basefw-parity
PKG_VERSION:=1.0
PKG_RELEASE:=2
PKG_LICENSE:=Proprietary

include $(INCLUDE_DIR)/package.mk

define Package/airoha-ponctl
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G PON control utility from base firmware
  DEPENDS:=+libgcc +kmod-airoha-xpon
endef

define Package/airoha-ponctl/conffiles
/etc/config/pon
endef

define Package/airoha-omcid
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G OMCI daemon from base firmware
  DEPENDS:=+libgcc +airoha-ponctl +kmod-airoha-xpon +ip-full
endef

define Package/airoha-oamd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G EPON OAM daemon from base firmware
  DEPENDS:=+libgcc +airoha-ponctl +kmod-airoha-xpon +ip-full
endef

define Package/airoha-pon-debug
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G PON diagnostics from base firmware
  DEPENDS:=+airoha-ponctl +airoha-omcid +airoha-oamd +ip-bridge +ip-full +tcpdump
endef

define Package/airoha-pon-debug/conffiles
/etc/config/airoha-pon-debug
endef

define Package/luci-app-pon
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=3. Applications
  TITLE:=LuCI support for Airoha XG2010G PON
  DEPENDS:=+luci-base +airoha-ponctl +airoha-omcid +airoha-oamd +airoha-pon-debug +rpcd +mtd +ubi-utils
  PKGARCH:=all
endef

define Package/rtl826x-firmware
  SECTION:=firmware
  CATEGORY:=Firmware
  TITLE:=Realtek RTL8261N/RTL8264B firmware from XG2010G base firmware
  DEPENDS:=+kmod-phy-realtek
endef

# Binary payloads are byte-for-byte extracts from the user's uploaded working
# XG2010G image. They are kept as xz+base64 text.  The wildcard form permits
# the large PON binaries to be committed as ordered .partNN fragments without
# changing this Makefile.
define Build/Prepare
	$(call Build/Prepare/Default)
	mkdir -p $(PKG_BUILD_DIR)/root
	test -n "$(wildcard $(CURDIR)/blobs/ponctl.xz.b64*)"
	test -n "$(wildcard $(CURDIR)/blobs/airoha-oamd.xz.b64*)"
	test -n "$(wildcard $(CURDIR)/blobs/airoha-omcid.xz.b64*)"
	test -f $(CURDIR)/blobs/rtl8261n.bin.xz.b64
	test -f $(CURDIR)/blobs/rtl8264b.bin.xz.b64
	test -f $(CURDIR)/blobs/small-assets.tar.gz.b64
	cat $(sort $(wildcard $(CURDIR)/blobs/ponctl.xz.b64*)) | base64 -d | xz -dc > $(PKG_BUILD_DIR)/ponctl
	cat $(sort $(wildcard $(CURDIR)/blobs/airoha-oamd.xz.b64*)) | base64 -d | xz -dc > $(PKG_BUILD_DIR)/airoha-oamd
	cat $(sort $(wildcard $(CURDIR)/blobs/airoha-omcid.xz.b64*)) | base64 -d | xz -dc > $(PKG_BUILD_DIR)/airoha-omcid
	base64 -d $(CURDIR)/blobs/rtl8261n.bin.xz.b64 | xz -dc > $(PKG_BUILD_DIR)/rtl8261n.bin
	base64 -d $(CURDIR)/blobs/rtl8264b.bin.xz.b64 | xz -dc > $(PKG_BUILD_DIR)/rtl8264b.bin
	base64 -d $(CURDIR)/blobs/small-assets.tar.gz.b64 | tar -xzf - -C $(PKG_BUILD_DIR)/root
	chmod 0755 $(PKG_BUILD_DIR)/ponctl $(PKG_BUILD_DIR)/airoha-oamd $(PKG_BUILD_DIR)/airoha-omcid
endef

define Build/Compile
endef

define Package/airoha-ponctl/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/etc/config $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/ponctl $(1)/usr/sbin/ponctl
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/root/etc/config/pon $(1)/etc/config/pon
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/etc/init.d/pon $(1)/etc/init.d/pon
endef

define Package/airoha-omcid/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/airoha-omcid $(1)/usr/sbin/airoha-omcid
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/etc/init.d/airoha-omcid $(1)/etc/init.d/airoha-omcid
	ln -sf /usr/sbin/airoha-omcid $(1)/usr/bin/omcictl
endef

define Package/airoha-oamd/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/airoha-oamd $(1)/usr/sbin/airoha-oamd
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/etc/init.d/airoha-oamd $(1)/etc/init.d/airoha-oamd
	ln -sf /usr/sbin/airoha-oamd $(1)/usr/bin/oamctl
endef

define Package/airoha-pon-debug/install
	$(INSTALL_DIR) $(1)/etc/config $(1)/etc/init.d $(1)/usr/libexec $(1)/usr/sbin
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/root/etc/config/airoha-pon-debug $(1)/etc/config/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/etc/init.d/airoha-pon-debug $(1)/etc/init.d/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/usr/libexec/airoha-pon-debug $(1)/usr/libexec/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/usr/sbin/pon-debug $(1)/usr/sbin/pon-debug
endef

define Package/luci-app-pon/install
	$(INSTALL_DIR) $(1)/usr/libexec $(1)/usr/share/luci/menu.d $(1)/usr/share/rpcd/acl.d $(1)/www/luci-static/resources/view/pon
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/root/usr/libexec/airoha-write-pon-data $(1)/usr/libexec/airoha-write-pon-data
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/usr/share/luci/menu.d/luci-app-pon.json $(1)/usr/share/luci/menu.d/luci-app-pon.json
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/usr/share/rpcd/acl.d/luci-app-pon.json $(1)/usr/share/rpcd/acl.d/luci-app-pon.json
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/www/luci-static/resources/view/pon/config.js $(1)/www/luci-static/resources/view/pon/config.js
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/www/luci-static/resources/view/pon/diagnostics.js $(1)/www/luci-static/resources/view/pon/diagnostics.js
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/www/luci-static/resources/view/pon/hardware.js $(1)/www/luci-static/resources/view/pon/hardware.js
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/root/www/luci-static/resources/view/pon/status.js $(1)/www/luci-static/resources/view/pon/status.js
endef

define Package/rtl826x-firmware/install
	$(INSTALL_DIR) $(1)/lib/firmware
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/rtl8261n.bin $(1)/lib/firmware/rtl8261n.bin
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/rtl8264b.bin $(1)/lib/firmware/rtl8264b.bin
endef

$(eval $(call BuildPackage,airoha-ponctl))
$(eval $(call BuildPackage,airoha-omcid))
$(eval $(call BuildPackage,airoha-oamd))
$(eval $(call BuildPackage,airoha-pon-debug))
$(eval $(call BuildPackage,luci-app-pon))
$(eval $(call BuildPackage,rtl826x-firmware))
