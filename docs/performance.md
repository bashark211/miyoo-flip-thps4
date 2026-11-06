# Performance evidence and limits

Player reports for the later selected route: typically **20–30 FPS**, sometimes
**15–20** in busy areas. The first Vulkan run also dipped to 10–15. These were
interactive observations, not a synchronized benchmark trace. No locked-FPS,
percentage-FPS improvement or complete campaign claim is made.

## CPU profiles

Stationary College profiles used approximately one minute of sampling. They
are samples of CPU time, **not GPU utilization or frame-time measurements**.
Percentages describe the sampled process, including its different threads.

| Capture | Samples | Sampled CPU seconds | Native libc share | msvcrt share |
| --- | ---: | ---: | ---: | ---: |
| Before cached readback | 29,674 | 149.116 | 23.519% | 7.963% |
| Cached readback | 25,453 | 127.905 | 3.418% | 8.781% |
| Native memmove, busy spot | 27,984 | 140.623 | 5.614% | 0.529% |

The first capture identified `__memcpy_neon`, copying **0x12c000 bytes**
(640×480×4) from a Mali mapping into X11 SYSV shared memory in the WSI caller.
Changing that readback allocation to HOST_VISIBLE|HOST_CACHED, then explicitly
invalidating it after the GPU fence, sharply reduced native-libc CPU time in
subsequent profiles. The player independently reported a faster feel.

Comparisons are imperfect: executable/shadow configurations differed in the
first comparison, and the later user-chosen busy spot was a different scene.
CPU frequencies ranged from roughly 1.1 to 1.8 GHz and temperatures reached
83–85°C in the busy capture. Do not turn CPU-share changes into a claimed FPS
percentage. Kernel syscall CPU time did not show evidence that the initial
copy reduction merely moved the same work into the kernel.

## Wine memmove bridge

An opt-in Box86 change recognizes one exact 495-byte, relocation-free Wine 8.21
SSE2 memmove routine and routes it through Box86's existing native cdecl bridge.
It does not patch the game. The fixture signature's SHA256 is
`4e5ab519a3b8e7246513fbec4a72a0f719a75526ab502c7a626cce0e9259028d`.

3,200 correctness cases per disabled/enabled/negative-fixture configuration
passed, covering overlap, alignment, zero length, return pointer and canaries.
Only the exact fixture was intercepted. Small-copy timings improved; large
1-MiB timings were mixed. Six D3D material checks passed and the user confirmed
correct menus/HUD/textures and playable College. The later msvcrt hotspot was
much smaller, but an isolated FPS benefit has **not** been established.

## Better future comparisons

Keep the same executable, save, stationary location, camera and settings.
Warm up caches, log clock/temperature, repeat each candidate, record frame times
and include visual/save validation. Compare one change at a time. Preserve the
working prefix and launcher before testing. Raw memory, process maps and
personal saves from our profiling sessions are not distributed here.
