# Reddit draft — not posted

Suggested subreddit: r/MiyooFlip

**Title:** THPS4 PC running on Miyoo Flip V2: Vulkan + Wine/Box86, around 20–30 FPS (experimental)

I wanted the PC/PS2-style Tony Hawk's Pro Skater 4 on my Flip V2, so we worked
through the existing compatibility projects and got the **Windows PC edition**
running on Spruce. This isn't PS2 emulation or a native engine port, and it
isn't an official PortMaster release.

Menus, HUD, textures, sound, College gameplay and career saving work in my tests.
I'm generally seeing 20–30 FPS, with dips around 15–20 in busy areas. It's not
locked 30, and I haven't validated the whole campaign. The video shows the
actual handheld with the FPS and CPU-temperature counters visible.

[VIDEO: add handheld recording here before posting]

The setup uses Wine 8.21 + Box86 + panDXVK, BCn compute decoding, a private
32-bit Mali Vulkan driver and a WSI/Weston display stack. The biggest change was
moving away from the very slow OpenGL route. Profiling then found an expensive
full-frame GPU-to-X11 memory copy; cached readback helped. There's also a narrowly
matched Wine memmove bridge. We kept the failed experiments and limitations
in the findings rather than treating every tweak as a win.

**Instructions, source patches and research:**
https://github.com/bashark211/miyoo-flip-thps4

You need to supply your own installed **PC game files**. The repo has no game
executable/assets, keys, personal Wine prefix or saves. It's a build/install
project for this specific Spruce/Flip setup, not a universal one-click port.

If you try it, please include your firmware, game build, scene, FPS/temperature,
and whether graphics and saving work. I'd especially welcome ideas for reducing
translation/driver overhead without breaking the rendering.
