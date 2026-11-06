# MicroG-RE 7.3.0 → T YouTube integration note

**Status:** research only. No build, no Gradle, no APK decoding, no commits.
**Source of truth:** `vendor/microg-RE` at `c370569f63376ec857fb0707ff8ec6a66a56507d` (tag `7.3.0`, clean tree) and the GitHub release `MorpheApp/MicroG-RE@7.3.0`.
**Bottom line:** bundle the official **`microg-7.3.0-noicon-arm64-v8a.apk`** (45,648,640 B / 43.53 MiB), stream it from `assets/` into a `PackageInstaller` session, and expect **one** system install confirmation. No system-level signature spoofing is required.

---

## 1. Package and SDK metadata

| Field | Value | Source |
|---|---|---|
| Application ID | `app.revanced.android.gms` | `play-services-core/build.gradle:142`, `build.gradle:8` |
| Java namespace | `com.google.android.gms` (code only, not the installed package) | `build.gradle` (`applicationNamespace`) |
| versionName | `7.3.0` | `build.gradle:109` |
| versionCode | `255070304` (fits in `int`; read `longVersionCode`) | `build.gradle:108`, `play-services-core/build.gradle:134` |
| minSdk | `21` (Android 5.0) | `build.gradle:45` |
| targetSdk | `34` (Android 14) | `build.gradle:46` |
| compileSdk | `36` | `build.gradle:47` |
| Account type | `app.revanced` | `play-services-core/build.gradle:161`, `res/xml/authenticator.xml` |
| App label | `MicroG RE` (both icon and noicon builds) | `res/values/strings.xml:7`, `play-services-core/build.gradle:149` |
| ABI filters (source build) | `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64` | `play-services-core/build.gradle:177-184` |
| `android:multiArch` | `true` | `play-services-core/src/main/AndroidManifest.xml:224` |

The installed package is **not** `com.google.android.gms`; that is only the Java namespace inherited from upstream GmsCore.

## 2. Release assets

Latest stable release is `7.3.0`, published `2026-10-31T08:21:08Z`. The `/releases/latest` endpoint skips prereleases; a newer `7.3.1-dev.1` prerelease exists (`2026-11-04`) and is not a target.

| Asset | ABI | Launcher icon | Bytes | MiB | URL |
|---|---|:--:|---:|---:|---|
| `microg-7.3.0.apk` | all | yes | 113,086,836 | 107.85 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0.apk` |
| `microg-7.3.0-noicon.apk` | all | no | 113,086,836 | 107.85 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0-noicon.apk` |
| `microg-7.3.0-icon-arm64-v8a.apk` | arm64-v8a | yes | 45,648,640 | 43.53 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0-icon-arm64-v8a.apk` |
| `microg-7.3.0-noicon-arm64-v8a.apk` | arm64-v8a | no | 45,648,640 | 43.53 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0-noicon-arm64-v8a.apk` |
| `microg-7.3.0-icon-armeabi-v7a.apk` | armeabi-v7a | yes | 43,445,006 | 41.43 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0-icon-armeabi-v7a.apk` |
| `microg-7.3.0-noicon-armeabi-v7a.apk` | armeabi-v7a | no | 43,445,006 | 41.43 | `https://github.com/MorpheApp/MicroG-RE/releases/download/7.3.0/microg-7.3.0-noicon-armeabi-v7a.apk` |

Icon and noicon assets are the same size because they differ only in one manifest placeholder and one bool resource. All six are built from the same tag with the same key, so `versionCode` is identical across variants. License: Apache-2.0 (keep the upstream notice when redistributing).

## 3. Manifest declarations

### 3.1 Host app (T YouTube)

