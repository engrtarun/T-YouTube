#!/usr/bin/env python3
"""Apply the three T-YouTube bug-fix patches to an apktool-decoded tree.

Usage: python3 scripts/apply-fixes.py <decoded-dir>

The patches only change default setting values / one static read; no UI or
feature code is added. Each replacement must match exactly once, otherwise the
build fails on purpose (so an upstream APK change can never silently produce an
unpatched build).
"""
from __future__ import annotations

import pathlib
import sys

SETTINGS = pathlib.Path(
    "smali_classes10/com/gold/extension/youtube/settings/Settings.smali"
)
EXTRACTOR = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/extractor/services/youtube/"
    "extractors/YoutubeStreamExtractor.smali"
)

EDITS = [
    (
        SETTINGS,
        "sget-object v7, Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;->MINIMAL:"
        "Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;",
        "sget-object v7, Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;->DEFAULT:"
        "Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;",
        "PiP: default miniplayer MINIMAL -> DEFAULT",
    ),
    (
        SETTINGS,
        "sget-object v6, Lcom/gold/extension/shared/spoof/ClientType;->ANDROID_REEL_AUTH:"
        "Lcom/gold/extension/shared/spoof/ClientType;",
        "sget-object v6, Lcom/gold/extension/shared/spoof/ClientType;->ANDROID_VR_1_64:"
        "Lcom/gold/extension/shared/spoof/ClientType;",
        "Playback: default spoof client ANDROID_REEL_AUTH -> ANDROID_VR_1_64",
    ),
    (
        EXTRACTOR,
        "sget-boolean v8, Lcom/gold/youtube/om7753/extractor/services/youtube/extractors/"
        "YoutubeStreamExtractor;->fetchIosClient:Z",
        "const/4 v8, 0x1",
        "Downloads: enable iOS stream source (setFetchIosClient(true) behaviour)",
    ),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <decoded-dir>", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    for rel_path, old, new, label in EDITS:
        path = root / rel_path
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            print(
                f"FAIL: {label}: expected 1 match in {path}, found {count}",
                file=sys.stderr,
            )
            return 1
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"OK: {label}")

    # Post-conditions: the patched instructions must be present, old ones gone.
    settings = (root / SETTINGS).read_text(encoding="utf-8")
    extractor = (root / EXTRACTOR).read_text(encoding="utf-8")
    checks = [
        (
            "MiniplayerPatch$MiniplayerType;->DEFAULT:"
            "Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;" in settings,
            "miniplayer DEFAULT default present",
        ),
        (
            "MiniplayerPatch$MiniplayerType;->MINIMAL:"
            "Lcom/gold/extension/youtube/patches/MiniplayerPatch$MiniplayerType;" not in settings,
            "miniplayer MINIMAL default removed",
        ),
        (
            "ClientType;->ANDROID_VR_1_64:Lcom/gold/extension/shared/spoof/ClientType;"
            in settings,
            "Android VR default present",
        ),
        (
            "ClientType;->ANDROID_REEL_AUTH:Lcom/gold/extension/shared/spoof/ClientType;"
            not in settings,
            "Reel default removed",
        ),
        (
            "sget-boolean v8, Lcom/gold/youtube/om7753/extractor/services/youtube/"
            "extractors/YoutubeStreamExtractor;->fetchIosClient:Z" not in extractor,
            "fetchIosClient read replaced",
        ),
        ("const/4 v8, 0x1" in extractor, "iOS fetch enabled"),
    ]
    for ok, msg in checks:
        if not ok:
            print(f"FAIL: post-condition: {msg}", file=sys.stderr)
            return 1
        print(f"OK: post-condition: {msg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
