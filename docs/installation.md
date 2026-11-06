# Install your own PC copy

This is an experimental compatibility setup for Miyoo Flip V2 + Spruce 4.5.6.
It uses the original **32-bit Windows PC edition**. A PS1/PS2 disc, a console
ROM, a patch archive or an executable without its installed data is insufficient.
Other PC executable revisions may work, but the tested installation does not
establish compatibility with every release. Install your own copy on your PC
first. This project provides no game downloads, keys or activation bypass.

## 1. Build the runtime on Linux

Install Python 3.11+, Git and Podman (or Docker), then:

```sh
git clone https://github.com/bashark211/miyoo-flip-thps4.git
cd miyoo-flip-thps4
python3 tools/build.py
```

Allow several GB of free space. Dependencies are fetched from pinned public
sources, checked against SHA256 and built in a container. See [build.md](build.md).
The output is `dist/runtime/`; it contains no game or personal Wine state.
The container build requires internet access. Do not run two builders in the
same checkout at once.

## 2. Package your installed game

Install `squashfs-tools` on your Linux host, then choose the installed directory
containing `Skate4.exe` and the complete `Data` directory:

```sh
python3 tools/pack-game.py '/path/to/installed/Game' --output "$HOME/thps4-own-game.squashfs"
```

The tool stages a copy, omits personal Save/config and existing D3D overrides,
and excludes movie files by default. Use `--include-movies` if desired; movie
playback has not been validated. It does not alter the source or upload files.
Keep the generated manifest locally to identify your game build in bug reports.

## 3. Install to the SD card

Shut down the handheld and put its Spruce SD card into a laptop reader. Have
PortMaster installed through Spruce: the launcher uses its controls and
`gptokeyb`. Back up the card before installing. Replace the paths below:

```sh
python3 tools/install.py --sd-root '/run/media/you/SDCARD' \
  --game-image "$HOME/thps4-own-game.squashfs"
sync
```

The installer checks the runtime manifest and game-image header. It refuses an
unmarked existing experimental `Persistent/thps4-lab` directory, preserves
existing saves/config/prefix on repeat installs, and refuses to silently replace
a different game image. It is intended for an **offline** card, not a live game.

Eject safely, put the card back, boot Spruce and open **Games → Ports → THPS4**.
The first launch initializes a blank 512-MiB Wine prefix and can take longer.
Later launches wait for an actual X11 handshake rather than a fixed delay.
The FPS counter appears at top left, with CPU temperature beneath it.

## Saves and removal

Career saves live in `Roms/ports/thps4/saves/`; config is next to that folder.
Wine registry/cache/overlay state lives in
`Persistent/thps4-lab/wine-prefix-opt.img`. Back up both **after exiting** the
game. The game image stays read-only; its writable overlay and save bind mount
prevent the original zero-free-space save failure.

Cloud sync is not bundled. Sync closed-game saves with your own backup tool;
do not synchronize a mounted prefix image or let two devices write a career at
once. Save compatibility with other game versions/devices is not established.

To uninstall, exit and shut down, preserve the save/config folder if desired,
then remove `Roms/ports/THPS4.sh`, `Roms/ports/thps4/` and
`Persistent/thps4-lab/`. No system driver replacement is required.
