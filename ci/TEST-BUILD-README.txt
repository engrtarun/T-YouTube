T YouTube fixed TEST build (test-fix-5)
=======================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.0 (YouTube 21.26.364) + all v1.0.1 fixes + test-fix-5
Signature: same AOSP testkey as v1.0.0/v1.0.1, installs as an in-place update
Min Android: 10 (API 29)

WHAT IS NEW IN test-fix-5
-------------------------
Only the download dialog changed. The UI is the complete stable v1.0.1 UI:
no layout, drawable, font, animation or watermark changes.

1) Duplicate filenames now ask first
   When a file with the same name already exists, the dialog offers
   "Generate unique name" as the positive/default action (for example
   "Title (1).mp4"). "Overwrite" is a separate neutral action on the same
   dialog. Choosing unique name must download alongside the old file;
   choosing overwrite must replace the old file.

2) No overwrite while a download is pending or running
   For Pending or Running missions the dialog informs you and only offers
   Cancel. It must never offer to overwrite an active download.

3) Finished-but-deleted downloads do not block
   Delete a finished download from the Downloads screen (keep the file if
   asked), then download the same video again. It must download normally,
   not claim the file already exists.

WHAT IS NOT IN THIS BUILD
-------------------------
The test-fix-4 Shorts brand loop and fullscreen watermark are gone. They
were removed because they changed the UI and did not render correctly on
the test device. Do not report missing branding/watermark as a bug.

Everything from v1.0.1 is still included: download-crash fix, visionOS
playback client (seek + quality), iOS stream source, dark theme, and the
#00FCFF / #F3024E seekbar.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube (v1.0.1 or test-fix-4). Do NOT uninstall the old app first (you
would lose downloads and settings). If Android says "App not installed",
stop and report it - do not uninstall.

TEST CHECKLIST (about 5 minutes)
--------------------------------
[  ] UI unchanged: open Shorts and confirm the header/back arrow looks
     exactly like v1.0.1 (a normal arrow, no text loop, no oversized
     button, title in its old position). Open a video fullscreen in
     portrait and landscape and confirm the normal bottom controls look
     unchanged, with no "T YouTube" watermark.
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
[  ] Link guide (optional): if you want it, follow the two settings
     steps in the site guide. If not, skip - links still open as before.

IF SOMETHING STILL FAILS
------------------------
Download dialog shows no working button / app freezes when tapping
Download:
   Send the video title or link, the phone model, and whether the file
   already existed. If possible, include a logcat taken while tapping
   Download. This build removed the test-fix-4 truncate helper, so a
   freeze here is new information.

Duplicate dialog does not appear at all:
   1. T YouTube settings -> Downloads -> download folder -> choose
      Internal storage (not the SD card), then retry the same video.
   2. If it still overwrites silently, send the video title/link and the
      exact dialog text you see.
   3. If it still fails, send the exact error text.

UI looks different from v1.0.1:
   Take a screenshot. This build contains no UI patches, so any difference
   means the wrong APK was installed. Check that the installed file is
   T-YouTube-fixed-test.apk from the test-fix-5 release.

ROLLBACK
--------
Install T YouTube v1.0.1 (or v1.0.0) over this build - same signature, no
data loss.
