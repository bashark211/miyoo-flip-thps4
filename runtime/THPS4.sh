#!/bin/bash
# SDK drm/crusty_gbm presentation with the existing vendor Vulkan ICD and WSI layer.
set -e
LAB=/mnt/SDCARD/Persistent/thps4-lab
BASE="$LAB/route-research"
WP=/tmp/thps4-weston
RUN=/tmp/thps4-runtime
LOCK=/tmp/thps4-session-lock
mkdir "$LOCK"
echo "$$" > "$LOCK/pid"
export controlfolder=/mnt/SDCARD/Persistent/portmaster/PortMaster
source "$controlfolder/control.txt"
get_controls
exec > "$BASE/box86-vulkan-display-launch.log" 2>&1
ulimit -c 0
: > "$BASE/vkcube-vendor-wayland.log"
echo RUNNING > "$BASE/box86-vulkan-display.result"
cleanup(){
 if [ -n "${TEMP_PID:-}" ]; then kill -TERM "$TEMP_PID" 2>/dev/null || true; wait "$TEMP_PID" 2>/dev/null || true; fi
 if [ -n "${PAD_PID:-}" ]; then kill -TERM "$PAD_PID" 2>/dev/null || true; fi
 if [ -n "${WINEPREFIX:-}" ]; then timeout -s KILL 6 "$BASE/wineserver-box86-vulkan-memmove.sh" -k >/dev/null 2>&1 || true; timeout -s KILL 6 "$BASE/wineserver-box86-vulkan-memmove.sh" -w >/dev/null 2>&1 || true; fi
 trap - EXIT INT TERM
 cd /
 for point in /tmp/thps4-game/data/models/Ped_Shadow/Ped_Shadowtex.dat /tmp/thps4-game/Skate4.exe /tmp/thps4-game/d3d8.dll /tmp/thps4-game/config.cfg /tmp/thps4-game/Save /tmp/thps4-game /tmp/thps4-game-lower /tmp/thps4-opt-prefix; do
  if awk -v p="$point" '$2==p {f=1} END {exit !f}' /proc/mounts; then
   for attempt in 1 2 3; do umount "$point" && break || sleep 1; done
  fi
 done
 if [ -n "${CUBE_PID:-}" ]; then kill -TERM "$CUBE_PID" 2>/dev/null || true; fi
 if [ -n "${WESTON_PID:-}" ]; then kill -TERM "$WESTON_PID" 2>/dev/null || true; sleep 1; kill -KILL "$WESTON_PID" 2>/dev/null || true; wait "$WESTON_PID" 2>/dev/null || true; fi
 if [ -n "${SEAT_PID:-}" ]; then kill -TERM "$SEAT_PID" 2>/dev/null || true; sleep 1; kill -KILL "$SEAT_PID" 2>/dev/null || true; wait "$SEAT_PID" 2>/dev/null || true; fi
 if [ -n "${SEAT_PID:-}" ] && [ -S /run/seatd.sock ] && ! grep -q '/run/seatd.sock$' /proc/net/unix; then unlink /run/seatd.sock; fi
 if [ "${OWN_FIFO:-0}" = 1 ]; then unlink /tmp/drmpipe 2>/dev/null || true; fi
 ln -snf /usr/lib32/libSDL2-2.0.so.0 /tmp/CRUSTY_LIBSDL.so
 ln -snf /usr/lib32/libEGL.so.1 /tmp/CRUSTY_LIBEGL.so
 if [ "${OWN_SDK:-0}" = 1 ]; then umount "$WP" 2>/dev/null || true; fi
 unlink "$LOCK/pid"; rmdir "$LOCK"
 sync
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
mkdir -p "$WP" "$RUN" /tmp/.X11-unix
chmod 700 "$RUN"
if ! grep -q " $WP " /proc/mounts; then mount -o loop,ro "$LAB/weston_pkg_0.2.squashfs" "$WP"; OWN_SDK=1; fi
export XDG_RUNTIME_DIR="$RUN" WESTON_DATA_DIR="$WP/data" WESTON_LIBEXEC_DIR="$WP/libexec"
export XKB_CONFIG_ROOT="$WP/share/xkb" XKB_BINDIR="$WP/bin"
export WESTON_MODULE_MAP="drm-backend.so=$WP/lib_aarch64/libweston-14/drm-backend.so;gl-renderer.so=$WP/lib_aarch64/libweston-14/gl-renderer.so;xwayland.so=$WP/lib_aarch64/libweston-14/xwayland.so;kiosk-shell.so=$WP/lib_aarch64/weston/kiosk-shell.so;"
export CRUSTY_LIBEGL=/usr/lib/libEGL.so.1 CRUSTY_LIBSDL=/usr/lib/libSDL2-2.0.so.0 CRUSTY_LIBGBM=/usr/lib/libgbm.so.1 CRUSTY_LIBDRM=/usr/lib/libdrm.so.2
export CRUSTY_SHOW_CURSOR=0 SDL_VIDEODRIVER=kmsdrm
ln -snf "$CRUSTY_LIBSDL" /tmp/CRUSTY_LIBSDL.so
ln -snf "$CRUSTY_LIBEGL" /tmp/CRUSTY_LIBEGL.so
if [ ! -e /tmp/drmpipe ]; then mkfifo /tmp/drmpipe; OWN_FIFO=1; fi
if [ -S /run/seatd.sock ]; then
    if grep -q '/run/seatd.sock$' /proc/net/unix; then echo 'Seat daemon socket is active'; exit 1; fi
    unlink /run/seatd.sock
fi
export LIBSEAT_BACKEND=seatd SEATD_SOCK=/run/seatd.sock
NATIVE_LIBS="$BASE/display-deps/aarch64-linux-gnu:$WP/lib_aarch64:/usr/lib:/mnt/SDCARD/spruce/flip/lib"
BACKEND="$WP/lib_aarch64/graphics/crusty_gbm"
LD_LIBRARY_PATH="$BACKEND:$NATIVE_LIBS" LD_PRELOAD="$BACKEND/libcrusty.so" "$WP/seatd" > "$BASE/box86-vulkan-seatd.log" 2>&1 &
SEAT_PID=$!
for attempt in {1..40}; do
 kill -0 "$SEAT_PID"
 [ -S "$SEATD_SOCK" ] && break
 sleep 0.2
done
test -S "$SEATD_SOCK"
cat > "$RUN/box86-vulkan-weston.ini" <<CONFIG
[core]
idle-time=0
[xwayland]
path=$RUN/Xwayland
CONFIG
cat > "$RUN/Xwayland" <<XSERVER
#!/bin/sh
cd $WP
unset LD_PRELOAD
exec $WP/bin/Xwayland -fp $WP/fonts "\$@"
XSERVER
chmod +x "$RUN/Xwayland"
LD_LIBRARY_PATH="$BACKEND:$NATIVE_LIBS" XWAYLAND_LD_LIBRARY_PATH="$WP/lib_aarch64/graphics/mesa_x11_stub:$NATIVE_LIBS" LD_PRELOAD="$BACKEND/libcrusty.so" "$WP/wp_weston" -c "$RUN/box86-vulkan-weston.ini" -B drm --drm-device card0 --renderer=gl --shell=kiosk-shell.so -i0 -Sthps4-vulkan-wayland --xwayland > "$BASE/box86-vulkan-weston.log" 2>&1 &
WESTON_PID=$!
unset LD_PRELOAD
DISPLAY_LIBS="$BASE/deps-modern/aarch64-linux-gnu:$BASE/deps/aarch64-linux-gnu:$NATIVE_LIBS"
ready=0
for attempt in {1..6}; do
 kill -0 "$WESTON_PID"
 if DISPLAY=:0 LD_LIBRARY_PATH="$DISPLAY_LIBS" timeout -s KILL 8 "$BASE/display-helper-aarch64" --ready; then ready=1; break; fi
 sleep 0.5
done
if [ "$ready" != 1 ]; then echo 'X11 display did not become ready; refusing to launch Wine'; exit 1; fi
export LD_LIBRARY_PATH="$BASE/wayland-deps/lib/aarch64-linux-gnu:$BASE/wayland-deps/usr/lib/aarch64-linux-gnu:$BASE/vulkan-modern/aarch64-linux-gnu:$BASE/vkmark-root/usr/lib/aarch64-linux-gnu:$BASE/vulkan-tools/usr/lib/aarch64-linux-gnu:$BASE/deps-modern/aarch64-linux-gnu:$BASE/deps/aarch64-linux-gnu:$NATIVE_LIBS"
export VK_ICD_FILENAMES="$BASE/vendor-g29-icd.json" XDG_DATA_HOME="$BASE/vulkan-home"
export WAYLAND_DISPLAY=thps4-vulkan-wayland VULKAN_WSI_DEBUG_LEVEL=3
unset LD_PRELOAD


THPS4_OPT_MODE=baseline
case "$THPS4_OPT_MODE" in baseline|astc|bigblock|callret|partymod-renderer|renderer-shadow16) ;; *) exit 2;; esac
export THPS4_OPT_MODE
export DISPLAY=:0 WSI_X11_FORCE_SHM=1 WSI_LOW_PRIORITY_QUEUES=0
export DXVK_LOG_LEVEL=info DXVK_HUD=fps
export ENABLE_BCN_COMPUTE=1 BCN_LAYER_LOG_LEVEL=info BCN_DISABLE_DEVICE_FAULT=1 BCN_COMPUTE_IMAGE_VIEW=0 BCN_TRANSCODE_TO_ASTC=0 BCN_TRANSCODE_TO_ETC2=0
case "$THPS4_OPT_MODE" in
 astc) export BCN_TRANSCODE_TO_ASTC=1;;
 bigblock) export BOX86_DYNAREC_BIGBLOCK=2;;
 callret) export BOX86_DYNAREC_CALLRET=1;;
