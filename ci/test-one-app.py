#!/usr/bin/env python3
"""Static acceptance tests for the T YouTube v1.2.0 one-app setup.

This is the RED/GREEN gate. It never builds anything; it inspects the decoded
tree, the compiled setup dex and the signed APK.

Usage:
    python3 ci/test-one-app.py --work work --dex build/setup-dex/classes.dex \
        --apk dist/T-YouTube-Zversion.apk --assets microg-assets
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import zipfile

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

failures: list[str] = []
checks = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if condition:
        print(f"PASS  {label}")
    else:
        failures.append(label + (f" ({detail})" if detail else ""))
        print(f"FAIL  {label}" + (f" ({detail})" if detail else ""))


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_work(work: pathlib.Path) -> None:
    manifest = (work / "AndroidManifest.xml").read_text(encoding="utf-8")
    prefs = (work / "res/xml/youtube_prefs.xml").read_text(encoding="utf-8")
    apktool = (work / "apktool.yml").read_text(encoding="utf-8")
    gms = (work / "smali_classes10/com/gold/extension/shared/patches/"
                 "GmsCoreSupportPatch.smali").read_text(encoding="utf-8")

    check("manifest: package unchanged",
          'package="com.gold.android.youtube"' in manifest)
    check("apktool: versionCode unchanged", "versionCode: 2147483647" in apktool)
    check("apktool: versionName unchanged", "versionName: 21.26.364" in apktool)

    for permission in (
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.REQUEST_DELETE_PACKAGES",
        "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
    ):
        check(f"manifest: {permission}", permission in manifest)

    check("manifest: microG package query",
          '<package android:name="app.revanced.android.gms"/>' in manifest)
    check("manifest: spoof package name kept",
          'android:name="app.revanced.android.gms.SPOOFED_PACKAGE_NAME"'
          in manifest)
    check("manifest: spoof signature kept",
          'android:name="app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE"'
          in manifest)
    check("manifest: launcher alias targets setup",
          'android:name="com.google.android.youtube.app.honeycomb.Shell$HomeActivity" '
          'android:targetActivity="com.gold.youtube.MicroG.MicroGActivity">'
          in manifest)
    check("manifest: setup activity exported",
          'android:exported="true" android:launchMode="singleTop" '
          'android:name="com.gold.youtube.MicroG.MicroGActivity"' in manifest)
    check("manifest: predictive back opted out",
          'android:enableOnBackInvokedCallback="false"' in manifest)
    check("manifest: receiver is not exported",
          '<receiver android:exported="false" '
          'android:name="com.gold.youtube.MicroG.InstallResultReceiver"/>'
          in manifest)
    check("manifest: no new QUERY_ALL_PACKAGES",
          manifest.count("QUERY_ALL_PACKAGES") == 1)

    check("settings: Setup & permissions row",
          'android:key="tyt_setup_preferences"' in prefs)
    check("settings: opens setup in manage mode",
          'android:targetClass="com.gold.youtube.MicroG.MicroGActivity"' in prefs
          and '<extra android:name="mode" android:value="manage" />' in prefs)
    check("settings: existing microG row kept",
          'android:key="microg_settings"' in prefs)
    check("settings: About build marker v1.2.0",
          'android:summary="21.26.364 (v1.2.0)"' in prefs)
    check("settings: one About screen only",
          prefs.count('android:key="youtube_settings_screen_13_about"') == 1)

    no_op = """.method public static checkGmsCore(Landroid/app/Activity;)V
    .locals 0

    # T YouTube owns setup. Never open a browser or a download page from here.
    return-void
