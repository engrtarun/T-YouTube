T YouTube v1.0.1 - stable update
=================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.0 (YouTube 21.26.364) - same package + versionCode
Signature: same AOSP testkey as v1.0.0, installs as an in-place update
Min Android: 10 (API 29)
Size: 222,566,961 bytes (212 MB)
SHA-256: 71B0F782702129A0DDCC80EE0A7150F52FE0099671AB62692766B1C605EBE7FE

WHAT CHANGED
------------
1) Download crash fixed (the main fix)
   Tapping Download could close the app instantly. The previous filename cap
   cut every title with substring(0, 80); for a normal title shorter than 80
   characters that call threw StringIndexOutOfBoundsException while the dialog
   was opening. Titles are now cut only when they are longer than 80 characters,
   so normal titles pass through unchanged and the dialog opens normally.

2) Downloads complete
   Filenames are cleaned with the app's filename charset before saving, and the
   built-in downloader's iOS stream source is enabled. The quality picker gets
   extra unthrottled stream URLs.

3) Seeking a long video no longer freezes playback or drops quality
   Default spoof playback client: "Android Reel" (ANDROID_REEL_AUTH) ->
   "visionOS". visionOS returns complete stream URLs with working seek and the
   full quality list, so jumps to 20+ minutes resume instead of hanging.

4) Shorts no longer stall
   Shorts use the same stream resolver, so they get the same seek/quality fix.

5) Dark theme by default
   Appearance defaults to Dark (app_theme_dark = true, Appearance = Dark).
   You can still switch to Light / Use device theme in Settings > General.

6) Seekbar in the logo colours
   Custom seekbar colours are ON by default:
     played part / primary: #00FCFF (logo cyan-green)
     accent / secondary:    #F3024E (logo red)
   You can change or disable them in Settings > Player > Seekbar.

7) Picture-in-picture kept
   Press Home while playing and the video keeps playing in a floating PiP
   window.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing T
YouTube. Do NOT uninstall the old app first - you would lose downloads and
settings. The signing key is unchanged, so Android accepts it as an update.

This is the same APK that was tested as test-fix-3. It was promoted to stable
without rebuilding, so the checksum above matches the tested build.

IF SOMETHING STILL FAILS
------------------------
A previously saved setting always wins over a new default. Check in the app:
  T YouTube settings -> General -> Appearance = Dark
  T YouTube settings -> Player -> Seekbar -> custom colours ON,
      primary #00FCFF, accent #F3024E
  T YouTube settings -> Miscellaneous -> Spoof video streams ->
      Default client = visionOS

Download still says "file not created":
  1. T YouTube settings -> Downloads -> download folder -> choose Internal
     storage (not the SD card), then retry the same video.
  2. If it works on internal storage, the SD card/folder was the problem.
  3. If it still fails, send the video title/link and the exact error text.

ROLLBACK
--------
Install the original T YouTube v1.0.0 APK over this build (same signature, no
data loss).
