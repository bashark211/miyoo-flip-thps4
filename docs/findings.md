# Research findings (November 2026)

This work started with an x86 Windows PC game and an RK3566 handheld, not engine
source. Existing infrastructure was investigated before the selected route was
kept. Celeste's FNA repack, Cuphead's Android/Unity approach and GTA SA's Android
wrapper use very different available runtimes; their existence does not supply
a THPS4 PC engine port. [THPS4-Recomp](https://github.com/GabrielBigardi/THPS4-Recomp)
targets the **PS1 edition**, a different engine/version from the requested PC/PS2
experience. A bespoke engine reconstruction remains a separate project.

## Selected route

Wine 8.21 x86 + Box86 ARMhf + panDXVK D3D8/9, BCn buffer-compute decode, private
G29 ARMhf vendor Vulkan, X11 SHM WSI and Westonpack/Crusty display. Native 32-bit
and 64-bit rotating textured cubes both displayed. The actual 32-bit Windows
game subsequently rendered menus, gameplay, textures and HUD and saved careers.
Simple graphics probes were useful but never treated as equivalent to the game.

| Experiment | Observation / decision |
| --- | --- |
| WineD3D/OpenGL | Early working UI but roughly 1–7 FPS. Superseded by Vulkan. |
| d3d8to9 | Player felt about the same as the working comparison; no demonstrated benefit. |
| Cached X11 readback | Profiling found full-frame uncached copies. HOST_CACHED memory + explicit invalidation reduced the CPU-copy hotspot; player reported faster skating. Kept. |
| Native Wine memmove | Exact signature opt-in bridge to ARM libc passed correctness cases, removed translated copy hotspot. Kept; separate FPS gain unproven. |
| Generic cached/write-only GPU buffers | Felt slower; desired cached+coherent Mali memory type unavailable. Rejected. |
| Shadows off / 16×16 shadow | Shadow removal visible, speed about the same. Kept original game behavior. |
| Larger Box86 blocks / CALLRET | No clear improvement / startup crashes respectively. Rejected. |
| Renderer flags / partial PARTYMOD experiments | No clear improvement; not a validated full mod integration. |
| BCn ASTC/image-view paths | Synthetic tests could pass while alpha/geometry broke. Buffer decode selected. |
| D3D8 batching experiment | Missing 3D objects. Rejected. |
| Direct Wayland Wine | Native cube worked, but Wine/Box86 proxy/event bridges were incomplete. Not a usable game route. |
| Sarek 1.11.1 Mali | Six material checks passed; game audio/menu input ran behind a frozen loading frame. Rejected, exact cause unresolved. |
| Native64/Hangover + Mali wrapper | Low-address explicit synchronization probes passed, but coherent-map requirements failed. Not selected. |

## Why not simply switch to native64?

A normal vendor map can return addresses outside Win32's address range. A
low-address wrapper passed native64 and real PE32 explicit flush/copy/invalidate
checks, but a coherent-without-explicit-sync case read stale data (exit 6).
DMA-BUF capabilities were import-only; host allocation and uncached DMA heap
imports selected noncoherent memory and declined the coherent-required tests
(exit 5). A kernel alias ioctl returned ENOTTY. These are concrete compatibility
barriers for that tested configuration, not a proof that future work is impossible.
No kernel patch, firmware flash or global driver replacement was attempted.

## Startup and save correctness

A fixed sleep before Wine was unreliable after cleanup. The selected launcher
uses an X11 handshake, then starts Wine. Two fresh launches showed full menus,
FPS and CPU temperature; normal exit cleaned the game/display helpers.
The initial zero-space career error was resolved with a writable game overlay
and a save-directory bind mount. The user explicitly confirmed successful saves.

## Upstream work consulted

- [PortMaster performance and memory guide](https://github.com/Knifethrower/PM-Porting-Tools/blob/main/docs/performance-and-memory.md)
- [Box86 usage and tuning](https://github.com/ptitSeb/box86/blob/master/docs/USAGE.md)
- [panDXVK](https://github.com/isygold/panDXVK)
- [WSI layer](https://github.com/ginkage/vulkan-wsi-layer)
- [BCn layer](https://github.com/leegao/bcn_layer)
- [Mali Vulkan wrapper low-address notes](https://github.com/zeyadadev/mali-vulkan-icd-wrapper/blob/main/docs/low-address-mapping.md)
- [Celeste repacker](https://github.com/JohnnyonFlame/celeste-repacker), [Cuphead PortMaster work](https://github.com/wild1walker/portmaster-cuphead), [GTA SA Vita wrapper](https://github.com/TheOfficialFloW/gtasa_vita)

Pinned build revisions are in the manifests. Unproven replacements are not
silently promoted into the only playable entry.
