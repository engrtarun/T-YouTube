# `tools/` — build & patch scripts

Everything needed to reproduce the rebrand from a stock **YT Pro v59** APK.
This folder is documentation, not a turnkey one-command build — each script
targets a stage of the pipeline.

## Pipeline order

| # | Stage | Script | What it does |
|:-:|:--|:--|:--|
| ① | Patch | *(manual)* | Decode with apktool, then stub `com.apksam.task.DevMsg.showMessage()` and `com.sammods4h.task.DevMsg.show()` to `return-void` — these are the two remote-config promo dialog entry points |
| ② | Patch | `relabel_locales.ps1` | Rewrites the app label across every locale |
| ③ | Patch | *(manual)* | Replace `YouTube Pro` → `T YouTube` in `res/values*/strings.xml` (83 files) |
| ④ | Art | `generate_icons.ps1` | Generates the source launcher-icon set from the logo |
| ④ | Art | `apply_icons.ps1` | Writes those icons into the decoded `res/mipmap-*` tree |
| ④ | Art | `brand_icons.py` | **Rewrites** adaptive / legacy / themed / action-bar icons to the 108-72-66 dp adaptive-icon spec |
| ④ | Art | `fix_wordmarks.py` | Rebuilds the **40 in-app wordmark PNG/WebP** files — the old *"YouTube Pro"* header was baked into *pixels*, so no text search can find it. Reads the original geometry from each asset and re-renders the T mark + "T YouTube" at the same size |
| ⑤ | Build | apktool | `apktool b` → `zipalign -p -f 4` → `apksigner sign` |
| ⑥ | Docs | `repo_art.py` | Generates the README banner, social-preview card, feature strip and logo |

## Why so many scripts

Each one exists because a *different* layer of the app carries the old brand:

| Layer | Carried as | Fixed by |
|:--|:--|:--|
| Launcher label | `strings.xml` | `relabel_locales.ps1` |
| In-app settings text | `strings.xml` | manual string pass |
| Launcher icon | PNG layers | `brand_icons.py` |
| Themed icon | `VectorDrawable` XML | `brand_icons.py` |
| Action-bar logo | WebP | `brand_icons.py` |
| **App header wordmark** | **pixels inside PNG/WebP** | **`fix_wordmarks.py`** |

## Running them

```powershell
# 1. decode
java -jar apktool.jar d YTPro-v59.apk -o dec59

# 2. artwork (point at your decoded tree)
python tools\brand_icons.py
python tools\fix_wordmarks.py

# 3. rebuild + sign
java -jar apktool.jar b dec59 -o unsigned.apk
zipalign -p -f 4 unsigned.apk aligned.apk
apksigner sign --ks testkey.p12 --ks-type PKCS12 --ks-pass pass:android `
    --key-pass pass:android --ks-key-alias testkey `
    --min-sdk-version 21 --out signed.apk aligned.apk
```

> **The signing key matters.** The key here is the publicly published
> **AOSP `testkey`** — the same certificate YT Pro v59 uses. Android refuses to
> update an app signed with a different key, so signing with a random debug key
> produces *"App not installed as package conflicts with an existing package"*.
> Keep `testkey.p12` somewhere safe; **it is not in this repo** (see `.gitignore`).

## README artwork

```powershell
python tools\repo_art.py
```