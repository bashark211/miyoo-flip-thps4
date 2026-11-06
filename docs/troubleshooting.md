# Controls and troubleshooting

The supplied `runtime/thps4.gptk` and `config.cfg` are the tested mapping pair.
Keep them together. They use PortMaster's `gptokeyb`; normal PortMaster exit is
its Back/Select + Start hotkey. If the game hangs, an SSH `TERM` to the launcher
allows its cleanup trap to stop Wine and unmount the writable state. Avoid a
hard power cut while saving. Do not delete a lock while a game is still running.

## Black screen, then return to Ports

A previous launcher started Wine before Xwayland was ready. The corrected
launcher waits for a real display connection, with bounded retries. Reopen
Ports and confirm you are using the current THPS4 entry. Inspect:

- `Persistent/thps4-lab/route-research/box86-vulkan-display-launch.log`
- `box86-vulkan-weston.log` and `box86-vulkan-seatd.log` in that directory
- `dxvk-results/native-memmove-baseline-pandxvk/game.log`
- `first-boot.log` if a blank prefix is being initialized

A visible loading image alone does not prove continuing frame presentation:
the rejected Sarek build kept audio/input running behind a frozen frame.

## No text, transparent objects or corrupted textures

Use the pinned panDXVK candidate and buffer-compute BCn configuration. Earlier
GL, image-view/ASTC decoding and batching experiments had different failures.
Do not combine DLLs, layers and manifests from old tests. Verify the runtime
manifest before changing game files.

## Not enough space to save

The original failure came from presenting the read-only game image as the
working game drive. The launcher now uses a writable overlay and maps `T:` to
it, with `Save` bound to the SD folder. Verify real free space too. Do not copy
save files into the read-only image; preserve the save folder and prefix when
upgrading.

## Low FPS or heat

Expect variable performance, not locked 30 FPS. Busy areas and thermal CPU
clock changes matter. Compare the same stationary scene and report FPS range,
CPU temperature, firmware and game-build fingerprint. Shadows-off and smaller
shadow textures did not produce a clear improvement in our tests. Do not use
the discarded cached-buffer or CALLRET candidates as assumed optimizations.

## Stale session lock

`/tmp/thps4-session-lock` prevents competing sessions. Check that THPS4, Wine,
Weston and its mounts have exited before removing a stale lock. A normal reboot
clears `/tmp`; do not erase persistent saves/prefix to fix a session lock.
