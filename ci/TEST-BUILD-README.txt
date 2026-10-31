T YouTube Zversion 4 TEST build
===============================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364)
Signature: same AOSP testkey as v1.0.1, installs as an in-place update
Min Android: 10 (API 29)
APK size: 222584140 bytes
SHA-256: 942a404e86b22f061bdbff25a6ab61dace88238d46dda57e6bc9b365cae6103d

WHAT IS NEW IN ZVERSION 4
-------------------------
This build fixes the three bugs that were still broken on the phone after
Zversion 3, at their actual root cause. It keeps every v1.0.1
playback/download/theme fix.

1) Shorts brand loop (root cause: a second back button)
   Shorts had TWO views with the same id reel_back_button.
   reel_player_static_header.xml was patched, but reel_player_back_button.xml
   (included by reel_non_video_page.xml, reel_non_video_page_v2.xml and
   reel_watch_survey_page.xml) still shipped the plain
   quantum_ic_arrow_back_white_24 arrow, so findViewById() could hand the
   player that arrow instead of the loop. Both layouts now carry the brand
   loop. As a safety net, onWindowFocusChanged restarts the AnimationDrawable
   once the view really has window focus, because start() while detached can
   drop the first frame callback and freeze on the opening arrow.
   Loop: arrow 4.8s -> 225ms crossfade -> "T YouTube" 2.75s -> 225ms
   crossfade. Whole 128x48dp strip is one Back target; title stays at 65dp.

2) Download confirm button (root cause: a rewritten state machine)
   Zversion 3 replaced checkSelectedDownload (305 -> 266 lines) and its
   catch block was just "return-void", so tapping the toolbar download
   button did nothing at all. Zversion 4 restores the original v1.0.1 method
   byte for byte (checked with a diff - only 4 hunks differ) and adds the
   duplicate handling on top of it. The filename still starts with the real
   video title (the FilenameUtils fix is kept).
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
   The About screen now shows "Play Store Version 21.20.402 (Zversion 4)"
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
[ ] About screen shows "Play Store Version 21.20.402 (Zversion 4)".
[ ] Install over the old app without uninstalling; logins, settings and
    downloads are still there.
[ ] Shorts loop: open Shorts and watch the top-left control for 10s. It
    must change to "T YouTube" after 4.8s, hold 2.75s, fade back, repeat.
    No plain white arrow on any Shorts page (video, poll/survey, non-video).
[ ] Shorts tap target: tap arrow, wordmark, and empty strip; all go Back.
[ ] Shorts lifecycle: rotate, background/foreground, re-enter; the loop
    must restart, never freeze on the arrow.
[ ] Fullscreen portrait: show controls; "T YouTube" sits BELOW the scrubber
    line at the bottom, small (14sp) and centred.
[ ] Fullscreen landscape: rotate; watermark stays in place.
[ ] Controls auto-hide: watermark hides with the controls and returns.
[ ] Inline/PiP/Shorts: no watermark.
[ ] Download confirm: tap the toolbar download icon; the dialog closes and
    the download starts (nothing must stay silent).
[ ] Download dialog: Filename starts with the video title, not "download".
[ ] Duplicate download: download the same video twice; the second starts
    immediately and is saved as "Title (1).mp4" (no extra tap/dialog).
[ ] Download in progress: info dialog with Cancel only, no overwrite.
[ ] Stale entry: delete a finished download, then download again; it works.
[ ] Regression: short-title download still opens, seeks resume at quality,
    Shorts do not stall.

AUTOMATED PROOF
---------------
Run scripts/device-proof.ps1 with the phone connected (USB debugging on).
It installs the APK, then checks the Shorts back control class, compares the
frames at t=0s and t=5s (proves the loop animates), looks for the watermark
node while the controls are visible and again after they hide, and taps the
download confirm button while capturing screenshots, uiautomator dumps and
logcat. Everything lands in proof/<timestamp>/ with a PASS/FAIL PROOF.md.

IF SOMETHING FAILS
------------------
Send the phone model, Android version, a screenshot/recording, and the
exact step. For the Shorts loop, include the header. For the watermark,
include fullscreen portrait and landscape with controls shown. For
downloads, include the video title/link and whether the folder was
re-picked. If you ran scripts/device-proof.ps1, send the whole
proof/<timestamp> folder.

ROLLBACK
--------
Install T YouTube v1.0.1 over this build - same signature, no data loss.
