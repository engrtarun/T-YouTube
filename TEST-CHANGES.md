# T YouTube — test build change log

This file lists every change that was made in the test builds, including the
one build that was withdrawn. Stable releases are listed at the end for
reference.

| Build | Status | Base | What it was for |
|:--|:--|:--|:--|
| `test-fix-1` | Superseded | v1.0.0 | PiP default, playback client, iOS download source |
| `test-fix-2` | Superseded | v1.0.0 | visionOS playback, filename cleanup, dark theme, seekbar colours |
| `test-fix-3` | **Promoted to v1.0.1** | v1.0.0 | Fixed the download dialog crash on short titles |
| `test-fix-4` | **Withdrawn — release and tag deleted** | v1.0.0 + v1.0.1 fixes | Shorts brand loop, fullscreen watermark, download dialog rework |
| `test-fix-5` | Superseded | v1.0.0 + v1.0.1 fixes | Download dialog only; complete stable v1.0.1 UI |
| `test-zversion-1` | Superseded | stable v1.0.1 | Shorts brand loop, fullscreen watermark, download dialog fix |
| `test-zversion-2` | **Current optional test build** | stable v1.0.1 | Fixed Shorts loop, both-layout watermark, automatic duplicate naming |

Stable **v1.0.1 remains the recommended download**. Test builds are optional
and are published as GitHub prereleases.

---

## test-zversion-2 - Zversion 1 fixes (current)

**Release:** https://github.com/engrtarun/T-YouTube/releases/tag/test-zversion-2

This build keeps the Zversion 1 feature set but fixes why the first attempt did
not appear on the phone, and restores automatic duplicate naming. It is still
decoded from the **published v1.0.1 APK**, and stable v1.0.1 is untouched.

### 1. Shorts brand loop now starts reliably

- The 8-second loop, 128x48 dp strip and 65 dp title anchor are unchanged.
- The custom view now restarts the `AnimationDrawable` when the **whole
  header** becomes visible, using `onVisibilityAggregated`, `onLayout` and
  `onWindowVisibilityChanged` fallbacks.
- Zversion 1 only reacted to the button's own visibility change. The Shorts
  controller makes the button visible while its parent header is still `GONE`,
  so the start could be skipped and never retried.
- The animation still stops when the header is detached or hidden, and the
  whole strip remains one Back target with the same content description.

### 2. Fullscreen watermark is in both bottom-control layouts

- The app chooses between `youtube_controls_bottom_ui_container.xml` and
  `youtube_video_exploder_controls_bottom_ui_container.xml` at runtime via
  `LegacyPlayerControlsPatch.usePlayerBottomControlsExploderLayout()`.
- Zversion 1 patched only the legacy layout. Devices with "Restore old player
  buttons" off use the exploder layout, so the watermark was never inflated.
- Zversion 2 patches **both** layouts with the same 18 sp bold white 80%
  wordmark, constrained between the timestamps and `bottom_end_container`.
- It is still a child of the controls, so it hides with them, and it remains
  absent inline, in PiP/miniplayer and in Shorts.

### 3. Duplicate downloads are automatic again

- The broken **Generate unique name** button and the
  `ZVersionDownloadUniqueAction` class are removed.
- A finished duplicate now silently calls the app's own
  `StoredDirectoryHelper.createUniqueFile()`, so a second file is saved as
  `Title (1).mp4` with no dialog and no extra tap.
- Pending and Running missions still show an information-only dialog and are
  never overwritten.
- A finished mission whose file was deleted is still forgotten and downloaded
  again normally.

### Build

- Base APK: **stable v1.0.1**
  (`T-YouTube-v1.0.1.apk`, SHA-256
  `71B0F782702129A0DDCC80EE0A7150F52FE0099671AB62692766B1C605EBE7FE`)
- Patch: `scripts/apply-zversion.py` only
- CI: GitHub Actions `.github/workflows/build-test-apk.yml`
- APK: `T-YouTube-Zversion.apk`
- Package: `com.gold.android.youtube`
- Version: `21.26.364` / versionCode `2147483647`
- Signature: AOSP `testkey` (same as v1.0.1)

### Verify

- APK size and SHA-256 are published on the release page.
- Test checklist: `ci/TEST-BUILD-README.txt`.

