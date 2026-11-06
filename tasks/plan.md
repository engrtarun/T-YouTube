# T YouTube v1.2.0 — one-app microG setup

## Objective

Ship one visible app: T YouTube. The APK bundles the official **MicroG-RE
`-noicon`** APKs and installs the right one on first run. microG stays a separate
Android package (this is unavoidable), but it has no launcher icon and the user
never has to download or install it manually.

Also fix issue #2: the fullscreen watermark is too large/bright.

## Hard constraints

- Package `com.gold.android.youtube`, versionCode `2147483647`, versionName
  `21.26.364`, and the AOSP `testkey` signature must not change. v1.2.0 must
  install over v1.1.0 with data intact.
- Do **not** compile or vendor microG source into the APK. `vendor/microg-RE`
  stays a read-only submodule. Install the official release bytes unchanged.
- No heavy APK decode/build on the maintainer machine. All decode, compile,
  sign and verification runs in GitHub Actions.
- No root, no signature-level permissions, no silent install. Android always
  shows one installer confirmation.
- Do not add a second launcher icon.

## Architecture

1. **Launcher hook without smali changes.** Retarget the existing launcher
   `activity-alias` (`com.google.android.youtube.app.honeycomb.Shell$HomeActivity`)
   to `com.gold.youtube.MicroG.MicroGActivity` (already declared in the base
   manifest, but the class is missing from the APK). The alias name stays the
   same, so the launcher component, icon and shortcuts keep working.
2. **Setup Activity in a new `classes11.dex`.** Small Java Activity compiled in
   CI with `javac` + `d8`, using framework APIs only. It checks microG, shows the
   welcome/checklist, copies the bundled asset, and drives `PackageInstaller`.
3. **Installer.** `PackageInstaller` session, 64 KB streaming copy, SHA-256
   verification, explicit mutable `PendingIntent` to an `exported="false"`
   receiver. `REQUEST_INSTALL_PACKAGES` is declared and the user grants
   "Install unknown apps" once.
4. **No extension nag.** Patch `GmsCoreSupportPatch.checkGmsCore` to a no-op so
   it cannot open a browser/download page behind the setup screen. Our Activity
   owns the check, update prompt and battery row.
5. **Re-entry.** Add a "Setup & permissions" preference to
   `res/xml/youtube_prefs.xml` with a standard `<intent>` targeting the setup
   Activity. No second activity, no shortcut hacks.
6. **Assets.** Bundle `microg-7.3.0-noicon-arm64-v8a.apk` and
   `microg-7.3.0-noicon-armeabi-v7a.apk`. Pick by `Build.SUPPORTED_ABIS`.
   Universal is a fallback only if a device has neither ABI (rare); show a clear
   unsupported message instead of shipping 107 MB extra.
7. **Spoofing.** The base manifest already declares
   `app.revanced.android.gms.SPOOFED_PACKAGE_NAME` /
   `SPOOFED_PACKAGE_SIGNATURE` and `<queries>` for the microG package. microG-RE
   reads those values; system-level signature spoofing is **not** required.
   Google Play Services can coexist; do not block setup on it.
8. **Watermark.** Reduce from 14 sp / 0.8 alpha to 11.5 sp / 0.55 alpha, keep it
   below the scrubber and tied to controls visibility.

## Acceptance criteria

### Build / identity
- `aapt2 dump badging` still reports package, versionCode and versionName above.
- `apksigner verify --print-certs` still reports testkey SHA-256
  `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc`.
- APK contains 11 dex files (`classes.dex` … `classes11.dex`).
- APK contains both microG assets under `assets/microg/` and they are stored
  uncompressed.
- `classes11.dex` contains `MicroGActivity` and the install receiver.

### Manifest
- `REQUEST_INSTALL_PACKAGES` and `REQUEST_DELETE_PACKAGES` declared.
- `<queries>` contains `app.revanced.android.gms`.
- Launcher alias targets `com.gold.youtube.MicroG.MicroGActivity`.
- Setup Activity exported; receiver not exported.
- Spoof metadata unchanged.

### Setup behaviour (static proof in CI + device checklist)
- Missing microG → welcome → permission gate → system installer → success.
- Install permission denied → in-app explanation, deep link, no crash/loop.
- User cancels installer → "Install cancelled" + retry.
- Signature mismatch → explain uninstall, offer system uninstall.
- Installed newer microG → keep it, never downgrade.
- Installed current microG → forward straight to the app.
- `Later` → open the app, set a flag, do not re-show setup automatically.
- Settings → "Setup & permissions" reopens the checklist.
- 32-bit device gets the v7 asset; arm64 gets the v8 asset.

### UI
- Brand colors, dark background, readable at 200% font scale, 48 dp targets.
- No WebView, no new bitmaps, no AppCompat/Material dependency.

### Watermark
- Both fullscreen control layouts use `11.5sp`, `alpha="0.55"`, tag
  `tyt_watermark`, and the CI greps assert the new values.

## Out of scope for v1.2.0

- True single-package microG merge (not possible on stock Android).
- Silent install / device-owner provisioning.
- Translating the new setup strings (English first).
- Changing the app package/version/signature.

## Verification strategy

- `ci/test-one-app.py` runs against the decoded tree and the built APK. It is
  written first (RED), then the implementation makes it pass (GREEN).
- GitHub Actions builds a `test-v1.2.0-*` prerelease.
- Static checks cannot prove the system installer flow; `ci/device-proof.ps1`
  and `ci/TEST-BUILD-README.txt` carry the on-device checklist.