| Declaration | Value | Why |
|---|---|---|
| `<queries><package>` | `app.revanced.android.gms` | Package visibility for `getPackageInfo()` on API 30+. Without it the setup says "not installed" even when it is. |
| `<queries><package>` | `com.google.android.gms` | Only for the Play Services blocker check (T YouTube specific). |
| `<queries><package>` | `com.mgoogle.android.gms`, `org.microg.gms` | Only if you replicate the conflict detection from the Morphe patch. |
| `<uses-permission>` | `android.permission.REQUEST_INSTALL_PACKAGES` | Required to drive `PackageInstaller`. |
| `<uses-permission>` | `android.permission.REQUEST_DELETE_PACKAGES` | Required to uninstall a conflicting microG via `PackageInstaller.uninstall` (targetSdk 28+). |
| `<meta-data>` | `app.revanced.android.gms.SPOOFED_PACKAGE_NAME` = `com.google.android.youtube` | Tells microG which Google app the caller is a fork of. |
| `<meta-data>` | `app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE` = `24bb24c05e47e0aefa68a58a766179d9b613a600` | SHA-1 of YouTube's signing cert. Note: **SHA-1, 40 hex chars** — not the SHA-256 used for update checks. |
| `<meta-data>` | `app.revanced.MICROG_PACKAGE_NAME` = `app.revanced.android.gms` | Written by the Morphe patch. No reader exists in MicroG-RE 7.3.0 or the current extension; harmless, not load-bearing. |

Manifest snippet:

```xml
<queries>
    <package android:name="app.revanced.android.gms" />
    <package android:name="com.google.android.gms" />
</queries>
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
<uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES" />

<application ...>
    <meta-data android:name="app.revanced.android.gms.SPOOFED_PACKAGE_NAME"
               android:value="com.google.android.youtube" />
    <meta-data android:name="app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE"
               android:value="24bb24c05e47e0aefa68a58a766179d9b613a600" />
</application>
```

### 3.2 microG APK

Nothing to add. The bundled APK already declares its own services, providers and permissions. The host only needs to bind/query these names:

| Kind | Name | Source |
|---|---|---|
| Service action | `app.revanced.android.gms.common.service.START` | manifest (services) |
| Service action | `app.revanced.android.gms.auth.service.START` | `AndroidManifest.xml:644-645` |
| Service action | `app.revanced.android.gms.auth.api.signin.service.START` | `AndroidManifest.xml:700` |
| Service action | `app.revanced.android.gms.checkin.BIND_TO_SERVICE` | `AndroidManifest.xml:338-339` |
| Service action | `app.revanced.android.gms.accounts.ACCOUNT_SERVICE` | manifest |
| Provider | `content://app.revanced.android.gsf.gservices/prefix` | `AndroidManifest.xml:309` |
| Account type | `app.revanced` | `res/xml/authenticator.xml` |
| Settings UI | `app.revanced.android.gms/org.microg.gms.ui.SettingsActivity` (exported alias) | `AndroidManifest.xml:977-988` |

Important: the **dex** must also be rewritten. The Morphe patch replaces every `com.google.android.gms…` service action/authority string with `app.revanced.android.gms…` and `com.google` with `app.revanced`; otherwise `bindService()` targets a component that does not exist. The full set lives in `shared/misc/gms/GmsCoreSupportPatch.kt` (`Constants.PERMISSIONS`, `ACTIONS`, `AUTHORITIES`). A manifest-only integration will look correct and fail at runtime.

## 4. Signature spoofing

**Not required for this build.** Three separate mechanisms are easy to confuse:

1. **Package rename (this is the one that matters).** The APK installs as `app.revanced.android.gms`, so Android never has to pretend it is `com.google.android.gms`. ROM support for `FAKE_PACKAGE_SIGNATURE` is irrelevant.
2. **Caller-declared identity.** `PackageSpoofUtils` reads `SPOOFED_PACKAGE_NAME` / `SPOOFED_PACKAGE_SIGNATURE` from the calling app's own `<meta-data>` (unverified metadata, no OS check) and `PackageUtils.firstSignatureDigest()` substitutes that digest. This is why the patched YouTube manifest carries the two meta-data entries.
3. **microG's self-identity.** microG's own manifest declares `SPOOFED_PACKAGE_SIGNATURE=38918a453d07199354f8b19af05ec6562ced5788` (`AndroidManifest.xml:233-235`), which equals `Constants.GMS_PACKAGE_SIGNATURE_SHA1`. That makes its own self-checks and `isGooglePackage()` calls pass without a ROM patch.

Consequences:

