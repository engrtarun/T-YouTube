T YouTube fixed TEST build
==========================

Package: com.gold.android.youtube
Base: T YouTube v1.0.0 (YouTube 21.26.364) - same package + versionCode
Signature: same AOSP testkey as v1.0.0, installs as an in-place update
Min Android: 10 (API 29)

WHAT CHANGED (3 default values only - no new menus, no new buttons)
-------------------------------------------------------------------
1) Picture-in-Picture / miniplayer
   Default miniplayer type: "Minimal" (custom overlay) -> "Default" (stock YouTube miniplayer).
   Pressing Home while a video plays now shrinks it into PiP like stock YouTube.

2) Playback: stalls after seeking, quality stuck low, weak-network handling
   Default spoof playback client: "Android Reel" (ANDROID_REEL_AUTH) -> "Android VR 1.64".
   Google has broken the Reel client (buffering every few seconds, missing quality menu,
   forced 360p, seek jumps back). Android VR is the client family Morphe switched to as
   its default in July 2026 and restores the quality menu + adaptive quality.
   Fallback order: Android VR -> Android Creator -> TV -> visionOS.

3) In-app downloads
   Enabled the iOS stream source in the built-in NewPipe-based downloader
   (the setFetchIosClient(true) behaviour stock NewPipe enables but this fork never did).
   The download quality list now gets extra, unthrottled stream URLs.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing T YouTube.
Do NOT uninstall the old app first (you would lose downloads/settings).
If Android says "App not installed", stop and report it - do not uninstall.

TEST CHECKLIST (about 5 minutes)
--------------------------------
[  ] PiP: play a video, press Home (or swipe up on gesture nav). The video should shrink
     to a floating PiP window and keep playing.
[  ] Download: open a video -> Download button -> pick a quality -> download completes and
     the file plays from the downloads screen.
[  ] Seek: play a 1080p video, seek forward/back several times (+10s/-10s and drag the bar).
     Playback should continue without freezing or jumping back.
[  ] Quality: on Wi-Fi open a video -> gear icon -> quality menu is present, lists 1080p
     (and 1440p/2160p when the upload has it), and auto-selects high quality after a few seconds.
[  ] Watch 2-3 minutes normally: no repeating 2-3 second buffering loop.

IF SOMETHING STILL FAILS
------------------------
A previously saved setting always wins over a new default. Check in the app:
  T YouTube settings -> Miniplayer -> Miniplayer type = Default
  T YouTube settings -> Miscellaneous -> Spoof video streams -> Default client = Android VR
Changing those two values has exactly the same effect as this build's new defaults.

ROLLBACK
--------
Install the original T YouTube v1.0.0 APK over this build (same signature, no data loss).
