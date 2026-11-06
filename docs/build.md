# Build and provenance

The builder downloads pinned release artifacts and Debian packages, verifies
SHA256, uses a pinned Slang compiler to generate the BCn shaders,
and cross-compiles Box86, the WSI layer, the BCn layer and the native
X11 display helper. It assembles only the selected runtime, not all the research
variants. It creates a new empty ext4 prefix image rather than copying the
tested user's registry, saves or cache.

- `runtime/sources.json`: upstream URLs, release hashes and Git commits.
- `runtime/dependencies.json`: exact Debian artifacts, archive members,
  destination paths and library hashes. Snapshot-by-content URLs provide a
  fallback when a Debian pool version disappears.
- `patches/`: reviewable changes to Box86, WSI and BCn.
- `tools/patch-mali.py`: validates the exact vendor ELF and adjusts the first
  load segment's readable padding. It refuses unexpected input/output hashes.
  This is a private runtime driver; it does not flash firmware or replace the
  Spruce system driver.
- `tools/Containerfile`: Debian Bookworm build environment. Container packages
  are not fully snapshot-pinned, so output is not claimed bit-for-bit identical
  across compiler/container updates. Source revisions and downloaded runtime
  inputs are pinned.

The target directory name `Persistent/thps4-lab` is historical but intentional:
ELF interpreter and Vulkan manifest paths target `/mnt/SDCARD` there. Moving it
requires rebuilding/updating those paths. ARMhf private glibc and native AArch64
compositor libraries serve different processes; do not mix their loaders.

Run `python3 tools/build.py` on Linux with Podman/Docker. Reuse `work/downloads`
for verified download caching. `work/sources` contains builder-owned source
trees; do not put unrelated work there. Patches are applied idempotently.
Delete `work/build-*` to force clean CMake builds after changing toolchains.
`dist/runtime/manifest.json` hashes every installed runtime file.

## Research tools

`tools/probes/` contains material, low-address Vulkan, import-capability and
memory-copy probe sources, plus a profile summarizer. They are research inputs,
not part of normal installation. Their results depend on the exact Wine,
loader, driver and architecture used. The low-map tests are deliberately not
a promise that native-64-bit Wine/Hangover is viable.

`tools/display-helper.c` provides `--ready` (XOpenDisplay + XSync) and
`--temperature` (one thermal read per second, small X11 child window). It matches
the game's WM_CLASS and does not read back each game frame or steal focus.

See [third-party notices](../THIRD_PARTY_NOTICES.md) for upstream licenses.
No prebuilt runtime release is currently promised. Build-time download failures
should be reported with the filename and hash, without supplying game files.

## Validation of this repository

The pinned inputs assembled successfully, all four cross-compiled components
built, and the resulting 181-file runtime manifest verified. The declared
Containerfile also built and ran the assembly successfully using the verified
download/source/build caches. Host tests cover game packaging isolation, path
escape rejection, corrupted runtime rejection and preservation of existing
saves/config/prefix during a repeat install:

```sh
python3 -m unittest discover -s tests -v
```

The handheld screenshots/gameplay evidence use the selected tested runtime.
A successful source build alone does not validate every PC executable or every
fresh-card configuration. This remains an experimental release.

A temporary freshly formatted prefix was initialized on the handheld with the
public launcher's first-boot code, without replacing the established prefix.
It advanced from loading to rendered College gameplay, including HUD, FPS and
CPU temperature. This checks prefix bootstrapping against the retained tested
runtime; it is not a second independently provisioned handheld/card test.
The actual 181-file built kit and game image also passed a host installation
check, including executable permission preservation.

All 58 pinned Debian dependency artifacts also passed a fresh network download
and SHA256 check independently of the seeded build cache at publication time.
