# T YouTube v1.1.0 — stable update

Shorts branding, the fullscreen watermark, and the download confirm button are
now the recommended stable build. Every change here was first shipped as the
`test-zversion-4` build and verified with a `git diff` against v1.0.1.

## What changed

- **Shorts show the T YouTube brand loop, on every Shorts page.** The top-left
  back control cycles every 8 seconds: arrow → 225 ms crossfade → **T YouTube**
  → 225 ms crossfade → arrow. The whole 128x48 dp strip is one Back target and
  the title does not move. Root cause of the old stuck arrow: Shorts had **two**
  views with the same `reel_back_button` id — the non-video and survey pages
  `<include>` a second layout that still shipped the plain white arrow, so
  `findViewById()` could hand the player that arrow instead of the loop. Both
  layouts now carry the loop, and the animation restarts once the view really
  has window focus, so it can no longer freeze on the opening arrow.
- **Tapping the toolbar download button actually starts the download again.**
  The current v1.0.1 state machine (`checkSelectedDownload`) is restored byte
  for byte and only gains the duplicate handling below — the same method that
  already worked in stable v1.0.1.
- **Automatic duplicate naming — no user effort.** Downloading the same title
  again just works: the app runs its own `createUniqueFile()` and starts
  downloading `Title (1).mp4` immediately. No prompt, no extra tap, no
  overwrite. The download dialog also opens with the **real video title**
  instead of the literal `download`.
- **Pending and Running downloads are never overwritten.** They show an
  information dialog with only a Cancel button, and an entry whose file was
  deleted can be downloaded again.
- **Fullscreen watermark is smaller and lower.** A subtle 14 sp bold **T YouTube**
  wordmark (32 dp) anchored to the **bottom of the control row, below the
  scrubber line**, hidden in sync with the controls. Portrait and landscape,
  fullscreen controls only, not clickable, no layout shift, absent inline /
  PiP / Shorts.
- **Build marker.** The About screen shows `21.20.402 (v1.1.0)` so the
  installed build is easy to identify. The app version stays `21.26.364`.

## Everything in v1.0.1 is kept

Download crash on short titles, completing downloads, seeking long videos at
the chosen quality, non-stalling Shorts, dark theme by default, auto-brightness,
PiP default, notification channels, and the theme colours.

## Install

- **Size:** 222,584,140 bytes (212.3 MiB)
- **SHA-256:** `337f55a17c8fdd1ae458a4ab9e76ca3bd1335c3865ca0bb5de055fd078496d5c`
- Same package (`com.gold.android.youtube`), version code and AOSP testkey
  signature as v1.0.1, so it installs **over** v1.0.1 with data intact.

Install the APK as an update — do **not** uninstall the old app first.

## Rollback

Install [v1.0.1](https://github.com/engrtarun/T-YouTube/releases/download/v1.0.1/T-YouTube-v1.0.1.apk)
over it. Same signature, no data loss.

## If something fails

Phone model, Android version, a screenshot/recording and the exact step. If
you ran `scripts/device-proof.ps1`, send the whole `proof/<timestamp>` folder.