---

## test-zversion-1 — Shorts, fullscreen and download (superseded)

**Release:** https://github.com/engrtarun/T-YouTube/releases/tag/test-zversion-1

This is a separate Zversion test build decoded from the **published v1.0.1
APK**, not from v1.0.0. Stable v1.0.1 is untouched. The package name,
version code, version name and AOSP testkey signature are unchanged, so it
installs over v1.0.1 with data intact.

### 1. Shorts brand loop

- The top-left Shorts back control is now a custom 128×48 dp strip.
- It loops every 8 seconds: arrow 4.8 s → 225 ms crossfade → “T YouTube”
  2.75 s → 225 ms crossfade → arrow.
- The whole strip is one Back target; tapping the arrow, the wordmark or the
  empty space goes Back.
- The video title is pinned at its old 65 dp start position and does not move.
- The animation starts only when the real header view is attached and visible,
  and stops when it is detached. TalkBack content description is unchanged.

### 2. Fullscreen watermark

- Adds a custom “T YouTube” view to the actual bottom control row
  (`youtube_controls_bottom_ui_container`), not the usually-hidden quick
  actions container.
- 18 sp bold YouTube Sans, overlay primary text colour, alpha 0.8.
- Constrained between the left time controls and the right-side “More videos”
  button, so it cannot overlap or resize a control.
- Gated by the real fullscreen container (`fullscreen_mode_container`) when the
  player is reparented, with a player-overlay-height fallback for other
  fullscreen modes. Because it is a child of the controls, it hides with the
  controls, and it is absent inline, in PiP/miniplayer and in Shorts.
- Not clickable, not focusable, `importantForAccessibility="no"`.

### 3. Download dialog

- Duplicate filename: **Generate unique name** is the positive/default action
  (for example `Title (1).mp4`).
- **Overwrite** is a separate neutral action on the same dialog.
- Pending and Running missions show an informational dialog with Cancel only;
  they never offer Overwrite.
- Finished mission with a deleted file: the stale mission is forgotten and the
  file is created again, so re-download works.
- The normal folder flow, the Save-as single-URI flow, and the directory+URI
  flow are handled separately; the old overloaded `v0` state machine was
  replaced.
- No `SafeTruncate` helper and no UI-thread delete/recreate path.

### Build

- Base APK: **stable v1.0.1**
  (`T-YouTube-v1.0.1.apk`, SHA-256
  `71B0F782702129A0DDCC80EE0A7150F52FE0099671AB62692766B1C605EBE7FE`)
- Patch: `scripts/apply-zversion.py` only
- CI: GitHub Actions `.github/workflows/build-test-apk.yml`
- APK: `T-YouTube-Zversion.apk`
- Package: `com.gold.android.youtube`
- Version: `21.26.364` / versionCode `2147483647`
- Signature: AOSP `testkey` (same as v1.0.1)

### Verify

- APK size **222,584,227 bytes (212 MB)**; SHA-256
  `4CD565F46672C9651AFB77831F7A8C2420A684D2F08E9098CB6C4B78D76A1F22`.
- Test checklist: `ci/TEST-BUILD-README.txt`.

---

## test-fix-5 — download dialog only (superseded)

**Release:** https://github.com/engrtarun/T-YouTube/releases/tag/test-fix-5

This build exists because test-fix-4 changed the UI and broke the download
flow. test-fix-5 restores the **complete stable v1.0.1 UI** and changes only
the duplicate-name download dialog.

### UI

- No layout, drawable, font, animation, colour or watermark changes.
- Shorts header, fullscreen controls, titles and every other screen are the
  stable v1.0.1 UI.

### Download dialog

- **Duplicate filenames ask first.** When a file with the same name already
  exists, the dialog opens instead of silently reusing or overwriting it.
- **Generate unique name is the positive/default action.** For example
  `Title (1).mp4`. Pressing the normal confirm action creates a second file
  alongside the old one.
- **Overwrite is a separate neutral action.** It is not the default and is
  only shown when overwriting makes sense.
- **Pending and Running downloads never offer Overwrite.** They show the
  status message and only a Cancel action.
