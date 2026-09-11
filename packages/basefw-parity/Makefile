include $(TOPDIR)/rules.mk

PKG_NAME:=xg2010g-basefw-parity
PKG_VERSION:=1.0
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/airoha-ponctl
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha PON control utility from XG2010G base firmware
  DEPENDS:=+kmod-airoha-xpon
endef

define Package/airoha-omcid
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha OMCI daemon from XG2010G base firmware
  DEPENDS:=+kmod-airoha-xpon
endef

define Package/airoha-oamd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha OAM daemon from XG2010G base firmware
  DEPENDS:=+kmod-airoha-xpon
endef

define Package/airoha-pon-debug
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha PON diagnostics from XG2010G base firmware
  DEPENDS:=+airoha-ponctl +airoha-omcid +airoha-oamd +ip-bridge +ip-full +tcpdump
endef

define Package/luci-app-pon
  SECTION:=luci
  CATEGORY:=LuCI
  SUBMENU:=3. Applications
  TITLE:=LuCI PON application from XG2010G base firmware
  DEPENDS:=+luci-base +airoha-ponctl +airoha-omcid +airoha-oamd +airoha-pon-debug +mtd +ubi-utils
endef

define Package/rtl826x-firmware
  SECTION:=firmware
  CATEGORY:=Firmware
  TITLE:=Realtek RTL826x firmware from XG2010G base firmware
  DEPENDS:=+kmod-phy-realtek
endef

define Package/airoha-ponctl/conffiles
/etc/config/pon
endef

define Package/airoha-ponctl/install
	$(INSTALL_DIR) $(1)/etc/config $(1)/etc/init.d $(1)/usr/sbin
	$(INSTALL_CONF) ./files/etc/config/pon $(1)/etc/config/pon
	$(INSTALL_BIN) ./files/etc/init.d/pon $(1)/etc/init.d/pon
	base64 -d ./blobs/ponctl.b64 > $(1)/usr/sbin/ponctl
	chmod 0755 $(1)/usr/sbin/ponctl
endef

define Package/airoha-omcid/install
	$(INSTALL_DIR) $(1)/etc/init.d $(1)/usr/bin $(1)/usr/sbin
	$(INSTALL_BIN) ./files/etc/init.d/airoha-omcid $(1)/etc/init.d/airoha-omcid
	base64 -d ./blobs/airoha-omcid.b64 > $(1)/usr/sbin/airoha-omcid
	chmod 0755 $(1)/usr/sbin/airoha-omcid
	ln -sf /usr/sbin/airoha-omcid $(1)/usr/bin/omcictl
endef

define Package/airoha-oamd/install
	$(INSTALL_DIR) $(1)/etc/init.d $(1)/usr/bin $(1)/usr/sbin
	$(INSTALL_BIN) ./files/etc/init.d/airoha-oamd $(1)/etc/init.d/airoha-oamd
	base64 -d ./blobs/airoha-oamd.b64 > $(1)/usr/sbin/airoha-oamd
	chmod 0755 $(1)/usr/sbin/airoha-oamd
	ln -sf /usr/sbin/airoha-oamd $(1)/usr/bin/oamctl
endef

define Package/airoha-pon-debug/install
	$(INSTALL_DIR) $(1)/etc/config $(1)/etc/init.d $(1)/usr/libexec $(1)/usr/sbin
	$(INSTALL_CONF) ./files/etc/config/airoha-pon-debug $(1)/etc/config/airoha-pon-debug
	$(INSTALL_BIN) ./files/etc/init.d/airoha-pon-debug $(1)/etc/init.d/airoha-pon-debug
	$(INSTALL_BIN) ./files/usr/libexec/airoha-pon-debug $(1)/usr/libexec/airoha-pon-debug
	$(INSTALL_BIN) ./files/usr/sbin/pon-debug $(1)/usr/sbin/pon-debug
endef

define Package/luci-app-pon/install
	$(INSTALL_DIR) $(1)/usr/libexec $(1)/usr/share/luci/menu.d $(1)/usr/share/rpcd/acl.d $(1)/www/luci-static/resources/view/pon
	$(INSTALL_BIN) ./files/usr/libexec/airoha-write-pon-data $(1)/usr/libexec/airoha-write-pon-data
	$(INSTALL_DATA) ./files/usr/share/luci/menu.d/luci-app-pon.json $(1)/usr/share/luci/menu.d/luci-app-pon.json
	$(INSTALL_DATA) ./files/usr/share/rpcd/acl.d/luci-app-pon.json $(1)/usr/share/rpcd/acl.d/luci-app-pon.json
	$(INSTALL_DATA) ./files/www/luci-static/resources/view/pon/config.js $(1)/www/luci-static/resources/view/pon/config.js
	$(INSTALL_DATA) ./files/www/luci-static/resources/view/pon/diagnostics.js $(1)/www/luci-static/resources/view/pon/diagnostics.js
	$(INSTALL_DATA) ./files/www/luci-static/resources/view/pon/hardware.js $(1)/www/luci-static/resources/view/pon/hardware.js
	$(INSTALL_DATA) ./files/www/luci-static/resources/view/pon/status.js $(1)/www/luci-static/resources/view/pon/status.js
endef

define Package/rtl826x-firmware/install
	$(INSTALL_DIR) $(1)/lib/firmware
	base64 -d ./blobs/rtl8261n.bin.b64 > $(1)/lib/firmware/rtl8261n.bin
	base64 -d ./blobs/rtl8264b.bin.b64 > $(1)/lib/firmware/rtl8264b.bin
	chmod 0644 $(1)/lib/firmware/rtl8261n.bin $(1)/lib/firmware/rtl8264b.bin
endef

$(eval $(call BuildPackage,airoha-ponctl))
$(eval $(call BuildPackage,airoha-omcid))
$(eval $(call BuildPackage,airoha-oamd))
$(eval $(call BuildPackage,airoha-pon-debug))
$(eval $(call BuildPackage,luci-app-pon))
$(eval $(call BuildPackage,rtl826x-firmware))
