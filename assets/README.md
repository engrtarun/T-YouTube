# `assets/` — image manifest

Everything here is referenced from [`README.md`](../README.md).

## Branding ✅

| File | Size | Used for |
|:--|:--|:--|
| `banner.png` | 1280×320 | README hero image (top of page) |
| `og-image.png` | 1200×630 | GitHub social preview card — repo **Settings → General → Social preview** |
| `feature-strip.png` | 1200×200 | The three-changes strip under the intro |
| `logo.png` | 512×512 | Repo avatar (Settings → General → Avatar) |
| `icon-256.png` | 256×256 | Smaller avatar / docs use |
| `logo-adaptive.png` | 512×512 | Unmasked 108 dp adaptive icon — Play Store / F-Droid listings |

## Screenshots ✅ (real captures)

| File | Size | What it proves |
|:--|:--|:--|
| `screenshots/player.jpg` | 1640×720 | Landscape player — download button, SponsorBlock and Return-YouTube-Dislike all visible in one frame |
| `screenshots/settings.jpg` | 720×1640 | **Rebrand proof** — toolbar reads *T YouTube*; full YT Pro patch menu intact |
| `screenshots/download.jpg` | 720×1640 | Downloader works — quality picker from 144p to 1080p60 |
| `screenshots/browse.jpg` | 720×1640 | Watch screen — playback, comments, music player |

All from a real device running the v1.0.0 build.

## Still wanted 📸

| Capture | How to get it |
|:--|:--|
| `screenshots/no-popup.jpg` | The headline feature. Uninstall (or clear app data), install fresh, then screenshot **within the first seconds of first launch** — no promo dialog should appear. Crop to the top of the screen where the dialog used to sit. |
| `screenshots/home.jpg` | The Home feed. Add it once you have a shot you like; it fills out the browse row. |

Drop the file in and add one `<img>` line to the README table.

## Regenerating

If the icon changes, re-run the generators so everything stays in sync:

```powershell
python tools\brand_icons.py   # launcher / themed / action-bar icons inside the APK tree
python tools\repo_art.py      # banner, og-image, feature-strip, logo
```