- The microG self-check will report signature spoofing as OK even on stock; the `fake-signature` module is only for ROMs that define the permission.
- There is **no per-app "allow signature spoofing" toggle** in 7.3.0 (only Huawei ROMs get a special button in the login assistant). The "enable signature spoofing for T YouTube" step in the current README is obsolete for MicroG-RE and should be removed or reworded.
- Hardcoding `com.google.android.youtube` as the spoofed name is what makes microG treat the fork as a Google app (`PackageUtils.isGooglePackage`). Any package ending in `.youtube` is also hardcoded to `GOOGLE_APP_KEY` (`PackageUtils.java:181-182`), so T YouTube's `com.gold.android.youtube` would pass even without the metadata — do not rely on that accident.

## 5. Install permission and install flow

### 5.1 Permission

- Declare `android.permission.REQUEST_INSTALL_PACKAGES`. AOSP declares it `signature|appop`; ordinary apps hold it and the real gate is the per-app "install unknown apps" app-op.
- API 26+: check `PackageManager.canRequestPackageInstalls()`. If false, open `Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES` with `package:<host>` and re-check in `onResume`. microG's own updater does exactly this (`AppUpdater.kt:588-609`).
- Do **not** trust the toggle after returning; re-query the package manager (the design doc already requires this).

### 5.2 Session

```java
var params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
params.setSize(assetSize);
params.setInstallLocation(PackageInfo.INSTALL_LOCATION_AUTO);
// optional, see 5.4:
// params.setRequestUpdateOwnership(true);              // API 34+
// params.setRequireUserAction(SessionParams.USER_ACTION_NOT_REQUIRED); // API 31+
int id = installer.createSession(params);
try (var session = installer.openSession(id);
     var out = session.openWrite("base.apk", 0, assetSize);
     var in = assets.open("microg/microg-7.3.0-noicon-arm64-v8a.apk")) {
    in.transferTo(out);
    session.fsync(out);
}
session.commit(PendingIntent.getBroadcast(...).getIntentSender());
```

Streaming straight from `assets/` avoids a temp file; the session still stages a full copy under `/data/app-staging`, so budget roughly **2× the APK size** (~90 MB) during install. The design doc's 250 MB headroom is sufficient.

### 5.3 Status handling

- `STATUS_PENDING_USER_ACTION` → read `EXTRA_INTENT` and `startActivity()`; this is the single system confirmation.
- `STATUS_SUCCESS` → re-query `getPackageInfo()`; do not assume the broadcast is the last word.
- `STATUS_FAILURE_ABORTED` → user cancelled.
- `STATUS_FAILURE_BLOCKED` → permission / Play Protect / device policy.
- `STATUS_FAILURE_INCOMPATIBLE` → wrong ABI, downgrade, or signature conflict; read `EXTRA_STATUS_MESSAGE` for the exact `INSTALL_FAILED_*` code.
- `STATUS_FAILURE_INVALID`, `STATUS_FAILURE_CONFLICT`, `STATUS_FAILURE_STORAGE` map to damaged asset, existing install, no space.

### 5.4 What cannot be silent

Android requires user action unless **all** of these hold (`PackageInstaller.SessionParams.setRequireUserAction` docs):

- `USER_ACTION_NOT_REQUIRED` is set (API 31+);
- the package being installed targets API 29+ on Android 12, 30+ on 13, 31+ on 14, 33+ on 15, 34+ on 16 (thresholds rise over time);
- the installer is the update owner (when enforcement is on), the installer of record (when it is off), or is updating itself;
- the installer declares `UPDATE_PACKAGES_WITHOUT_USER_ACTION`.

A fresh microG install is never an update, so **the prompt is unavoidable**. `INSTALL_PACKAGES` is `signature|privileged` and is not available to a sideloaded app.

Optional improvement: call `setRequestUpdateOwnership(true)` and declare `ENFORCE_UPDATE_OWNERSHIP` **on the first install** (API 34+, only takes effect on initial install). Later updates bundled in T YouTube releases can then install without a prompt. microG updating itself remains allowed.

## 6. noicon behaviour