- **Finished downloads use the same explicit choice.** A finished mission
  whose file was deleted no longer blocks a new download: the overwrite path
  forgets the stale mission and continues.
- **No crash when the download directory is missing.** The dialog falls back
  to an informational message instead of starting a unique-name action that
  cannot work.

### Removed from test-fix-4

- Shorts “T YouTube” brand loop.
- Fullscreen “T YouTube” watermark.
- The extra `SafeTruncate` helper (a possible UI-thread freeze path).
- The separate stale-mission patch (the normal overwrite path now handles it).
- All branding drawables and runtime layout patches are not applied.

### Included from v1.0.1

Everything in stable v1.0.1: download-dialog crash fix, visionOS playback
client, iOS stream source, dark theme by default, and the `#00FCFF` /
`#F3024E` seekbar.

### Build

- Base APK: v1.0.0
- Patches: `scripts/apply-fixes.py` + `scripts/apply-test-fix-5.py`
- CI: GitHub Actions run `41034902281`, commit `7da51e1`
- Package: `com.gold.android.youtube`
- Version: `21.26.364` / versionCode `2147483647`
- Signature: AOSP `testkey` (same as v1.0.0 and v1.0.1)

### Verify

- APK: `T-YouTube-fixed-test.apk`
- Size: **222,566,961 bytes** (212 MB)
- SHA-256: `4AE3F2D8B26B3869B21A6B17B0C588095626BCF7C6362883F98AC97B63370A0D`

The APK size matches v1.0.1 because only smali code changed.

---

## test-fix-4 — withdrawn

**Status:** release and tag deleted. Do not install this build.

This was an optional preview that added a new look on top of v1.0.1. It was
withdrawn after testing because the UI looked broken and downloads lagged or
froze.

### What was planned

1. **Shorts “T YouTube” brand loop**
   - The back arrow in the Shorts header was supposed to cycle through an
     8-second animation: arrow → crossfade → “T YouTube” → crossfade → arrow.
   - The whole 128×48 dp strip was supposed to stay a single Back target, so
     tapping the words would still go back.
   - The video title was supposed to stay pinned in its old position.

2. **Fullscreen “T YouTube” watermark**
   - A static wordmark centred in the bottom action row, between the left
     controls and “More videos”.
   - Visible in portrait and landscape fullscreen, only while the controls
     were shown.
   - Not clickable and hidden with the controls.

3. **Download dialog rework**
   - Duplicate filenames default to **Generate unique name**.
   - **Overwrite** as a separate explicit action, hidden while a download was
     Pending or Running.
   - Finished-but-deleted missions forgotten instead of blocking a re-download.
   - `SafeTruncate` helper to recover from a failed truncate with
     delete + recreate.

4. **Optional YouTube link guide**
   - Documentation-only guide to make `youtube.com` links open in T YouTube.
   - No app or package-name change.

### Why it was withdrawn

- The Shorts and watermark patches targeted wrong or unused runtime layouts,
  so the branding did not appear on the real surfaces.
- The download dialog used one overloaded layout (`v0`), so the new
  unique/overwrite buttons were usually unreachable and some dialogs showed
  only Cancel.
- The app lagged or froze when tapping Download. The `SafeTruncate` and
  stale-mission changes were unnecessary risk on the UI thread and were
  removed.
- The UI did not match stable v1.0.1 and looked broken.

The release and tag were deleted so the build cannot be downloaded by mistake.
Its changes are **not** part of test-fix-5.

---

## test-fix-3 — became stable v1.0.1

**Status:** promoted unchanged to v1.0.1. The published v1.0.1 APK is the exact
file testers installed as test-fix-3.

### Change

- **Fixed the download dialog crash on short titles.**
  - test-fix-2 added an 80-character filename cap, but the comparison was
    inverted: titles of 80 characters or fewer still went through
    `substring(0, 80)`, which threw `StringIndexOutOfBoundsException` as soon
    as the dialog opened.
  - The cap now applies only when the title is actually longer than 80
    characters.
  - The surrogate regex was removed; titles are still cleaned with the app's
    filename charset before saving.

### Included from earlier builds

- visionOS playback client (seek and quality).
- iOS stream source for downloads.
- Dark theme by default.
- `#00FCFF` / `#F3024E` seekbar colours.
- PiP behaviour from test-fix-1.

