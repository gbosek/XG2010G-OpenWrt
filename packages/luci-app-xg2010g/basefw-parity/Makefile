include $(TOPDIR)/rules.mk

PKG_NAME:=xg2010g-basefw-pon
PKG_VERSION:=1.0
PKG_RELEASE:=5
PKG_LICENSE:=Proprietary

# The complete payload is kept in the private outer repository next to src/
# during GitHub Actions builds. Test-4B copies this package definition into
# src/package while keeping the proprietary payload outside the OpenWrt tree.
BASEFW_REPO_DIR:=$(TOPDIR)/../packages/basefw-parity
PAYLOAD_FILE:=$(BASEFW_REPO_DIR)/xg2010g-parity-v2.tar.xz

include $(INCLUDE_DIR)/package.mk

define Package/airoha-ponctl
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G PON control utility from uploaded base firmware
  DEPENDS:=+libgcc +kmod-airoha-xpon
endef

define Package/airoha-ponctl/conffiles
/etc/config/pon
endef

define Package/airoha-omcid
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G OMCI daemon from uploaded base firmware
  DEPENDS:=+libgcc +airoha-ponctl +kmod-airoha-xpon +ip-full
endef

define Package/airoha-oamd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G EPON OAM daemon from uploaded base firmware
  DEPENDS:=+libgcc +airoha-ponctl +kmod-airoha-xpon +ip-full
endef

define Package/airoha-pon-debug
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Airoha XG2010G PON diagnostics from uploaded base firmware
  DEPENDS:=+airoha-ponctl +airoha-omcid +airoha-oamd +ip-bridge +ip-full +tcpdump
endef

define Package/airoha-pon-debug/conffiles
/etc/config/airoha-pon-debug
endef

define Build/Prepare
	$(call Build/Prepare/Default)
	test -s $(PAYLOAD_FILE)
	cp $(PAYLOAD_FILE) $(PKG_BUILD_DIR)/payload.tar.xz
	echo '5d8a87780fbec056c21709ec86520faef93057dbfc9d7a7aeb0ed783542c94f4  $(PKG_BUILD_DIR)/payload.tar.xz' | sha256sum -c -
	tar -xJf $(PKG_BUILD_DIR)/payload.tar.xz -C $(PKG_BUILD_DIR)
	# Byte-for-byte checks against the uploaded firmware extraction.
	echo '3bd8b7e264f6738de7eff66afa44068a9684fb0dd559b950ad702a2e59f7b01c  $(PKG_BUILD_DIR)/usr/sbin/ponctl' | sha256sum -c -
	echo 'aee701662d3c25f98c37eb91c600836e1cff1263f0664572eb83d3060f392429  $(PKG_BUILD_DIR)/usr/sbin/airoha-oamd' | sha256sum -c -
	echo '6e361fc1be99f64185b62b7e93fde1462d392309774a36af59dd4b1248850b63  $(PKG_BUILD_DIR)/usr/sbin/airoha-omcid' | sha256sum -c -
	echo 'ae1963b2a84a17eaa2fb9052591bdb5152838feda045d7313f45a8608b918533  $(PKG_BUILD_DIR)/lib/firmware/rtl8261n.bin' | sha256sum -c -
	echo '7a0bcf605739d6f780e0799bbea0c73acf56c9a4cbba015da5d27589bf4352ca  $(PKG_BUILD_DIR)/lib/firmware/rtl8264b.bin' | sha256sum -c -
endef

define Build/Compile
endef

# These ELF files are extracted byte-for-byte from the uploaded working
# XG2010G firmware.  Do not use INSTALL_BIN for them: INSTALL_BIN invokes the
# target strip tool, while these already-built proprietary binaries may not
# carry a section layout that the current toolchain can strip safely.
define Package/airoha-ponctl/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/etc/config $(1)/etc/init.d
	$(CP) $(PKG_BUILD_DIR)/usr/sbin/ponctl $(1)/usr/sbin/ponctl
	chmod 0755 $(1)/usr/sbin/ponctl
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/etc/config/pon $(1)/etc/config/pon
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/pon $(1)/etc/init.d/pon
endef

define Package/airoha-omcid/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/usr/bin $(1)/etc/init.d
	$(CP) $(PKG_BUILD_DIR)/usr/sbin/airoha-omcid $(1)/usr/sbin/airoha-omcid
	chmod 0755 $(1)/usr/sbin/airoha-omcid
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/airoha-omcid $(1)/etc/init.d/airoha-omcid
	ln -sf /usr/sbin/airoha-omcid $(1)/usr/bin/omcictl
endef

define Package/airoha-oamd/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/usr/bin $(1)/etc/init.d
	$(CP) $(PKG_BUILD_DIR)/usr/sbin/airoha-oamd $(1)/usr/sbin/airoha-oamd
	chmod 0755 $(1)/usr/sbin/airoha-oamd
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/airoha-oamd $(1)/etc/init.d/airoha-oamd
	ln -sf /usr/sbin/airoha-oamd $(1)/usr/bin/oamctl
endef

define Package/airoha-pon-debug/install
	$(INSTALL_DIR) $(1)/etc/config $(1)/etc/init.d $(1)/usr/libexec $(1)/usr/sbin
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/etc/config/airoha-pon-debug $(1)/etc/config/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/etc/init.d/airoha-pon-debug $(1)/etc/init.d/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/usr/libexec/airoha-pon-debug $(1)/usr/libexec/airoha-pon-debug
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/usr/sbin/pon-debug $(1)/usr/sbin/pon-debug
endef

$(eval $(call BuildPackage,airoha-ponctl))
$(eval $(call BuildPackage,airoha-omcid))
$(eval $(call BuildPackage,airoha-oamd))
$(eval $(call BuildPackage,airoha-pon-debug))
