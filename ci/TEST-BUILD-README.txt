T YouTube fixed TEST build (test-fix-4)
=======================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.0 (YouTube 21.26.364) + all v1.0.1 fixes + test-fix-4
Signature: same AOSP testkey as v1.0.0/v1.0.1, installs as an in-place update
Min Android: 10 (API 29)

WHAT IS NEW IN test-fix-4
-------------------------
1) Shorts "T YouTube" brand loop
   The back arrow in the Shorts header now runs an 8-second animation:
   arrow (4.8s) -> crossfade -> "T YouTube" (2.75s) -> crossfade -> arrow.
   The whole 128x48dp strip is still ONE Back button. Tapping it at any
   moment - including while the words are showing - must go back.
   The video title is pinned to its old position, so nothing jumps.

2) Fullscreen "T YouTube" watermark (controls only)
   In fullscreen the wordmark sits centred in the bottom action row,
   between the left controls and "More videos". It appears in BOTH
   portrait and landscape fullscreen, and ONLY while the controls are
   visible. Tap the video to hide the controls: the wordmark must hide
   with them. It is not clickable.

3) Download dialog: duplicate names and stale entries
   When a file with the same name exists, the dialog now defaults to
   "Generate unique name" (e.g. "Title (1).mp4"). "Overwrite" is a
   separate, explicit button and is not offered while a download is
   running. A finished download whose file was later deleted no longer
   blocks a new download of the same title.

4) YouTube link guide (optional - you may skip it)
   The site and README explain how to make youtube.com links open in
   T YouTube. This cannot be automatic: Android allows one app per site
   and official YouTube currently owns youtube.com, so it must be
   released in Android settings first. Skipping changes nothing.

Everything from v1.0.1 is still included: download-crash fix, visionOS
playback client (seek + quality), iOS stream source, dark theme, and the
#00FCFF / #F3024E seekbar.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube. Do NOT uninstall the old app first (you would lose downloads
and settings). If Android says "App not installed", stop and report it -
do not uninstall.

TEST CHECKLIST (about 8 minutes)
--------------------------------
[  ] Shorts loop: open Shorts. The header arrow should change into
     "T YouTube" after a few seconds, then back to the arrow.
[  ] Shorts Back: wait until the words are visible, then tap the words.
     It MUST go back. Repeat twice.
[  ] Shorts title: the video title must stay in the same place the whole
     time - it must not shift left or right when the words appear.
[  ] Fullscreen portrait: play a normal video, go fullscreen, tap once to
     show controls. "T YouTube" must be centred at the bottom between
     the left buttons and "More videos". Wait for the controls to hide -
     the wordmark must hide too.
[  ] Fullscreen landscape: rotate to landscape fullscreen and repeat.
[  ] Inline (not fullscreen): the watermark must NOT appear.
[  ] Download duplicate: download a video, then download the same video
     again. The dialog must offer "Generate unique name" as the main
     action and "Overwrite" as a second action. Choose unique name and
     confirm both files exist.
[  ] Download overwrite: repeat, choose "Overwrite". It must replace the
     file without an error and the new file must play.
[  ] Download stale entry: delete a finished download from the Downloads
     screen (keep the file if asked), then download the same video again.
     It must download normally, not claim the file already exists.
[  ] Download in progress: start a large download, then try downloading
     the same title. "Overwrite" must not be offered while it runs.
[  ] Link guide (optional): if you want it, follow the two settings
     steps in the site guide. If not, skip - links still open as before.
[  ] Regression: the download dialog still opens for a normal short
     title (v1.0.1 fix), long seeks still resume at quality, and Shorts
     do not stall.

IF SOMETHING STILL FAILS
------------------------
Shorts tap while words are visible does not go back:
   Send a screenshot of the header and the phone model. That means the
   tap target is being clipped by the animation drawable.

Watermark shows when the controls are hidden, or in inline mode:
   Send the phone model, Android version, and whether it was portrait or
   landscape fullscreen. The gate is "overlay height >= 75% of display
   height", and a screenshot shows which side failed.

Watermark missing in one orientation:
   Same as above - send the orientation and a screenshot with controls
   visible.

Download still says "file not created" or "already exists":
   1. T YouTube settings -> Downloads -> download folder -> choose
      Internal storage (not the SD card), then retry the same video.
   2. If it works on internal storage, the SD card/folder was the
      problem.
   3. If it still fails, send the video title/link and the exact error
      text.

ROLLBACK
--------
Install T YouTube v1.0.1 (or v1.0.0) over this build - same signature, no
data loss.
