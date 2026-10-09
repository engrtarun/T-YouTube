<div align="center">

  <img src="assets/banner.png" width="100%" alt="T YouTube">

  ### 📦 Download

  <a href="https://github.com/engrtarun/T-YouTube/releases/latest">
    <img src="https://img.shields.io/badge/%F0%9F%93%A6%20Download%20T%20YouTube%20v1.0.0-FF1744?style=for-the-badge&logo=android&logoColor=white" alt="Download T YouTube APK">
  </a>

  <a href="https://github.com/microg/GmsCore/releases/latest">
    <img src="https://img.shields.io/badge/%F0%9F%93%A6%20microG%20GmsCore%20(required)-3DDC84?style=for-the-badge&logo=google-play&logoColor=white" alt="microG GmsCore download">
  </a>

  <br><br>

  [![Version](https://img.shields.io/github/v/release/engrtarun/T-YouTube?style=flat-square&label=Version&color=FF1744)](https://github.com/engrtarun/T-YouTube/releases/latest)
  [![Downloads](https://img.shields.io/github/downloads/engrtarun/T-YouTube/total?style=flat-square&label=Downloads&color=2563EB)](https://github.com/engrtarun/T-YouTube/releases)
  [![Android](https://img.shields.io/badge/Android-10%2B-3DDC84?style=flat-square&logo=android&logoColor=white)](https://developer.android.com/)
  [![Size](https://img.shields.io/badge/APK-214%20MB-8B5CF6?style=flat-square)](https://github.com/engrtarun/T-YouTube/releases/latest)
  [![microG](https://img.shields.io/badge/powered%20by-microG-34A853?style=flat-square&logo=google-play&logoColor=white)](https://github.com/microg/GmsCore)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](#-contributing)

  <sub>
    <a href="https://github.com/engrtarun/T-YouTube/releases/latest/download/T-YouTube-v1.0.0.apk">Direct download · T-YouTube-v1.0.0.apk</a>
  </sub>

</div>

---

**YouTube, minus the noise.** A cleaned-up, fully rebranded build with the
startup ad/promo popups removed — nothing else added, nothing else touched.

<img src="assets/feature-strip.png" width="100%" alt="Startup popup removed · 82 locales rebranded · 5 densities icon rebuilt">

---

## 📸 Screenshots

> These are designed placeholder tiles. Replace the `.png` files in
> `assets/screenshots/` with your real captures (same filenames, `.jpg` is fine).

| Home | Player |
|:--:|:--:|
| <img src="assets/screenshots/home.png" width="230" alt="Home screen"> | <img src="assets/screenshots/player.png" width="230" alt="Player screen"> |

| Settings | Downloads |
|:--:|:--:|
| <img src="assets/screenshots/settings.png" width="230" alt="Settings showing T YouTube Settings"> | <img src="assets/screenshots/downloader.png" width="230" alt="Downloads screen"> |

**The money shot** — fresh install, first launch, no promo dialog:

<img src="assets/screenshots/no-popup.png" width="260" alt="First launch with no promo popup">

---

## ✨ What this build changes

This is **not** a feature-addition fork. It is a *cleanup and rebrand* of
**YT Pro v59** — three deliberate changes, nothing else.

| # | Change | Details |
|:-:|:--|:--|
| 1 | 🧹 **Startup ad/promo popup removed** | The mod fetches a remote JSON from a third-party server and pops an affiliate/promo dialog on every launch. Both code paths are stubbed to `return-void` at the entry point — no network request, no dialog, no background thread. |
| 2 | ✏️ **Full rebrand** | Every `YouTube Pro` string replaced with `T YouTube` across **all 82 locales**, plus settings screens and the launcher label. Zero occurrences of the old branding remain in the APK. |
| 3 | 🎨 **New icon set** | Purpose-built launcher icon built to the official Android adaptive-icon spec. |

**Not changed:** the package name, version code, or any patch/feature logic.
This build upgrades in place over the original and keeps your data, logins and
watch history.

---

## 🎨 The icon

The previous icon was drawn at ~82 dp wide on a 108 dp canvas. Android only ever
shows a **72 dp** window of that canvas — so the neon ring was clipped by every
launcher mask. It looked broken.

This one is built to spec:

```
Canvas          108 dp
Masked window    72 dp   ← what the launcher actually shows
Safe zone        66 dp   ← artwork is fitted inside this circle, always
```

Built and previewed against circle, squircle and rounded-square masks at all
five densities (`mdpi` → `xxxhdpi`), plus the legacy square bitmap and the
Android 13+ **themed icon** (previously still showing the YouTube play glyph).

---

## 📋 Requirements

| | |
|:--|:--|
| **Android** | 10.0 (API 29) or newer |
| **Architecture** | `arm64-v8a`, `armeabi-v7a`, `x86`, `x86_64` — universal APK |
| **Google Play Services** | ❌ **Not required — and must not be active.** T YouTube runs on **microG**, which cannot coexist with Google Play Services. |
| **microG** | ✅ **Required.** See below. |
| **Free storage** | ~350 MB (app + data) |

---

## 📥 Installation

### Step 1 — Install microG first

microG **GmsCore** provides the Google Play Services APIs YouTube needs.
T YouTube declares these in its manifest, and microG reads them to grant the
app its identity:

```
app.revanced.android.gms.SPOOFED_PACKAGE_NAME      = com.google.android.youtube
app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE = 24bb24c0…
```

Install GmsCore from the official releases (don't take APKs from random sites):

> **https://github.com/microg/GmsCore/releases/latest**
>
> On a stock device grab **`com.google.android.gms-*.apk`**.
> Huawei/EMUI devices use the `-hw` variant. microG is **GPLv3** — if you
> redistribute it, you must also offer its source.

> ⚠️ Already using **Google Play Services**? It must be **disabled/uninstalled**
> first. microG will not install alongside it, and it will not work if Play
> Services is still active.

### Step 2 — Enable signature spoofing

```
microG Settings → Signature spoofing → enable for T YouTube
```

Without this the app installs but sign-in, playback and most API calls fail.

### Step 3 — Install T YouTube

1. Download `T-YouTube-v1.0.0.apk` from the link at the top
2. Open it — allow **"Install unknown apps"** for your file manager/browser
3. Tap **Install**

---

## ⚠️ Upgrading from an older YT Pro build

Android refuses to install an update signed with a **different key**. T YouTube
is signed with the same AOSP `testkey` certificate that YT Pro v59 uses, so it
installs **directly over** it — no uninstall, your data stays.

```
package        com.gold.android.youtube
versionCode    2147483647
signature      SHA-256  a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc
```

### If you get `App not installed as package conflicts with an existing package`

That message means a **differently-signed** copy of the same package is already
installed. Common causes:

| Situation | What to do |
|:--|:--|
| A YT Pro build signed with a modder's own key | Uninstall it first (⚠️ clears app data) |
| A build signed with a random debug key | Uninstall it first |
| Any other fork of `com.gold.android.youtube` | Uninstall it first |

Reinstalling **this** build after that, and staying on this build for all future
updates, avoids the problem entirely.

---

## ❓ FAQ

<details>
<summary><b>Can it run alongside the official YouTube?</b></summary>

Yes. T YouTube uses the package `com.gold.android.youtube`, while the official
YouTube is `com.google.android.youtube`. Different packages — both can be
installed side by side. In practice though, YouTube needs microG and Play
Services cannot coexist with microG, so you will usually want only one.
</details>

<details>
<summary><b>Does this remove in-video ads?</b></summary>

It removes the **mod's own startup promo/affiliate popup**. In-stream
advertising is served by YouTube's servers and is a separate matter.
</details>

<details>
<summary><b>Why does it say "MicroG Not Installed"?</b></summary>

microG GmsCore is not running, or signature spoofing is off. Go back to
Steps 1–2 above.
</details>

<details>
<summary><b>Can I update later without losing data?</b></summary>

Yes — as long as future updates keep the same signing key, Android treats them
as an in-place update. Never re-sign with a random debug key; that is the single
most common cause of the conflict error above.
</details>

<details>
<summary><b>Why was this signed with the AOSP test key?</b></summary>

Because that is the key the original YT Pro v59 is signed with, and Android
requires a matching key to install over an existing app. The AOSP `testkey`
certificate is a publicly published test certificate from the Android Open
Source Project — it is not a secret, and it grants no special privileges.
</details>

<details>
<summary><b>Is this safe?</b></summary>

It is a modified YouTube client. It is not distributed by, affiliated with, or
endorsed by Google. See [Legal](#-legal--disclaimer).
</details>

---

## 🧪 Technical details

| Property | Value |
|:--|:--|
| Package name | `com.gold.android.youtube` |
| Version name | `21.26.364` |
| Version code | `2147483647` |
| Min SDK | 29 (Android 10) |
| Target SDK | 37 |
| APK size | 224,578,294 bytes (214 MB) |
| Entry count | 16,830 |
| Signature scheme | APK Signature Scheme **v3** |
| Signing certificate | AOSP `testkey` — `CN=Android, O=Android, L=Mountain View, ST=California, C=US` |
| Cert SHA-256 | `a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc` |
| Cert SHA-1 | `61ed377e85d386a8dfee6b864bd85b0bfaa5af81` |

### Verify before you install

```powershell
# signature
apksigner verify --print-certs T-YouTube-v1.0.0.apk

# checksum
Get-FileHash T-YouTube-v1.0.0.apk -Algorithm SHA256
```

**SHA-256 for v1.0.0**

```
82146CDBDE17D5213C5CFF75415DCCCA4C3C5A1A19D2B4DF347E07A5C7A42A71
```

---

## 🔨 How it was built

```
YT Pro v59 (original APK)
        │
        ├─ apktool 2.9.3  d  →  decode to smali + res
        │
        ├─ patch ①  com.apksam.task.DevMsg.showMessage()  → return-void
        ├─ patch ②  com.sammods4h.task.DevMsg.show()      → return-void
        │            (both are the remote-config promo dialog entry points)
        │
        ├─ patch ③  res/values*/strings.xml  →  83 files, "YouTube Pro" → "T YouTube"
        ├─ patch ④  adaptive + legacy + themed icons rebuilt to spec
        ├─ patch ⑤  in-app action-bar logo → T mark
        │
        ├─ apktool 2.9.3  b  →  rebuild
        ├─ zipalign -p -f 4
        └─ apksigner sign --ks testkey.p12   (AOSP testkey, scheme v3)
```

The rebuild was verified **byte-identical across all 10 `classes*.dex` files**
versus the known-good build, confirming the runtime patches survived reassembly.

---

## 👤 Author

<table>
<tr><td align="center">
  <a href="https://github.com/engrtarun"><img src="https://github.com/engrtarun.png" width="72" height="72" alt="engrtarun"></a><br>
  <a href="https://github.com/engrtarun"><b>@engrtarun</b></a>
</td><td align="center">
  <a href="https://github.com/engrtarundilwal"><img src="https://github.com/engrtarundilwal.png" width="72" height="72" alt="engrtarundilwal"></a><br>
  <a href="https://github.com/engrtarundilwal"><b>@engrtarundilwal</b></a>
</td></tr>
</table>

---

## 🤝 Contributing

Issues and pull requests are welcome — especially translations, bug reports with
logs, and icon refinements for other launcher shapes.

Please do **not** open issues for ad-blocking or account problems; those are
server-side / microG-side concerns.

---

## ⚖️ Legal & Disclaimer

T YouTube is an **unofficial, community-made modification** of the YouTube
Android client. It is not affiliated with, endorsed by, sponsored by, or
otherwise connected to Google LLC or YouTube.

- "YouTube" is a trademark of Google LLC. The name is used here only to describe
  what this software is a modification of.
- The APK contains copyrighted Google code and is published for educational and
  interoperability purposes only.
- **No source code is provided for the YouTube client itself.** The original
  authors and copyright holders retain all rights to it.
- microG is a separate project licensed under **GPLv3** and is *not* bundled or
  redistributed here — you download it from
  [microg/GmsCore](https://github.com/microg/GmsCore).
- You are responsible for complying with the laws in your jurisdiction.

---

## 🙏 Credits

| | |
|:--|:--|
| **YT Pro v59** | The base build this is forked from — the patch set, downloader and feature work are theirs |
| **microG** | The open-source Google Play Services replacement this runs on — [microg/GmsCore](https://github.com/microg/GmsCore) |
| **apktool** | Used for decode / patch / rebuild — [iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool) |
| **Android Open Source Project** | The `testkey` signing certificate is a publicly published AOSP test certificate |
| **You** | For the bug reports and translations |

---

<div align="center">
  <sub>
    Not affiliated with Google ·
    <a href="https://github.com/engrtarun/T-YouTube/issues">Report an issue</a> ·
    <a href="https://github.com/engrtarun/T-YouTube/releases">All releases</a>
  </sub>
</div>