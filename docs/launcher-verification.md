# Clean launcher verification

The first renamed entry selected the correct panDXVK libraries but Wine could not load a graphics driver. The display startup used a fixed delay and did not verify that the on-demand Xwayland server accepted connections.

The launcher now uses a native AArch64 XOpenDisplay/XSync readiness probe before starting Wine. A finite retry/timeout loop exits with a display-specific log if initialization fails. The probe triggers Xwayland startup and verifies an actual X11 handshake. The first corrected launch retried twice before succeeding, then reached the rendered main menu.

DXVK_HUD=fps remains enabled. A separate native X11 child-window overlay displays the SoC CPU temperature once per second below the FPS display. It identifies the Wine game window by WM_CLASS with a title fallback, takes no input focus, and does not read back game frames. The launcher owns and stops its process during cleanup.

A screenshot confirmed both FPS and CPU temperature on the rendered main menu. A second fresh relaunch of the single THPS4 entry reached the rendered menu with both counters automatically attached; normal exit also removed the helper and compositor processes.

After the complete local history was verified, 1,531 unused SD experiment
files (about 5.06 GiB logical data) were removed. The remaining runtime was
about 1.1 GiB, with 16.7 GiB available on the card. A fresh launch of the normal
THPS4 entry then reached the full textured main menu, with FPS and CPU
temperature visible. The screenshot in the README is from this final check.
The game executable, selected panDXVK DLL and cached WSI layer hashes matched
the working inputs. The instantaneous screenshot FPS is not a benchmark.
