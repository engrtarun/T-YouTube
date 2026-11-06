#!/usr/bin/env python3
"""Apply the T YouTube v1.2.0 one-app setup patches to a decoded tree.

Usage:
    python3 scripts/apply-one-app.py <decoded-dir> [microg-assets-dir]

Run this AFTER scripts/apply-zversion.py. The script is exact-once: every
anchor must match exactly one line or it stops without writing that change.

What it adds:
  * Manifest: install/battery permissions, setup Activity flags, result
    receiver, and the launcher alias retargeted to MicroGActivity.
  * Settings: one "Setup & permissions" row above About.
  * Assets: the two official MicroG-RE -noicon APKs, copied byte-for-byte
    and verified against pinned SHA-256 values.
  * Extension: GmsCoreSupportPatch.checkGmsCore becomes a no-op so the old
    extension cannot open a browser behind the setup screen.
  * apktool.yml: inner APKs stored uncompressed.
"""

from __future__ import annotations

import hashlib
import pathlib
import shutil
import sys

MANIFEST = pathlib.Path("AndroidManifest.xml")
PREFS = pathlib.Path("res/xml/youtube_prefs.xml")
APKTOOL = pathlib.Path("apktool.yml")
GMS_PATCH = pathlib.Path(
    "smali_classes10/com/gold/extension/shared/patches/GmsCoreSupportPatch.smali"
)

REPO = pathlib.Path(__file__).resolve().parent.parent
LICENSE_SOURCE = REPO / "licenses" / "microg-RE.txt"

MICROG_PACKAGE = "app.revanced.android.gms"
MICROG_VERSION = "7.3.0"
MICROG_VERSION_CODE = 255070304
MICROG_CERT_SHA256 = (
    "0b6c9515afb195fac59601696ba0a7907a0b217ccf720b43148427ccf64343e7"
)

ASSETS = {
    "microg-7.3.0-noicon-arm64-v8a.apk": (
        45648640,
        "98e2de8c1543fb2736971b8ba307c2b58c092c96fb6dcebe3c3b8a4538151a23",
    ),
    "microg-7.3.0-noicon-armeabi-v7a.apk": (
        43445006,
        "af89d740a58136779f7406b6f00a546880ee7f3c7472b2a886239ee5a6e43a86",
    ),
}

ACTIVITY_OLD = (
    '        <activity android:name="com.gold.youtube.MicroG.MicroGActivity" '
    'android:theme="@style/Theme.YouTube.Settings"/>'
)
ACTIVITY_NEW = (
    '        <activity android:configChanges="keyboardHidden|orientation|screenSize|'
    'screenLayout|smallestScreenSize|uiMode|density" '
    'android:enableOnBackInvokedCallback="false" android:exported="true" '
    'android:launchMode="singleTop" '
    'android:name="com.gold.youtube.MicroG.MicroGActivity" '
    'android:theme="@android:style/Theme.Material.NoActionBar"/>'
)
RECEIVER = (
    '        <receiver android:exported="false" '
    'android:name="com.gold.youtube.MicroG.InstallResultReceiver"/>'
)

ALIAS_OLD = (
    '        <activity-alias android:exported="true" '
    'android:name="com.google.android.youtube.app.honeycomb.Shell$HomeActivity" '
    'android:targetActivity="com.google.android.apps.youtube.app.watchwhile.MainActivity">'
)
ALIAS_NEW = (
    '        <activity-alias android:exported="true" '
    'android:name="com.google.android.youtube.app.honeycomb.Shell$HomeActivity" '
    'android:targetActivity="com.gold.youtube.MicroG.MicroGActivity">'
)

PERMISSIONS_ANCHOR = (
    '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>\n'
)
PERMISSIONS_NEW = (
    PERMISSIONS_ANCHOR
    + '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>\n'
    + '    <uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES"/>\n'
    + '    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"/>\n'
)

PREFS_ANCHOR = (
    '    <PreferenceScreen android:title="@string/youtube_settings_screen_00_about_title" '
    'android:key="youtube_settings_screen_13_about">\n'
)
PREFS_NEW = (
    '    <Preference android:title="Setup &amp; permissions" '
    'android:key="tyt_setup_preferences" '
    'android:summary="microG, notifications and battery">\n'
    '        <intent android:targetPackage="com.gold.android.youtube" '
    'android:targetClass="com.gold.youtube.MicroG.MicroGActivity">\n'
    '            <extra android:name="mode" android:value="manage" />\n'
    '        </intent>\n'
    '    </Preference>\n'
    + PREFS_ANCHOR
)

GMS_SIGNATURE = ".method public static checkGmsCore(Landroid/app/Activity;)V"
GMS_NEW = """.method public static checkGmsCore(Landroid/app/Activity;)V
    .locals 0

    # T YouTube owns setup. Never open a browser or a download page from here.
    return-void
.end method"""


def replace_once(root: pathlib.Path, rel: pathlib.Path, old: str, new: str,
                 label: str) -> bool:
    path = root / rel
    if not path.is_file():
        print(f"FAIL: {label}: missing {path}", file=sys.stderr)
        return False
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        print(f"FAIL: {label}: expected 1 match in {path}, found {count}",
              file=sys.stderr)
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"OK: {label}")
    return True


