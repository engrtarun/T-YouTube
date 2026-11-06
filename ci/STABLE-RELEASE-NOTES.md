# T YouTube v1.2.0 — one app, microG included

T YouTube now installs microG for you. The official MicroG-RE 7.3.0 `-noicon`
APKs ship inside the T YouTube APK; first launch shows a short setup screen,
picks the build for your phone, verifies it and hands it to Android's installer.
One download, one icon.

## What changed

- **First-run setup.** Welcome → checklist → install → done. Every screen has
  **Later**, and relaunching does not loop. The microG APK is streamed from the
  bundled asset and checked against its pinned SHA-256 while it is written.
- **One visible icon.** microG stays a separate Android package because Android
  cannot merge it into another app, but its launcher alias is disabled. Only
  T YouTube appears in the app drawer.
- **Already have microG?** The app opens straight into YouTube, even when the
  installed microG is older. **Settings → Setup & permissions** offers the
  update when you want it.
- **No surprise browser.** The extension's old `checkGmsCore()` opened the
  microG download page when the service was missing. It is now a no-op, so
  nothing can pop up behind the setup screen.
- **Issue #2 fixed.** The fullscreen watermark is now **11.5 sp at 0.55 alpha**
  (was 14 sp at 0.8). It stays below the scrubber line, still hides with the
  controls, and is still absent inline, in PiP and in Shorts.
- **Build marker.** About shows `21.26.364 (v1.2.0)`. The app version stays
  `21.26.364`; the package, version code and AOSP testkey signature are
  unchanged.

## Everything in v1.1.0 is kept

The Shorts brand loop on every Shorts page, the working toolbar download
button, automatic duplicate naming, and every v1.0.1 playback, download and
theme fix.

## Install

- **Size:** 311,639,792 bytes (297.2 MiB)
- **SHA-256:** `7f43429321d918957dede2dad2d96f1b47c68a42c6e2a5cc1315ab2a4eee74f2`
- Same package (`com.gold.android.youtube`), version code (`2147483647`) and
  AOSP testkey signature as v1.1.0, so it installs **over** v1.1.0 with data
  intact. Install it as an update — do **not** uninstall the old app first.

Android shows one installer confirmation for microG the first time. That is
normal. The APK is already inside T YouTube and nothing is downloaded.

## Rollback

Install [v1.1.0](https://github.com/engrtarun/T-YouTube/releases/download/v1.1.0/T-YouTube-v1.1.0.apk)
(or v1.0.1) over it. Same signature, no data loss. You can remove the hidden
microG package from Android Settings → Apps at any time.

## If something fails

Send the phone model, Android version, a screenshot or recording, and the exact
step. For setup problems, include what the microG row says. For the watermark,
include fullscreen portrait and landscape with the controls shown. If you ran
`scripts/device-proof.ps1`, send the whole `proof/<timestamp>` folder.
