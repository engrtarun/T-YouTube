# v1.2.0 task list

Status: `[ ]` todo, `[~]` in progress, `[x]` done, `[!]` blocked

## 0. Reconnaissance
- [x] Clone repo, add MicroG-RE submodule at 7.3.0 (`c370569`).
- [x] Pin base APK v1.0.1 + SHA-256.
- [x] Inspect manifest/smali on CI (`ci-results` branch).
- [x] Confirm base already has microG `<queries>`, spoof metadata, and a
      dangling `MicroGActivity` manifest entry.
- [x] Confirm microG package id `app.revanced.android.gms`, versionCode
      `255070304`, account type `app.revanced`.
- [x] Confirm `-noicon` disables the launcher alias only.
- [x] Confirm official microG signing cert SHA-256
      `0b6c9515afb195fac59601696ba0a7907a0b217ccf720b43148427ccf64343e7`.
- [x] Confirm Play Services coexistence (GmsCoreSupportPatch comment).
- [x] Fetch third inspection: `youtube_prefs.xml`, `main_shortcuts.xml`,
      `GmsCoreSupportPatch.checkGmsCore` body, resource IDs.
- [x] Read research report `docs/research/microg-integration.md`.

## 1. Tests first (RED)
- [x] Add `ci/test-one-app.py` with checks for:
      manifest permission/queries/alias/activity/receiver, assets and hashes,
      `classes11.dex` classes, settings preference, no-op extension patch,
      watermark values, package/version/signature, dex count.
- [x] Run it against the current tree/APK and record the expected failures.

## 2. Setup code
- [x] `setup-src/com/gold/youtube/MicroG/MicroGActivity.java`
      - welcome / checklist / permission / progress / success / error states
      - SharedPreferences flags
      - ABI pick, version check, signature-conflict handling
      - forward to MainActivity when ready
- [x] `setup-src/com/gold/youtube/MicroG/MicroGInstaller.java`
      - stream asset, SHA-256, `PackageInstaller` session, commit
- [x] `setup-src/com/gold/youtube/MicroG/InstallResultReceiver.java`
- [x] `setup-src/com/gold/youtube/MicroG/SetupPrefs.java` (persisted flags)
- [x] Keep every class framework-only (no AndroidX/Material).
- [x] Compile with `javac --release 8` + `d8` locally (~48 KB dex).

## 3. Patch scripts
- [x] `scripts/apply-one-app.py`
      - manifest: permissions, activity exported/theme, alias target, receiver
      - assets: copy pinned microG APKs + verify hashes
      - `apktool.yml`: add `apk` to `doNotCompress`
      - settings preference with `<intent>`
      - no-op `GmsCoreSupportPatch.checkGmsCore`
      - watermark 11.5sp / 0.55 and update post-conditions
- [x] Run after `apply-zversion.py`; exact-once anchors only.
- [x] Dry-run against real manifest/prefs/apktool anchors + stub smali.

## 4. CI
- [x] Download microG 7.3.0 noicon arm64 + v7, verify SHA-256.
- [x] Compile `setup-src` with `javac` + `d8` → `classes11.dex`.
- [x] Add `classes11.dex` to the rebuilt APK.
- [x] Run `ci/test-one-app.py` in the workflow.
- [x] Update existing verification greps (dex count 11, watermark values).
- [x] Keep artifact + prerelease publishing.
- [ ] First real workflow run (needs a tag push).

## 5. Docs / release
- [x] README: remove "install microG first" as a required manual step; explain
      bundled setup, one icon, Play Services coexistence, recovery.
- [x] `ci/TEST-BUILD-README.txt`: v1.2.0 what's new + device checklist.
- [x] `docs/index.html`: one-download tutorial, v1.2.0 cards, FAQ.
- [x] `ci/STABLE-RELEASE-NOTES.md` / release notes.
- [x] Update `TEST-CHANGES.md` build marker to v1.2.0.
- [ ] Close/mention issue #2 (watermark) after a successful verified build.

## 6. Build and verify
- [ ] Push `test-v1.2.0-*` tag; watch CI.
- [ ] Inspect verification report + asset hashes + dex count.
- [ ] Download artifact, check `aapt2 badging` and `apksigner`.
- [ ] Hand the device checklist to the user; cannot test on-device remotely.

## Blocked / notes
- `versionCode` is max int; same-value updates are expected to work.
- The base's `MicroGActivity` class is missing, so adding it is safe.
- The extension's `checkGmsCore` must be no-op or it opens a browser on Later.
- Do not change `GmsCoreSupportPatch` other methods; update checks are ours.
- The 212 MB base is never decoded locally; only CI does the heavy build.