def replace_method(root: pathlib.Path, rel: pathlib.Path, signature: str,
                   new_method: str, required: tuple[str, ...],
                   label: str) -> bool:
    path = root / rel
    if not path.is_file():
        print(f"FAIL: {label}: missing {path}", file=sys.stderr)
        return False
    text = path.read_text(encoding="utf-8")
    if text.count(signature) != 1:
        print(f"FAIL: {label}: expected 1 method signature in {path}, "
              f"found {text.count(signature)}", file=sys.stderr)
        return False
    start = text.index(signature)
    end = text.index(".end method", start) + len(".end method")
    old_method = text[start:end]
    for needle in required:
        if needle not in old_method:
            print(f"FAIL: {label}: old method is missing {needle!r}",
                  file=sys.stderr)
            return False
    path.write_text(text[:start] + new_method + text[end:], encoding="utf-8")
    print(f"OK: {label}")
    return True


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_assets(root: pathlib.Path, assets_dir: pathlib.Path | None) -> bool:
    target_dir = root / "assets" / "microg"
    target_dir.mkdir(parents=True, exist_ok=True)
    if assets_dir is None:
        print(f"FAIL: microG assets dir not provided; expected {target_dir}",
              file=sys.stderr)
        return False
    for name, (expected_size, expected_sha) in ASSETS.items():
        source = assets_dir / name
        if not source.is_file():
            print(f"FAIL: bundled asset missing: {source}", file=sys.stderr)
            return False
        size = source.stat().st_size
        sha = sha256_file(source)
        if size != expected_size or sha != expected_sha:
            print(f"FAIL: {name}: size={size} sha256={sha}",
                  file=sys.stderr)
            print(f"      expected size={expected_size} sha256={expected_sha}",
                  file=sys.stderr)
            return False
        destination = target_dir / name
        shutil.copyfile(source, destination)
        print(f"OK: bundled {name} ({size} bytes)")

    info = [
        f"package={MICROG_PACKAGE}",
        f"versionName={MICROG_VERSION}",
        f"versionCode={MICROG_VERSION_CODE}",
        f"signerSha256={MICROG_CERT_SHA256}",
        "variants=" + ",".join(ASSETS),
        "",
    ]
    (target_dir / "BUILD-INFO.txt").write_text("\n".join(info), encoding="utf-8")
    licenses = root / "assets" / "licenses"
    licenses.mkdir(parents=True, exist_ok=True)
    if not LICENSE_SOURCE.is_file():
        print(f"FAIL: license text missing: {LICENSE_SOURCE}", file=sys.stderr)
        return False
    shutil.copyfile(LICENSE_SOURCE, licenses / "microg-RE.txt")
    print("OK: microG metadata and license written")
    return True


def post_conditions(root: pathlib.Path) -> bool:
    manifest = (root / MANIFEST).read_text(encoding="utf-8")
    prefs = (root / PREFS).read_text(encoding="utf-8")
    apktool = (root / APKTOOL).read_text(encoding="utf-8")
    gms = (root / GMS_PATCH).read_text(encoding="utf-8")

    checks = [
        ("REQUEST_INSTALL_PACKAGES declared",
         'android.permission.REQUEST_INSTALL_PACKAGES' in manifest),
        ("REQUEST_DELETE_PACKAGES declared",
         'android.permission.REQUEST_DELETE_PACKAGES' in manifest),
        ("battery exemption declared",
         'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS' in manifest),
        ("launcher alias targets setup",
         'android:targetActivity="com.gold.youtube.MicroG.MicroGActivity">'
         in manifest),
        ("setup activity exported",
         'android:exported="true" android:launchMode="singleTop" '
         'android:name="com.gold.youtube.MicroG.MicroGActivity"' in manifest),
        ("install receiver declared",
         'com.gold.youtube.MicroG.InstallResultReceiver' in manifest),
        ("microG package query kept",
         '<package android:name="app.revanced.android.gms"/>' in manifest),
        ("settings row present",
         'android:key="tyt_setup_preferences"' in prefs),
        ("settings row opens manage mode",
         '<extra android:name="mode" android:value="manage" />' in prefs),
        ("checkGmsCore is a no-op",
         GMS_NEW in gms),
        ("inner APKs are stored",
         "- apk" in apktool.split("doNotCompress:", 1)[1]),
    ]
    ok = True
    for label, passed in checks:
        if passed:
            print(f"OK: {label}")
        else:
            print(f"FAIL: {label}", file=sys.stderr)
            ok = False
    return ok


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    assets_dir = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else None
    if not (root / MANIFEST).is_file():
        print(f"FAIL: {root} is not a decoded APK tree", file=sys.stderr)
        return 2

    steps = [
        (MANIFEST, PERMISSIONS_ANCHOR, PERMISSIONS_NEW,
         "Manifest: declare install and battery permissions"),
        (MANIFEST, ACTIVITY_OLD, ACTIVITY_NEW,
         "Manifest: make MicroGActivity the single-top setup screen"),
        (MANIFEST, ACTIVITY_NEW, ACTIVITY_NEW + "\n" + RECEIVER,
         "Manifest: declare the install result receiver"),
        (MANIFEST, ALIAS_OLD, ALIAS_NEW,
         "Manifest: retarget the launcher alias to setup"),
        (PREFS, PREFS_ANCHOR, PREFS_NEW,
         "Settings: add Setup & permissions above About"),
        (APKTOOL, "doNotCompress:\n- arsc\n",
         "doNotCompress:\n- apk\n- arsc\n",
         "apktool.yml: store inner APKs uncompressed"),
    ]
    for rel, old, new, label in steps:
        if not replace_once(root, rel, old, new, label):
            return 1

    if not replace_method(
            root, GMS_PATCH, GMS_SIGNATURE, GMS_NEW,
            ("isPackageNameOriginal", "https://morphe.software"),
            "Extension: stop checkGmsCore from opening a browser"):
        return 1

    if not copy_assets(root, assets_dir):
        return 1

    if not post_conditions(root):
        print("FAIL: post-conditions failed", file=sys.stderr)
        return 1
    print("DONE: one-app setup patches applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
