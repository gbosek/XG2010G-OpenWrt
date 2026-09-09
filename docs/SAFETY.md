# Flashing safety

Test builds generate sysupgrade/recovery images only. Do not modify or flash BL2/preloader or FIP/U-Boot unless a later boot-chain change is explicitly required and independently reviewed.

Preserve device-unique DSD/factory/PON identity, certificates, MAC addresses and EN7572 optical calibration.

Before LuCI flashing, validate the generated image with `sysupgrade -T` on the target firmware. Initial Test-1 validation should preferably use a clean configuration so stale network/firewall/PON settings do not hide driver behavior.
