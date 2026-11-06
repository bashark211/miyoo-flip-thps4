# Third-party components

The repository's original scripts and documentation use the MIT license.
Upstream software keeps its own license. The builder downloads upstream
artifacts directly; no game files, vendor-driver binary, pre-existing Wine
prefix or saves are included in this repository.

| Component | Pinned source | License / use |
| --- | --- | --- |
| Box86 | ptitSeb/box86, bb716a2a6576cc06da811bf55e31e2f6f03b7596 | MIT upstream; native-call bridge patch supplied here |
| Wine | Wine 8.21; Kron4ek Wine-Builds x86 archive | LGPL-2.1-or-later; downloaded unmodified |
| WSI layer | ginkage/vulkan-wsi-layer, 40cfec09d0e2d42c5e1f2642cf4cba11e7008112 | MIT, Arm and contributors; cached-readback patch supplied |
| BCn layer | leegao/bcn_layer, 50993a2d51772567de9c36de4d523652773f0899 | MIT, Pipetto-crypto and contributors; optional-fault diagnostic guard supplied |
| Slang shader compiler | shader-slang/slang v2026.10.2 (build-time only) | Upstream Slang license, included as licenses/SLANG.txt |
| Vulkan headers | KhronosGroup/Vulkan-Headers, 8d6039a455a7ecc7d2a592ff97f62db4e59b70bf | Upstream Apache-2.0/MIT notices |
| panDXVK | isygold/panDXVK v01 / fa53ce71 | Upstream license in licenses/DXVK.txt; downloaded release DLLs |
| Westonpack | PortsMaster/PortMaster-New, 2025-07-24_0745, weston_pkg_0.2 | Mixed licenses for Weston, Xwayland, Crusty and bundled libraries; downloaded upstream runtime |
| Mali G29 ARMhf | JeffyCN/mirrors pinned blob | Arm/vendor license applies; downloaded from its upstream mirror and patched locally at ELF program-header fields only |
| Private C/X11/Vulkan runtime libraries | Debian packages listed in runtime/dependencies.json | Individual upstream licenses; exact package versions, source package names, URLs and hashes are recorded |

The Box86 patch contains a 495-byte identification signature derived from
Wine 8.21's SSE2 memmove implementation. That patch is offered under
LGPL-2.1-or-later, including the Wine-derived signature; the original Box86
code retains its MIT notice. See licenses/WINE-LGPL-2.1.txt and the Wine source
at https://github.com/wine-mirror/wine/blob/wine-8.21/dlls/msvcrt/string.c.
The signature is used to recognize an exact implementation, not to replace
an arbitrary game function.

The WSI and BCn MIT license texts are included in licenses/. The patches are
not substitutes for the complete upstream source. Source revisions and build
instructions are provided so modified open-source components can be rebuilt.
If distributing built runtime packages, preserve the upstream notices and
meet the source-availability requirements of the components you distribute.

THPS4, its game executable, art, music and data belong to their respective
rights holders. The screenshot illustrates the technical result; it is not
a source of game assets. This project supplies no serials, activation or
disc-check bypass and makes no claim that every retail executable works.
