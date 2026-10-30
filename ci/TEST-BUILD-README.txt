T YouTube Zversion TEST build
=============================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364)
Signature: same AOSP testkey as v1.0.1, installs as an in-place update
Min Android: 10 (API 29)

WHAT IS NEW IN ZVERSION
-----------------------
This is a separate test build on top of stable v1.0.1. It keeps every
v1.0.1 playback/download/theme fix and adds three changes:

1) Shorts header brand loop
   The top-left Shorts back control cycles every 8 seconds:
   arrow (4.8s) -> 225ms crossfade -> "T YouTube" (2.75s) -> 225ms
   crossfade -> arrow. The whole 128x48dp strip is still one Back target.
   The video title must stay in exactly the same position.

2) Fullscreen "T YouTube" watermark
   A small 18sp bold "T YouTube" wordmark, 80% white, centred in the
   bottom control row between the left controls and "More videos".
   It appears only in fullscreen while the controls are visible, in
   portrait and landscape. It must never appear inline, in miniplayer/PiP,
   or in Shorts, and it must not intercept taps or move any control.

3) Download dialog duplicate-name fix
   When a file with the same name already exists, the dialog offers
   "Generate unique name" as the positive/default action (for example
   "Title (1).mp4") and "Overwrite" as a separate neutral action.
   Pending and Running downloads never offer Overwrite. A finished
   mission whose file was deleted can be downloaded again.

Everything from v1.0.1 is still included: download-crash fix, visionOS
playback client (seek + quality), iOS stream source, dark theme, and the
#00FCFF / #F3024E seekbar.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube v1.0.1. Do NOT uninstall the old app first (you would lose
downloads and settings). If Android says "App not installed", stop and
report it - do not uninstall.

TEST CHECKLIST
--------------
[  ] Install over v1.0.1 without uninstalling. Logins, settings and
     downloads must still be there.

[  ] Shorts loop: open Shorts and watch the top-left back control for
     about 10 seconds. It must change from the arrow to "T YouTube"
     after 4.8 seconds, hold for 2.75 seconds, then fade back. It must
     repeat. The video title must not move during the loop.

[  ] Shorts tap target: tap the arrow, tap the wordmark, and tap the
     empty part of the 128x48dp strip. All three must go Back.

[  ] Shorts lifecycle: rotate, leave Shorts, and re-enter. The loop must
     start again cleanly, with no doubled animation or stuck frame.
     TalkBack must still announce it as the Back button.

[  ] Fullscreen portrait: open a video, go fullscreen, and show the
     controls. "T YouTube" must appear centred at the bottom between the
     left time controls and "More videos". It must not overlap or push
     any button.

[  ] Fullscreen landscape: rotate while fullscreen. The watermark must
     stay in the same place, with no clipping.

[  ] Controls auto-hide: wait for the controls to hide. The watermark
     must hide with them. Tap to show the controls; it must return in the
     same place. Tap directly on the watermark; the tap must reach the
     player/controls, not be swallowed.

[  ] Inline/PiP/Shorts: the watermark must not appear in the normal
     inline player, miniplayer/PiP, or Shorts.

[  ] Download duplicate: download a video, then download the same video
     again. The dialog must show "Generate unique name" as the main
     action and "Overwrite" as a second action. Choose unique name and
     confirm both files exist.

[  ] Download overwrite: repeat, choose "Overwrite". It must replace the
     file without an error and the new file must play.

[  ] Download in progress: start a large download, then try downloading
     the same title. The dialog must not offer "Overwrite" while it is
     Pending or Running.

[  ] Stale entry: delete a finished download from the Downloads screen
     (keep the file if asked), then download the same video again. It
     must download normally, not claim the file already exists.

[  ] Regression: the download dialog still opens for a normal short
     title (v1.0.1 fix), long seeks still resume at quality, and Shorts
     do not stall.

[  ] Link guide (optional): if you want youtube.com links to open in
     T YouTube, follow the two settings steps in the site guide. If not,
     skip - links still open as before.

IF SOMETHING FAILS
------------------
Shorts loop does not appear:
   Send a screenshot/recording of the Shorts header, the phone model,
   Android version, and whether the app was installed over v1.0.1.

Fullscreen watermark does not appear or appears inline:
   Send fullscreen portrait and landscape screenshots with controls
   shown and hidden, plus the inline player screenshot.

Download dialog has no working button or the app freezes:
   Send the video title or link, the phone model, and whether the file
   already existed. If possible, include a logcat taken while tapping
   Download.

UI looks different from v1.0.1:
   Take a screenshot. Check that the installed file is
   T-YouTube-Zversion.apk from the test-zversion release.

ROLLBACK
--------
Install T YouTube v1.0.1 over this build - same signature, no data loss.