- Build flag `-PnoIcon=true` sets `launcherIconEnabled=false` and `resValue bool hide_launcher_icon_available=true` (`play-services-core/build.gradle:147-158`).
- The launcher entry is an `activity-alias` `org.microg.gms.ui.SettingsActivityLauncher` with `android:enabled="${launcherIconEnabled}"` (`AndroidManifest.xml:960-975`). The noicon APK ships it **disabled at install time**, so launchers never list it and no first-launch refresh race exists.
- The icon resource stays in the APK. The app remains visible in **Settings → Apps → MicroG RE**, which is required for recovery and uninstall.
- The noicon build exposes a Settings toggle; `toggleLauncherIconVisibility()` calls `setComponentEnabledSetting(DISABLED|ENABLED, DONT_KILL_APP)` (`SettingsFragment.kt:221-235`).
- The icon build's same toggle does **not** hide anything locally: it offers to download the noicon APK and install it (`AppUpdater.kt:188-283`), which needs network and the install permission.
- icon → noicon is an in-place update (same package, same key, same `versionCode`), so data and accounts survive and the icon disappears after the update. Explicit per-component state set by the user survives package updates, so a user who re-enabled the alias keeps it.
- The host **cannot** hide another app's alias: `CHANGE_COMPONENT_ENABLED_STATE` is signature/privileged. Offer the update, not a toggle.

## 7. Coexistence with genuine GMS

Technically they coexist: different package, different UIDs, different provider authorities (`app.revanced.*` vs `com.google.*`), different account type (`app.revanced` vs `com.google`). The Morphe extension deliberately does **not** treat Google Play services as a conflict and comments that "genuine Google Play services coexists with MicroG-RE without any problem" (`GmsCoreSupportPatch.java:96-103`).

What actually breaks when both are enabled:

- The patched dex points every `com.google.android.gms…` string at `app.revanced…`, but any hardcoded or dynamically loaded Google integration (Cast, Play Integrity, some SDKs) still reaches real GMS.
- microG accounts live under type `app.revanced`; anything asking `AccountManager` for `com.google` sees nothing.
- Two GMS-sized background stacks cost RAM and battery, and push/registration paths can disagree.
- Play Integrity / SafetyNet still fail either way.

So keep the design doc's `PLAY_SERVICES_ACTIVE` blocker: warn and deep-link to disable GMS, but do not claim the install is impossible. The only true incompatibility is installing microG **as** `com.google.android.gms`, which replaces the package and cannot coexist with real GMS.

Separate from GMS: `com.mgoogle.android.gms` and `org.microg.gms` are real conflicts (same services under a different package) and should block or be uninstalled first.

## 8. Update implications

- Official release signing cert SHA-256: `0b6c9515afb195fac59601696ba0a7907a0b217ccf720b43148427ccf64343e7` (`GmsCoreSupportPatch.java:85-90`; the comment says it was verified against 7.1.x APKs, so re-verify for 7.3.0 with `apksigner`).
- Same package + same key → normal update, microG data and accounts kept.
- Different key under the same package (e.g. a self-built microG, or ReVanced GmsCore) → `INSTALL_FAILED_UPDATE_INCOMPATIBLE`; the only fix is uninstall, which deletes microG accounts. The extension detects this and offers "uninstall all users".
- Downgrade → `INSTALL_FAILED_VERSION_DOWNGRADE` (PackageInstaller reports `STATUS_FAILURE_INCOMPATIBLE` with that message). Always compare `longVersionCode` and skip when installed ≥ bundled.
- Installer detection:

```java
var info = pm.getPackageInfo("app.revanced.android.gms", PackageManager.GET_SIGNING_CERTIFICATES);
boolean official = sha256(info.signingInfo.getApkContentsSigners()[0].toByteArray())
        .equals("0b6c9515afb195fac59601696ba0a7907a0b217ccf720b43148427ccf64343e7");
long installed = info.getLongVersionCode();
```

- Two update paths exist: the host bundles a floor version, and microG updates itself from `https://github.com/MorpheApp/MicroG-RE/releases/latest/download/microg-<ver>-noicon-arm64-v8a.apk` (`AppUpdater.kt:244-253`). The Morphe extension additionally polls `releases/latest` and shows an "update available" dialog. Do not run all three: let microG self-update, and have the host only install when its bundled `versionCode` is higher.
- Bumping the bundled asset in a later T YouTube release is a normal app update. If microG is already newer, leave it alone.
- Building microG from `vendor/microg-RE` yourself produces a different key. That build cannot update official installs or be updated by them, and the extension will report a conflict. Bundle the official asset.

## 9. ABI recommendation

