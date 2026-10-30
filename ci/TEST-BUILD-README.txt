T YouTube Zversion 3 TEST build
===============================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364)
Signature: same AOSP testkey as v1.0.1, installs as an in-place update
Min Android: 10 (API 29)
APK size: 222584227 bytes
SHA-256: 181aa22e700d59e3e2d3910064d1ba1b1ac4d6cd6a3a9024ea6c48962969e4a3

WHAT IS NEW IN ZVERSION 3
-------------------------
This build fixes three bugs that made the Zversion 2 changes invisible on
the phone. It keeps every v1.0.1 playback/download/theme fix.

1) Shorts brand loop (actually starts now)
   The custom view only started the loop when it was already marked
   visible, so the hidden-to-visible transition was skipped. Zversion 3
   fixes that guard and starts the 8-second loop (arrow 4.8s -> 225ms
   crossfade -> "T YouTube" 2.75s -> 225ms crossfade) as soon as the
   header appears. The whole 128x48dp strip is one Back target; the title
   stays at 65dp.

2) Fullscreen "T YouTube" watermark (actually appears now)
   The view's OnGlobalLayoutListener was never registered because the
   listenerAttached check was inverted. Zversion 3 attaches the listener,
   updates immediately on attach, and keeps the watermark in both
   bottom-control layouts. 18sp bold white 80%, controls-only, portrait
   and landscape, no taps, no layout shift.

3) Download filename (uses the video title now)
   v1.0.1's FilenameUtils had an inverted isEmpty() check: every non-empty
   title was replaced with the literal "download". Zversion 3 restores the
   title, so the dialog starts with the real video name. Duplicate finished
   downloads still auto-rename via createUniqueFile ("Title (1).mp4");
   Pending/Running remain info-only and are never overwritten.

4) Build marker
   The About screen now shows "Play Store Version 21.20.402 (Zversion 3)"
   so you can confirm the new build is installed. The actual app version
   remains 21.26.364.

DOWNLOAD FOLDER ERROR
---------------------
If the download dialog says "The destination folder can not be created",
the app's saved download folder is no longer writable (common after
changing phones, removing an SD card, or clearing app data). Fix it once:
  Settings -> Downloads -> Video download folder -> pick a folder on
  internal storage (for example Download/T YouTube) -> Use this folder ->
  Allow. Then try the download again.
This is a storage-folder setting, not a naming bug.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube v1.0.1 or Zversion build. Do NOT uninstall the old app first
(you would lose downloads and settings). If Android says "App not
installed", stop and report it - do not uninstall.

TEST CHECKLIST
--------------
[ ] About screen shows "Play Store Version 21.20.402 (Zversion 3)".
[ ] Install over the old app without uninstalling; logins, settings and
    downloads are still there.
[ ] Shorts loop: open Shorts and watch the top-left control for 10s. It
    must change to "T YouTube" after 4.8s, hold 2.75s, fade back, repeat.
    The title must not move.
[ ] Shorts tap target: tap arrow, wordmark, and empty strip; all go Back.
[ ] Shorts lifecycle: rotate, leave and re-enter; loop restarts cleanly.
[ ] Fullscreen portrait: show controls; "T YouTube" appears centred at the
    bottom between the left time controls and "More videos".
[ ] Fullscreen landscape: rotate; watermark stays in place.
[ ] Controls auto-hide: watermark hides with the controls and returns.
[ ] Inline/PiP/Shorts: no watermark.
[ ] Download dialog: Filename starts with the video title, not "download".
[ ] Duplicate download: download the same video twice; the second starts
    immediately and is saved as "Title (1).mp4" (no extra tap/dialog).
[ ] Download in progress: info dialog only, no overwrite.
[ ] Stale entry: delete a finished download, then download again; it works.
[ ] Regression: short-title download still opens, seeks resume at quality,
    Shorts do not stall.

IF SOMETHING FAILS
------------------
Send the phone model, Android version, a screenshot/recording, and the
exact step. For the Shorts loop, include the header. For the watermark,
include fullscreen portrait and landscape with controls shown. For
downloads, include the video title/link and whether the folder was
re-picked.

ROLLBACK
--------
Install T YouTube v1.0.1 over this build - same signature, no data loss.