---

## test-fix-2

**Status:** superseded by test-fix-3 / v1.0.1.

### Changes

1. **Default playback client: Android Reel → visionOS**
   - visionOS returns complete stream URLs with working seek and a full
     quality list.
   - Jumps to 20+ minutes resume at the selected quality instead of freezing
     and dropping to 144p/360p.
   - Shorts use the same resolver, so the 1–2 minute stall was fixed too.

2. **Versioned spoof-client setting key**
   - The default was stored under a new key
     (`youtube_spoof_video_streams_client_type_v2`) so existing installs pick
     up visionOS instead of keeping the old saved value.
   - A follow-up change pointed the settings UI
     (`youtube_prefs*.xml`) at the same versioned key.

3. **Download filename cleanup**
   - Titles are trimmed and cleaned with the app's filename charset.
   - Empty names fall back to `download`.
   - Names are capped at 80 characters, keeping the extension.
   - The first implementation of the cap was inverted; test-fix-3 fixed it.

4. **Dark theme by default**
   - `app_theme_dark = true` and Appearance = Dark.
   - Light / Use device theme can still be selected in Settings → General.

5. **Seekbar in the logo colours**
   - Custom seekbar colours enabled by default:
     - played part / primary: `#00FCFF` (logo cyan-green)
     - accent / secondary: `#F3024E` (logo red)
   - Colours sampled from the official T YouTube logo.
   - Can be changed in Settings → Player → Seekbar.

---

## test-fix-1

**Status:** superseded by later builds. Its PiP behaviour is kept in v1.0.1.

### Changes (three defaults only — no new menus or buttons)

1. **Picture-in-Picture / miniplayer**
   - Default miniplayer type: `MINIMAL` (custom overlay) → `DEFAULT` (stock
     YouTube miniplayer).
   - Pressing Home while a video plays now shrinks it into a floating PiP
     window and keeps playing.

2. **Spoof playback client: Android Reel → Android VR 1.64**
   - Android Reel was buffering every few seconds, missing the quality menu,
     forcing 360p and jumping back on seek.
   - Android VR restored the quality menu and adaptive quality.
   - Later changed to visionOS in test-fix-2.

3. **iOS stream source for downloads**
   - Enabled `setFetchIosClient(true)` in the built-in downloader.
   - The download quality list gets extra, unthrottled stream URLs.

---

## Stable v1.0.1

**Release:** https://github.com/engrtarun/T-YouTube/releases/tag/v1.0.1

Recommended download. It is the exact APK that passed testing as test-fix-3,
promoted without rebuilding.

- APK: `T-YouTube-v1.0.1.apk`
- Size: **222,566,961 bytes** (212 MB)
- SHA-256: `71B0F782702129A0DDCC80EE0A7150F52FE0099671AB62692766B1C605EBE7FE`
- Package: `com.gold.android.youtube`
- Version: `21.26.364` / versionCode `2147483647`
- Signature: AOSP `testkey`

---

## Install and rollback

All builds use the same package name, version code and AOSP `testkey`
signature, so they install in place over v1.0.0, v1.0.1 and any test build.

1. Download the APK on the phone.
2. Open it and install as an **update**.
3. Do **not** uninstall the old app first — you would lose downloads, logins
   and settings.
4. If Android says “App not installed”, stop and report it instead of
   uninstalling.

**Rollback:** install v1.0.1 over the test build. No data is lost.

---

## How the test APKs are built

The CI workflow is `.github/workflows/build-test-apk.yml`.

1. Download the v1.0.0 base APK and verify its SHA-256.
2. Decode with apktool 2.11.1.
3. Apply `scripts/apply-fixes.py` (the v1.0.1 fixes).
4. Apply `scripts/apply-test-fix-5.py` (download dialog only).
5. Rebuild, zipalign and sign with the AOSP `testkey`.
6. Verify the APK, then publish it as a prerelease when the pushed tag matches
   `test-fix-*`.

Every patch replacement must match exactly once. If the upstream dialog
changes, the build fails instead of shipping a half-patched APK.

---

*T YouTube is an unofficial community modification. Not affiliated with,
endorsed by, or connected to Google LLC or YouTube.*
