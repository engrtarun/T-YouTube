#!/usr/bin/env python3
"""Apply the T-YouTube bug-fix + branding-default patches to a decoded tree.

Usage: python3 scripts/apply-fixes.py <decoded-dir>

Only default values, one filename sanitizer and two XML defaults are changed.
No new screens, buttons or menus are added. Each replacement must match
exactly once, otherwise the build fails on purpose (so an upstream APK change
can never silently produce an unpatched build).
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
FILENAMES = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/util/FilenameUtils.smali"
)
GENERAL_PREFS = pathlib.Path("res/xml/general_prefs.xml")

OLD_FILENAME_METHOD = """.method private static createFilename(Ljava/lang/String;Ljava/util/regex/Pattern;Ljava/lang/String;)Ljava/lang/String;
    .locals 0

    invoke-virtual {p1}, Ljava/util/regex/Pattern;->pattern()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p0, p1, p2}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method
"""

NEW_FILENAME_METHOD = r""".method private static createFilename(Ljava/lang/String;Ljava/util/regex/Pattern;Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    invoke-virtual {p1}, Ljava/util/regex/Pattern;->pattern()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p0, p1, p2}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z

    move-result p1

    if-nez p1, :nonempty

    const-string p0, "download"

    :nonempty
    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result p1

    const/16 p2, 0x50

    if-le p1, p2, :done

    const/4 v0, 0x0

    invoke-virtual {p0, v0, p2}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object p0

    :done
    return-object p0
.end method
"""

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
        "sget-object v6, Lcom/gold/extension/shared/spoof/ClientType;->VISIONOS:"
        "Lcom/gold/extension/shared/spoof/ClientType;",
        "Playback: default spoof client ANDROID_REEL_AUTH -> VISIONOS",
    ),
    (
        SETTINGS,
        "const-string v2, \"youtube_spoof_video_streams_client_type\"",
        "const-string v2, \"youtube_spoof_video_streams_client_type_v2\"",
        "Playback: version the spoof-client pref key so old installs pick up VISIONOS",
    ),
    (
        pathlib.Path("res/xml/youtube_prefs.xml"),
        'android:key="youtube_spoof_video_streams_client_type"',
        'android:key="youtube_spoof_video_streams_client_type_v2"',
        "Playback: point settings UI at versioned spoof-client key (youtube_prefs)",
    ),
    (
        pathlib.Path("res/xml/youtube_prefs_icons.xml"),
        'android:key="youtube_spoof_video_streams_client_type"',
        'android:key="youtube_spoof_video_streams_client_type_v2"',
        "Playback: point settings UI at versioned spoof-client key (icons)",
    ),
    (
        pathlib.Path("res/xml/youtube_prefs_icons_bold.xml"),
        'android:key="youtube_spoof_video_streams_client_type"',
        'android:key="youtube_spoof_video_streams_client_type_v2"',
        "Playback: point settings UI at versioned spoof-client key (icons bold)",
    ),
    (
        SETTINGS,
        "    new-instance v5, Lcom/gold/extension/shared/settings/BooleanSetting;\n"
        "\n"
        "    const-string v6, \"youtube_seekbar_custom_color\"\n"
        "\n"
        "    invoke-direct {v5, v6, v4, v7}, Lcom/gold/extension/shared/settings/"
        "BooleanSetting;-><init>(Ljava/lang/String;Ljava/lang/Boolean;Z)V",
        "    new-instance v5, Lcom/gold/extension/shared/settings/BooleanSetting;\n"
        "\n"
        "    const-string v6, \"youtube_seekbar_custom_color\"\n"
        "\n"
        "    invoke-direct {v5, v6, v1, v7}, Lcom/gold/extension/shared/settings/"
        "BooleanSetting;-><init>(Ljava/lang/String;Ljava/lang/Boolean;Z)V",
        "Seekbar: enable custom colors by default (v1 is Boolean.TRUE here)",
    ),
    (
        SETTINGS,
        "const-string v7, \"#FF0033\"",
        "const-string v7, \"#00FCFF\"",
        "Seekbar: primary colour -> logo cyan-green #00FCFF",
    ),
    (
        SETTINGS,
        "const-string v3, \"#FF2791\"",
        "const-string v3, \"#F3024E\"",
        "Seekbar: accent colour -> logo red #F3024E",
    ),
    (
        FILENAMES,
        OLD_FILENAME_METHOD,
        NEW_FILENAME_METHOD,
        "Downloads: cap display names at 80 chars without crashing short titles",
    ),
    (
        GENERAL_PREFS,
        'android:key="app_theme_dark" android:summary="@string/pref_dark_theme_for_app_summary" '
        'android:defaultValue="false"',
        'android:key="app_theme_dark" android:summary="@string/pref_dark_theme_for_app_summary" '
        'android:defaultValue="true"',
        "Theme: dark theme switch default false -> true",
    ),
    (
        GENERAL_PREFS,
        'android:key="app_theme_appearance" android:summary="@string/app_theme_appearance_summary"',
        'android:key="app_theme_appearance" android:defaultValue="@string/app_theme_appearance_dark" '
        'android:summary="@string/app_theme_appearance_summary"',
        "Theme: Appearance list default -> Dark",
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
    filenames = (root / FILENAMES).read_text(encoding="utf-8")
    prefs = (root / GENERAL_PREFS).read_text(encoding="utf-8")
    spoof_prefs = [
        (root / pathlib.Path("res/xml/youtube_prefs.xml")).read_text(encoding="utf-8"),
        (root / pathlib.Path("res/xml/youtube_prefs_icons.xml")).read_text(encoding="utf-8"),
        (root / pathlib.Path("res/xml/youtube_prefs_icons_bold.xml")).read_text(encoding="utf-8"),
    ]
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
            "ClientType;->VISIONOS:Lcom/gold/extension/shared/spoof/ClientType;" in settings,
            "visionOS default present",
        ),
        (
            "ClientType;->ANDROID_REEL_AUTH:Lcom/gold/extension/shared/spoof/ClientType;"
            not in settings,
            "Reel default removed",
        ),
        (
            '"youtube_spoof_video_streams_client_type_v2"' in settings,
            "spoof-client key versioned",
        ),
        (
            all(
                'android:key="youtube_spoof_video_streams_client_type_v2"' in t
                for t in spoof_prefs
            )
            and not any(
                'android:key="youtube_spoof_video_streams_client_type"' in t
                for t in spoof_prefs
            ),
            "settings UI uses the versioned spoof-client key",
        ),
        (
            "\"#00FCFF\"" in settings and "\"#F3024E\"" in settings,
            "seekbar brand colours present",
        ),
        (
            "invoke-direct {v5, v6, v1, v7}, Lcom/gold/extension/shared/settings/"
            "BooleanSetting;-><init>(Ljava/lang/String;Ljava/lang/Boolean;Z)V" in settings,
            "seekbar custom colours enabled by default",
        ),
        (
            "if-le p1, p2, :done" in filenames,
            "filename cap skips short names (no short-title substring crash)",
        ),
        (
            "const/16 p2, 0x50" in filenames,
            "filename 80-char cap present",
        ),
        (
            "uD800" not in filenames,
            "unsafe surrogate regex removed",
        ),
        (
            'android:key="app_theme_dark"' in prefs
            and 'android:defaultValue="true"' in prefs,
            "dark theme switch defaults to true",
        ),
        (
            'android:key="app_theme_appearance" android:defaultValue='
            '"@string/app_theme_appearance_dark"' in prefs,
            "appearance defaults to dark",
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
