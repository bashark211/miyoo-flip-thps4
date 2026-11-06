# Research probes

The C sources are diagnostic programs, not part of normal game installation.
Use the architectures and headers required by each source. `d3d8-materials.c`
is a Win32/MinGW test; Vulkan import probes are native ARM tests.

To rebuild the freestanding i386 memory-copy probe:

```sh
python3 tools/probes/make-memmove-fixtures.py
cd work/memmove-probes
# Requires an i386-capable GCC/binutils toolchain:
gcc -m32 -O2 -fno-builtin -fno-stack-protector -nostdlib -no-pie \
  ../../tools/probes/memmove-probe.c ../../tools/probes/memmove-probe.S -o memmove-probe
```

Build the negative fixture by changing the `.incbin` filename to
`wine821-sse2-memmove-negative.bin`. It swaps equivalent register save/restore
instructions. Run with the target Box86 bridge disabled, enabled, and enabled
against that negative fixture; correctness should pass all three and only the
exact original signature should log interception. Fixture bytes derive from
Wine 8.21 and use LGPL-2.1-or-later, as does the bridge patch.

A probe passing does not establish full-game correctness. See the findings for
the Sarek loading-frame failure and noncoherent mapping limitations.
