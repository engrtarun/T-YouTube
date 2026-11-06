T YouTube v1.2.0 test build (one-app setup)
============================================

Package: com.gold.android.youtube
Base: T YouTube v1.0.1 (YouTube 21.26.364)
Signature: same AOSP testkey as v1.0.1, installs as an in-place update
Min Android: 10 (API 29)
APK size: (filled in by CI)
SHA-256: (filled in by CI)

WHAT IS NEW IN v1.2.0
---------------------
One visible app. Open T YouTube and a short setup screen installs the official
MicroG-RE 7.3.0 -noicon APK that is already inside the T YouTube APK. No
separate microG download, no file manager, no second launcher icon.

Two Android packages are still installed. This is an Android rule, not a
choice: a normal app cannot merge another app's services into itself. microG's
launcher icon is hidden, so the phone shows only T YouTube.

1) First-run setup
   Welcome -> Start setup -> microG install -> notifications (optional) ->
   battery (optional) -> done. Every screen has Later, and the flow never
   loops or re-opens a denied system prompt.

2) Bundled microG
   microg-7.3.0-noicon-arm64-v8a.apk for 64-bit phones and
   microg-7.3.0-noicon-armeabi-v7a.apk for 32-bit phones. The app picks by
   Build.SUPPORTED_ABIS, verifies SHA-256 while streaming into Android's
   PackageInstaller, and installs the official bytes unchanged. Android still
   shows its one normal installer confirmation.

3) Settings -> Setup & permissions
   The row sits above About. It reopens the checklist in manage mode after a
   skipped setup or a later microG uninstall.

4) No old browser redirect
   The extension's checkGmsCore() is now a no-op. It used to open
   https://morphe.software/microg when microG was missing, which would fight
   the new setup screen.

5) Issue #2: fullscreen watermark
   Now 11.5sp at 0.55 alpha (was 14sp at 0.8). Still below the scrubber line,
   tied to controls visibility, and absent inline/PiP/Shorts.

6) Build marker
   About now shows "Play Store Version 21.26.364 (v1.2.0)". The package,
   versionCode (2147483647), versionName and testkey signature are unchanged.

HOW TO INSTALL
--------------
Open the APK on the phone and install it as an update over the existing
T YouTube v1.0.1 / v1.1.0 build. Do NOT uninstall the old app first (you would
lose downloads and settings). If Android says "App not installed", stop and
report it - do not uninstall.

If microG was already installed and working, the setup screen is skipped
automatically.

TEST CHECKLIST
--------------
[ ] Install over v1.1.0 without uninstalling; logins, settings and downloads
    are still there.
[ ] If microG was already installed: opening T YouTube goes straight to the
    app, with no welcome screen.
[ ] Fresh install (or after uninstalling microG): the welcome screen appears.
[ ] Start setup shows the checklist; microG row says Install.
[ ] Tap Install. Android asks for "Install unknown apps" for T YouTube once.
[ ] Return from that screen: the install continues automatically.
[ ] Android's installer appears once. Tap Install.
[ ] After install: checklist shows "microG installed." and Continue is enabled.
[ ] Notifications row: Turn on shows the Android prompt once; denying does not
    loop. The row then offers Open settings.
[ ] Battery row: Allow opens the system exemption screen (or the battery list
    on phones that do not support the direct dialog).
[ ] Continue -> success -> Open T YouTube. Video playback and sign-in work.
[ ] Later path: from the checklist, tap Later. The app opens. Relaunching does
    not show the welcome screen again.
[ ] Settings -> Setup & permissions reopens the checklist in manage mode.
[ ] Installed microG current: microG row shows Installed, no update prompt.
[ ] Simulate a signature mismatch (install a differently-signed microG build):
    the error explains it and offers Uninstall microG.
[ ] Unsupported ABI (x86-only emulator): "This phone isn't supported." appears
    before any install attempt.
[ ] microG icon: the launcher shows only T YouTube. microG settings are
    reachable from T YouTube's existing MicroG row and from Setup & permissions.
[ ] Watermark: show fullscreen controls; T YouTube is faint and small
    (11.5sp / 0.55), below the scrubber. Hide controls: it disappears with them.
[ ] Inline/PiP/Shorts: no watermark.
[ ] Downloads and Shorts loop still work (v1.1.0 regression checks).

KNOWN LIMITS
------------
- Android always shows one installer confirmation. Silent install needs root
  or device-owner provisioning.
- x86-only devices are not supported by the bundled arm microG. Use the
  universal build from the release page.
- Setup strings are English-only in this test build.
- microG remains a separate package; only its icon is hidden.

IF SOMETHING FAILS
------------------
Send the phone model, Android version, a screenshot/recording, and the exact
step. Include whether microG was already installed before the test. Setup logs
use the "TytSetup" tag:
  adb logcat -d -s TytSetup:V

ROLLBACK
--------
Install T YouTube v1.1.0 or v1.0.1 over this build - same signature, no data
loss. The hidden microG package can be removed from Android Settings -> Apps.