esac
export THPS4_WINEDEBUG=-all,err+all
mounted(){ awk -v point="$1" '$2==point {f=1} END {exit !f}' /proc/mounts; }
mkdir -p /tmp/thps4-wine /tmp/thps4-opt-prefix
mounted /tmp/thps4-wine || mount -o loop,ro "$LAB/wine-8.21-x86.squashfs" /tmp/thps4-wine
mounted /tmp/thps4-opt-prefix || mount -t ext4 -o loop,noatime "$LAB/wine-prefix-opt.img" /tmp/thps4-opt-prefix
export WINEPREFIX=/tmp/thps4-opt-prefix/prefix
if [ ! -f "$WINEPREFIX/system.reg" ]; then
 mkdir -p "$WINEPREFIX"
 timeout -s KILL 180 "$BASE/wine-box86-vulkan-memmove.sh" wineboot.exe -u > "$BASE/first-boot.log" 2>&1
 test -f "$WINEPREFIX/system.reg"
fi
mkdir -p "$WINEPREFIX/drive_c/windows/system32"
export DXVK_STATE_CACHE_PATH="$WINEPREFIX/dxvk-cache"
mkdir -p "$DXVK_STATE_CACHE_PATH"
test -n "${WINEPREFIX:-}"
candidate=pandxvk
case "$candidate" in pandxvk|sarek1-mali) ;; *) exit 2;; esac
for dll in d3d8 d3d9; do
 dest="$WINEPREFIX/drive_c/windows/system32/$dll.dll"
 cp "$BASE/dxvk-candidates/$candidate/$dll.dll" "$dest.new"
 mv -f "$dest.new" "$dest"
