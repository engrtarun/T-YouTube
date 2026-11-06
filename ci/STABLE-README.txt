T YouTube v1.2.0 - one app, microG included
==========================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364) - same package + versionCode
Signature: same AOSP testkey as v1.1.0, installs as an in-place update
Min Android: 10 (API 29)
Size: 311,639,792 bytes (297.2 MiB)
SHA-256: 7f43429321d918957dede2dad2d96f1b47c68a42c6e2a5cc1315ab2a4eee74f2

WHAT CHANGED
------------
1) One download, one icon
   microG-RE 7.3.0 -noicon is inside the T YouTube APK for arm64-v8a and
   armeabi-v7a. First launch opens a short setup screen, picks the build for
   the phone, verifies it and hands it to Android's installer. There is no
   second file to download and no second launcher icon.

2) Bundled bytes, checked while streaming
   The microG APK is never unpacked into memory or re-signed. The app streams
   the asset into a PackageInstaller session, computes SHA-256 as it writes,
   and refuses to commit if the size or digest does not match. The pinned
   values come from the official MorpheApp/MicroG-RE 7.3.0 release.

3) Setup, later
   Welcome -> checklist (microG / notifications / battery) -> done. Every
   screen has Later, and relaunching does not loop. Settings > Setup &
   permissions reopens the same checklist in manage mode if setup was skipped
   or microG was later removed. If microG is already installed and enabled,
   the app opens straight into YouTube, even when the installed build is older;
   the manage screen then offers the update.

4) Issue #2 - watermark
   The fullscreen T YouTube mark is 11.5sp at 0.55 alpha (was 14sp at 0.8).
   It stays below the scrubber line, still hides with the controls through
   onVisibilityChanged, and is still absent inline, in PiP and in Shorts.
   Not clickable, no layout shift.

5) No surprise browser
   The extension's checkGmsCore() used to open https://morphe.software when
   microG was missing. It is now a no-op, so nothing can open behind setup.

6) Build marker
   About shows "Play Store Version 21.26.364 (v1.2.0)". The app version stays
   21.26.364. Package, versionCode (2147483647) and the AOSP testkey signature
   are unchanged.

EVERYTHING IN v1.1.0 IS KEPT
----------------------------
- Shorts brand loop on every Shorts page, including the second layout with
  the same reel_back_button id.
- Toolbar download button starts the download; duplicate names are automatic.
- Every v1.0.1 playback, download, Shorts and theme fix.

FIRST-RUN CHECKLIST (please test on the phone)
----------------------------------------------
[ ] Installs over v1.1.0 as an update; logins, watch history and downloads
    are still there.
[ ] Only one app icon appears in the drawer. microG has no icon.
[ ] First launch shows the setup screen, not the YouTube home feed.
[ ] Start setup -> Install -> Android shows one installer confirmation.
[ ] After Install, the checklist turns green and Open T YouTube works.
[ ] Force-stop and relaunch: it opens YouTube directly, no welcome loop.
[ ] Settings > Setup & permissions opens the checklist in manage mode.
[ ] Fullscreen portrait and landscape: watermark is small and faint, below
    the scrubber, and disappears with the controls.
[ ] Inline, PiP and Shorts show no watermark.
[ ] Airplane mode: setup still installs microG, because nothing is downloaded.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube v1.1.0 (or any test build). Do NOT uninstall the old app first
(you would lose downloads and settings). If Android says "App not installed",
stop and report it - do not uninstall.

Android will ask once for "Install unknown apps" for T YouTube during setup.
That is Android's normal confirmation for installing the bundled microG.

ROLLBACK
--------
Install T YouTube v1.1.0 over this build - same signature, no data loss.
https://github.com/engrtarun/T-YouTube/releases/download/v1.1.0/T-YouTube-v1.1.0.apk
The hidden microG package can be removed from Android Settings > Apps.

IF SOMETHING FAILS
------------------
Send the phone model, Android version, a screenshot/recording and the exact
step. For setup, include what the microG row says and the Android installer
message. For the watermark, include fullscreen portrait and landscape with
controls shown. If you ran scripts/device-proof.ps1, send the whole
proof/<timestamp> folder.
