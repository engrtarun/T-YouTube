# `assets/` — image manifest

Everything here is referenced from [`README.md`](../README.md).
Generated with Pillow — no design tool needed.

## Ready to use ✅

| File | Size | Used for |
|:--|:--|:--|
| `banner.png` | 1280×320 | README hero image (top of page) |
| `og-image.png` | 1200×630 | GitHub social preview card — set via repo **Settings → General → Social preview** |
| `feature-strip.png` | 1200×200 | The three-changes strip under the intro |
| `logo.png` | 512×512 | Repo avatar (GitHub → Settings → General → Avatar) |
| `icon-256.png` | 256×256 | Smaller avatar / docs use |
| `logo-adaptive.png` | 512×512 | Unmasked 108 dp adaptive icon — for Play Store / F-Droid listings |

## Placeholder tiles — replace these ⚠️

`screenshots/*.png` are **designed placeholders**, not real captures. They keep
the README looking finished until you have real screenshots, but a public repo
should show the real thing.

Delete the `.png` and drop in your own capture with the same base name:

| Placeholder | Replace with | What to capture |
|:--|:--|:--|
| `screenshots/home.png` | `home.jpg` | Home feed |
| `screenshots/player.png` | `player.jpg` | Watch/player screen |
| `screenshots/settings.png` | `settings.jpg` | ⚙️ Settings showing **"T YouTube Settings"** — proof of the rebrand |
| `screenshots/downloader.png` | `downloader.jpg` | Downloads screen — proof the base patch set still works |
| `screenshots/no-popup.png` | `no-popup.jpg` | **Fresh install → first launch → no promo dialog.** The headline feature. |

Then update the `<img src>` paths in `README.md` from `.png` to `.jpg`.

**Screenshot tips**
- Capture on the highest-resolution device you have, then downscale to ~1080 px wide.
- Use JPG quality 80–85 — PNG screenshots of dark UI get large for no benefit.
- Turn off developer option *Show taps*; hide notification content.
- Crop out the status bar clock if it shows anything personal.
- `no-popup.jpg` matters most: clear app data (or uninstall first), install, then
  capture within the first few seconds of first launch.

## Regenerating

If you change the icon, re-run the generator and everything stays in sync:

```powershell
python tools\repo_art.py
```