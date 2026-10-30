T YouTube fixed TEST build (test-fix-3)
=======================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.0 (YouTube 21.26.364) - same package + versionCode
Signature: same AOSP testkey as v1.0.0, installs as an in-place update
Min Android: 10 (API 29)

WHAT CHANGED (defaults + bug fixes - no new menus, no new buttons)
-----------------------------------------------------------------
1) Download button force-closed the app (test-fix-2 regression - fixed)
   test-fix-2 added filename cleanup that cut every title at 80 characters.
   For a normal title shorter than 80 characters that cut was invalid and the
   download dialog crashed the moment it opened. Titles are now cut only when
   they are actually longer than 80 characters, so normal titles pass through
   unchanged and the dialog opens normally.

2) Seeking a long video froze playback, then only low quality played
   Default spoof playback client: "Android Reel" (ANDROID_REEL_AUTH) -> "visionOS".
   visionOS returns complete stream URLs with working seek and full quality
   list, so jumps to 20+ minutes no longer hang and quality is not forced down.

3) Shorts stalled for 1-2 minutes, then resumed in low quality
   Same client change as (2): Shorts use the same stream resolver, so they get
   the same seek/quality fix.

4) In-app downloads: extra stream source
   Enabled the iOS stream source in the built-in NewPipe-based downloader
   (the setFetchIosClient(true) behaviour stock NewPipe enables but this fork
   never did). The download quality list now gets extra, unthrottled stream URLs.

5) Dark theme by default
   Appearance defaults to Dark (app_theme_dark = true, Appearance = Dark).
   You can still switch to Light / Use device theme in Settings > General.

6) Seekbar in the logo colours
   Custom seekbar colours are now ON by default:
     played part / primary: #00FCFF (logo cyan-green)
     accent / secondary:    #F3024E (logo red)
   Colours were sampled from the official T YouTube logo.
   You can change or disable them in Settings > Player > Seekbar.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing T YouTube.
Do NOT uninstall the old app first (you would lose downloads/settings).
If Android says "App not installed", stop and report it - do not uninstall.

TEST CHECKLIST (about 8 minutes)
--------------------------------
[  ] Download dialog (the main fix): tap Download on a normal video with a
     short title. The dialog must open (the app must NOT close) and show the
     quality list. Pick a quality; the download must complete, appear in
     Downloads, and play from there.
[  ] Download a video whose title has emoji and is longer than 80 characters.
     It must also open the dialog and download normally.
[  ] Download a second normal video, to be sure repeated downloads still work.
[  ] Long seek: play a 30+ minute 1080p video, drag the bar to ~23:00 (or use
     the +10s button repeatedly). Playback should resume in a few seconds with
     the quality you selected - no 2-8 minute freeze, no forced 144p/360p.
[  ] Quality: gear icon -> quality menu is present and lists 1080p (1440p/2160p
     when the upload has it). Changing quality takes effect immediately.
[  ] Shorts: swipe through 10-15 Shorts. No 1-2 minute stall; if one buffers it
     should recover quickly at normal quality.
[  ] Theme: on first launch after install the app should be dark. Check
     Settings > General > Appearance = Dark.
[  ] Seekbar: play any video. The progress bar should be cyan/green (#00FCFF)
     with a red (#F3024E) accent, not the old pink/red gradient.
[  ] PiP: play a video, press Home. It should shrink to a floating PiP window
     and keep playing (kept from test-fix-1).

IF SOMETHING STILL FAILS
------------------------
A previously saved setting always wins over a new default. Check in the app:
  T YouTube settings -> General -> Appearance = Dark
  T YouTube settings -> Player -> Seekbar -> custom colours ON,
      primary #00FCFF, accent #F3024E
  T YouTube settings -> Miscellaneous -> Spoof video streams -> Default client = visionOS
Changing those values has exactly the same effect as this build's new defaults.

Download button closes the app again:
   Send the video title/link and the exact step where it closes. That means
   the filename crash fix did not cover your title, and a log is needed.

Download still says "file not created":
  1. T YouTube settings -> Downloads -> download folder -> choose Internal storage
     (not the SD card), then retry the same video.
  2. If it works on internal storage, the SD card/folder was the problem.
  3. If it still fails, send the video title/link and the exact error text.

ROLLBACK
--------
Install the original T YouTube v1.0.0 APK over this build (same signature, no data loss).