.end method"""
    check("extension: checkGmsCore is a no-op", no_op in gms)
    check("extension: no browser URL left in checkGmsCore",
          "https://morphe.software" not in gms[gms.index(no_op):
                                              gms.index(".end method",
                                                        gms.index(no_op))])

    layouts = [
        work / "res/layout/youtube_controls_bottom_ui_container.xml",
        work / "res/layout/youtube_video_exploder_controls_bottom_ui_container.xml",
    ]
    for layout in layouts:
        if not layout.is_file():
            check(f"watermark: {layout.name} exists", False)
            continue
        text = layout.read_text(encoding="utf-8")
        check(f"watermark: {layout.name} present",
              'android:tag="tyt_watermark"' in text)
        check(f"watermark: {layout.name} 11.5sp",
              'android:textSize="11.5sp"' in text)
        check(f"watermark: {layout.name} alpha 0.55",
              'android:alpha="0.55"' in text)
        check(f"watermark: {layout.name} no old 14sp",
              'android:textSize="14.0sp"' not in text)
        check(f"watermark: {layout.name} no old 0.8 alpha",
              'android:alpha="0.8"' not in text)
        check(f"watermark: {layout.name} below controls",
              'layout_constraintBottom_toBottomOf="parent"' in text)

    compressed = apktool.split("doNotCompress:", 1)
    check("apktool: doNotCompress has apk",
          len(compressed) == 2 and "- apk" in compressed[1])

    assets = work / "assets/microg"
    for name, (size, sha) in ASSETS.items():
        path = assets / name
        check(f"asset: {name} exists", path.is_file())
        if path.is_file():
            check(f"asset: {name} size", path.stat().st_size == size,
                  f"got {path.stat().st_size}")
            check(f"asset: {name} sha256", sha256_file(path) == sha)
    check("asset: build info", (assets / "BUILD-INFO.txt").is_file())
    license_file = work / "assets/licenses/microg-RE.txt"
    check("asset: microG license", license_file.is_file())
    if license_file.is_file():
        license_text = license_file.read_text(encoding="utf-8")
        check("asset: license is the full Apache-2.0 text",
              "Apache License" in license_text
              and "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION"
              in license_text)

    setup = (pathlib.Path(__file__).resolve().parent.parent
             / "setup-src/com/gold/youtube/MicroG/MicroGInstaller.java")
    if setup.is_file():
        source = setup.read_text(encoding="utf-8")
        check("setup: package pinned", f'"{MICROG_PACKAGE}"' in source)
        check("setup: versionCode pinned", str(MICROG_VERSION_CODE) + "L" in source)
        check("setup: signer pinned", MICROG_CERT_SHA256 in source)
        for name, (size, sha) in ASSETS.items():
            check(f"setup: {name} hash pinned", sha in source)
            check(f"setup: {name} size pinned", str(size) + "L" in source)


def test_dex(dex: pathlib.Path) -> None:
    data = dex.read_bytes()
    check("dex: MicroGActivity compiled",
          b"Lcom/gold/youtube/MicroG/MicroGActivity;" in data)
    check("dex: InstallResultReceiver compiled",
          b"Lcom/gold/youtube/MicroG/InstallResultReceiver;" in data)
    check("dex: MicroGInstaller compiled",
          b"Lcom/gold/youtube/MicroG/MicroGInstaller;" in data)
    check("dex: no AndroidX imports",
          b"Landroidx/" not in data)


def test_apk(apk: pathlib.Path) -> None:
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        dexes = sorted(n for n in names
                       if n.startswith("classes") and n.endswith(".dex"))
        check("apk: 11 dex files", len(dexes) == 11, f"got {len(dexes)}")
        check("apk: classes11.dex present", "classes11.dex" in names)
        if "classes11.dex" in names:
            data = archive.read("classes11.dex")
            check("apk: setup activity in classes11.dex",
                  b"Lcom/gold/youtube/MicroG/MicroGActivity;" in data)
            check("apk: install receiver in classes11.dex",
                  b"Lcom/gold/youtube/MicroG/InstallResultReceiver;" in data)

        for name, (size, sha) in ASSETS.items():
            entry = f"assets/microg/{name}"
            check(f"apk: {entry} present", entry in names)
            if entry in names:
                info = archive.getinfo(entry)
                data = archive.read(entry)
                check(f"apk: {entry} stored uncompressed",
                      info.compress_type == zipfile.ZIP_STORED,
                      f"compress_type={info.compress_type}")
                check(f"apk: {entry} size", len(data) == size)
                check(f"apk: {entry} sha256",
                      hashlib.sha256(data).hexdigest() == sha)
        check("apk: license packaged",
              "assets/licenses/microg-RE.txt" in names)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=pathlib.Path)
    parser.add_argument("--dex", type=pathlib.Path)
    parser.add_argument("--apk", type=pathlib.Path)
    args = parser.parse_args()
    if not args.work and not args.dex and not args.apk:
        parser.error("provide at least one of --work, --dex, --apk")

    if args.work:
        test_work(args.work)
    if args.dex:
        test_dex(args.dex)
    if args.apk:
        test_apk(args.apk)

    print(f"\n{checks - len(failures)}/{checks} checks passed")
    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