done
export DXVK_LOG_PATH="$BASE/dxvk-results/native-memmove-$THPS4_OPT_MODE-$candidate"
mkdir -p "$DXVK_LOG_PATH"
export PANDXVK_TELEMETRY=1 PANDXVK_REPORT_DIR="$DXVK_LOG_PATH/telemetry"
mkdir -p "$PANDXVK_REPORT_DIR"
PORT=/mnt/SDCARD/Roms/ports/thps4
mkdir -p /tmp/thps4-game-lower /tmp/thps4-game "$PORT/saves" /tmp/thps4-opt-prefix/game-overlay/{upper,work}
mounted /tmp/thps4-game-lower || mount -o loop,ro "$LAB/thps4-complete-xz.squashfs" /tmp/thps4-game-lower
mounted /tmp/thps4-game || mount -t overlay overlay -o lowerdir=/tmp/thps4-game-lower,upperdir=/tmp/thps4-opt-prefix/game-overlay/upper,workdir=/tmp/thps4-opt-prefix/game-overlay/work /tmp/thps4-game
DOSDRIVE="$WINEPREFIX/dosdevices/t:"
if [ -e "$DOSDRIVE" ] || [ -L "$DOSDRIVE" ]; then
 test "$(readlink "$DOSDRIVE")" = /tmp/thps4-game
else ln -s /tmp/thps4-game "$DOSDRIVE"; fi
[ -e /tmp/thps4-game/d3d8.dll ] || : > /tmp/thps4-game/d3d8.dll
[ -e /tmp/thps4-game/config.cfg ] || : > /tmp/thps4-game/config.cfg
mkdir -p /tmp/thps4-game/Save
mount --bind "$BASE/dxvk-candidates/$candidate/d3d8.dll" /tmp/thps4-game/d3d8.dll
mount --bind "$PORT/saves" /tmp/thps4-game/Save
mount --bind "$PORT/config.cfg" /tmp/thps4-game/config.cfg
export SDL_GAMECONTROLLERCONFIG_FILE="$controlfolder/gamecontrollerdb.txt"
if [ "${THPS4_OPT_MATERIALS:-0}" = 1 ]; then
 mkdir -p "$WINEPREFIX/direct-dxvk-tests"
 cp "$BASE/d3d8-bc3-materials.exe" "$WINEPREFIX/direct-dxvk-tests/materials.exe"
 cd "$WINEPREFIX/direct-dxvk-tests"
 status=0
 timeout -s KILL 90 "$BASE/wine-box86-vulkan-memmove.sh" "$WINEPREFIX/direct-dxvk-tests/materials.exe" > "$DXVK_LOG_PATH/materials.log" 2>&1 || status=$?
 echo "$status" > "$DXVK_LOG_PATH/materials.exit"
 exit "$status"
fi
SDL_VIDEODRIVER=dummy LD_LIBRARY_PATH=/mnt/SDCARD/spruce/flip/lib:/usr/lib32 "$controlfolder/gptokeyb" -1 Skate4.exe -hotkey back -c "$LAB/thps4.gptk" > "$BASE/box86-dxvk-controller.log" 2>&1 &
PAD_PID=$!
cd /tmp/thps4-game
"$BASE/wine-box86-vulkan-memmove.sh" 'T:\Skate4.exe' > "$DXVK_LOG_PATH/game.log" 2>&1 &
CUBE_PID=$!
echo "$CUBE_PID" > /tmp/thps4-runtime/game.pid
DISPLAY=:0 LD_LIBRARY_PATH="$DISPLAY_LIBS" "$BASE/display-helper-aarch64" --temperature > "$BASE/temperature.log" 2>&1 &
TEMP_PID=$!
wait "$CUBE_PID"