microG runs as its own process, so only the device ABI matters — not the ABI YouTube was extracted for. But the bundled asset must cover every device the host APK supports. The current T YouTube base APK is universal (222,566,961 B / 212.26 MiB; `arm64-v8a`, `armeabi-v7a`, `x86`, `x86_64`).

| Bundle | Added | Resulting APK | Covers |
|---|---:|---:|---|
| `noicon-arm64-v8a` | +43.53 MiB | 255.79 MiB (+20.5%) | 64-bit ARM phones (essentially all phones since ~2017) |
| `noicon-armeabi-v7a` | +41.43 MiB | 253.69 MiB (+19.5%) | 32-bit ARM only |
| both ARM assets | +84.97 MiB | 297.22 MiB (+40.0%) | all ARM devices |
| `noicon` universal | +107.85 MiB | 320.10 MiB (+50.8%) | ARM + x86/x86_64 (emulators, some Chromebooks) |

**Recommendation:** bundle **`microg-7.3.0-noicon-arm64-v8a.apk`** in the standard build. It covers the realistic phone fleet and adds 20% instead of 51%. At runtime, pick the asset from `Build.SUPPORTED_ABIS`; if no bundled ABI matches, show the existing `UNSUPPORTED_ABI` state and link to the release page (do not attempt a partial install).

Add the v7a asset only if a 32-bit-only build is actually needed; do not bundle the universal APK (it buys x86 support that only emulators use). For emulator testing, use an arm64 system image or a debug flavor that bundles the universal asset. Wrong-ABI installs fail with `INSTALL_FAILED_NO_MATCHING_ABIS`.

## 10. Open items

- Confirm the `-arm64-v8a` asset contains only `lib/arm64-v8a` (check at build time with `aapt`/`unzip -l`; not done here).
- Re-verify the official signing cert SHA-256 against the 7.3.0 APK (`apksigner verify --print-certs`); the extension constant was last verified on 7.1.x.
- Reword the README's "enable signature spoofing in microG" step; it does not apply to the `app.revanced` build.
- Decide whether T YouTube claims update ownership (`setRequestUpdateOwnership`) on first install, or leaves updates to microG's own updater.

## Sources

Local (submodule `vendor/microg-RE`):
`build.gradle`, `play-services-core/build.gradle`, `play-services-core/src/main/AndroidManifest.xml`, `play-services-core/src/main/kotlin/org/microg/gms/ui/SettingsFragment.kt`, `play-services-core/src/main/kotlin/org/microg/gms/ui/updater/AppUpdater.kt`, `play-services-base/core/src/main/kotlin/org/microg/gms/common/PackageSpoofUtils.kt`, `play-services-base/core/src/main/java/org/microg/gms/common/PackageUtils.java`, `play-services-basement/src/main/java/org/microg/gms/common/Constants.java`, `play-services-core/src/main/res/values/strings.xml`.

Morphe patch sources:
`https://github.com/MorpheApp/morphe-patches/blob/main/patches/src/main/kotlin/app/morphe/patches/shared/misc/gms/GmsCoreSupportPatch.kt`,
`https://github.com/MorpheApp/morphe-patches/blob/main/extensions/shared-youtube/library/src/main/java/app/morphe/extension/shared/patches/GmsCoreSupportPatch.java`,
`https://github.com/MorpheApp/morphe-patches-library/blob/main/patch-library/src/main/kotlin/app/morphe/patches/all/misc/gms/GmsCorePackageQueriesPatch.kt`.

Android docs / release data:
- `https://developer.android.com/reference/android/provider/Settings#ACTION_MANAGE_UNKNOWN_APP_SOURCES`
- `https://developer.android.com/reference/android/content/pm/PackageManager#canRequestPackageInstalls()`
- `https://developer.android.com/reference/android/content/pm/PackageInstaller`
- `https://developer.android.com/reference/android/content/pm/PackageInstaller.SessionParams#setRequireUserAction(int)`
- `https://developer.android.com/about/versions/oreo/android-8.0-changes#unknown-sources`
- `https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/AndroidManifest.xml` (`REQUEST_INSTALL_PACKAGES`, line 6036; `REQUEST_DELETE_PACKAGES`, line 6047)
- `https://api.github.com/repos/MorpheApp/MicroG-RE/releases/latest`
- `https://github.com/MorpheApp/MicroG-RE/wiki/Signature-Spoofing`
