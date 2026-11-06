#!/bin/sh
set -eu
LAB=/mnt/SDCARD/Persistent/thps4-lab
BASE="$LAB/route-research"
WINE=/tmp/thps4-wine
WP=/tmp/thps4-weston
export LD_LIBRARY_PATH="$BASE/armhf-glibc/usr/lib/arm-linux-gnueabihf:$BASE/armhf-deps/lib/arm-linux-gnueabihf:$BASE/armhf-deps/usr/lib/arm-linux-gnueabihf:$WP/lib_armhf/graphics/mesa_x11_stub:$WP/lib_armhf:/usr/lib32:/mnt/SDCARD/spruce/flip/lib32"
export BOX86_LD_LIBRARY_PATH="$WINE/lib:$WINE/lib/wine/i386-unix:$LAB/x86lib"
export BOX86_NOBANNER=1 BOX86_LOG=1
export WINEPREFIX=/tmp/thps4-opt-prefix/prefix WINEARCH=win32
export WINELOADER="$BASE/wine-box86-vulkan-memmove.sh" WINESERVER="$BASE/wineserver-box86-vulkan-memmove.sh"
export WINEDEBUG="${THPS4_WINEDEBUG:--all,err+all}" WINEESYNC=0 WINEFSYNC=0
export WINEDLLOVERRIDES="mscoree,mshtml,winemenubuilder=;d3d8,d3d9=n,b"
export XDG_RUNTIME_DIR=/tmp/thps4-runtime DISPLAY=:0
export VK_ICD_FILENAMES="$BASE/vendor-g29-armhf-readable-padding-icd.json" XDG_DATA_HOME="$BASE/vulkan-armhf-cached-home"
export FONTCONFIG_FILE="$LAB/fonts.conf"
unset LD_PRELOAD
export BOX86_WINE_NATIVE_MEMMOVE=1
exec "$BASE/box86-native-memmove-private-glibc" "$WINE/bin/wineserver" "$@"
