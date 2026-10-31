T YouTube v1.1.0 - stable update
================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364) - same package + versionCode
Signature: same AOSP testkey as v1.0.1, installs as an in-place update
Min Android: 10 (API 29)
Size: 222,584,140 bytes (212.3 MiB)
SHA-256: 337f55a17c8fdd1ae458a4ab9e76ca3bd1335c3865ca0bb5de055fd078496d5c

WHAT CHANGED (all four fixes were first shipped and verified as Zversion 4)
---------------------------------------------------------------------------
1) Shorts brand loop (root cause: a second view with the same id)
   Shorts had TWO views with the id reel_back_button. The patched header
   (reel_player_static_header.xml) was fine, but reel_player_back_button.xml
   (included by reel_non_video_page.xml, reel_non_video_page_v2.xml and
   reel_watch_survey_page.xml) still shipped the plain
   quantum_ic_arrow_back_white_24 arrow, so findViewById() could hand the
   player that arrow instead of the brand loop. Both layouts now carry the
   brand loop, and onWindowFocusChanged restarts the AnimationDrawable once
   the view really has window focus, so it can no longer freeze on frame 0.
   Loop: arrow 4.8s -> 225ms crossfade -> "T YouTube" 2.75s -> 225ms
   crossfade. The whole 128x48dp strip is one Back target; the title stays at
   65dp and does not move. TalkBack description is unchanged.

2) Download confirm button (root cause: a rewritten state machine)
   A previous test build had replaced checkSelectedDownload (305 -> 266
   lines) and its catch block was just "return-void", so tapping the toolbar
   download button did nothing at all. v1.1.0 restores the original v1.0.1
   method byte for byte (checked with a diff - only 4 hunks differ) and adds
   the duplicate handling on top of it. The filename still starts with the
   real video title (the FilenameUtils fix is kept).
   Duplicate finished file, or a file with no mission -> the app's own
   createUniqueFile() runs and the download starts immediately: no prompt,
   no extra tap, no overwrite. Pending/Running -> information dialog with
   only a Cancel button, never overwritten.

3) Fullscreen watermark (lower and smaller)
   14sp bold white 80%, 32dp tall, anchored to the BOTTOM of the control row
   so it sits below the scrubber line, with a 4dp margin. It is hidden
   through onVisibilityChanged, which Android documents as firing when the
   view OR an ancestor changes visibility, so it disappears with the controls
   instead of one layout pass later. Controls-only, portrait and landscape,
   not clickable, no layout shift, absent inline/PiP/Shorts.

4) Build marker
   The About screen now shows "Play Store Version 21.20.402 (v1.1.0)" so you
   can confirm the new build is installed. The actual app version remains
   21.26.364.

EVERYTHING IN v1.0.1 IS KEPT
----------------------------
- Download crash on short titles stays fixed (80-char cap only when the title
  is really longer than 80 characters).
- Filenames are cleaned with the app's charset and the downloader's iOS
  stream source is enabled, so downloads complete.
- Seeking long videos resumes at the selected quality (visionOS client).
- Shorts no longer stall; Shorts downloads keep working.
- Dark theme by default.
- Auto-brightness, PiP default, notification channels, theme colours.

DOWNLOAD FOLDER ERROR
---------------------
If the download dialog says "The destination folder can not be created",
the app's saved download folder is no longer writable (common after changing
phones, removing an SD card, or clearing app data). Fix it once:
  Settings -> Downloads -> Video download folder -> pick a folder on
  internal storage (for example Download/T YouTube) -> Use this folder ->
  Allow. Then try the download again.
This is a storage-folder setting, not a naming bug.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube v1.0.1 (or any test build). Do NOT uninstall the old app first
(you would lose downloads and settings). If Android says "App not
installed", stop and report it - do not uninstall.

ROLLBACK
--------
Install T YouTube v1.0.1 over this build - same signature, no data loss.
https://github.com/engrtarun/T-YouTube/releases/download/v1.0.1/T-YouTube-v1.0.1.apk

IF SOMETHING FAILS
------------------
Send the phone model, Android version, a screenshot/recording and the exact
step. For the Shorts loop, include the header. For the watermark, include
fullscreen portrait and landscape with controls shown. For downloads,
include the video title/link and whether the folder was re-picked. If you
ran scripts/device-proof.ps1, send the whole proof/<timestamp> folder.
