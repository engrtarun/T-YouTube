#!/usr/bin/env python3
"""Apply the T-YouTube test-fix-4 patches to a decoded tree.

Usage: python3 scripts/apply-test-fix-4.py <decoded-dir>

Adds:
  * Shorts back button: 8-second "T YouTube" branding loop (4.8s arrow,
    2.75s wordmark, 225ms crossfade each way), still one big Back tap target.
  * Fullscreen-only, controls-only "T YouTube" watermark in the bottom
    action row (portrait + landscape fullscreen).
  * Download dialog fix: duplicate names default to "Generate unique
    name", "Overwrite" is an explicit secondary action, stale finished
    missions are forgotten instead of blocking, and a failed truncate
    recovers with delete + recreate.

Every replacement must match exactly once, otherwise the build fails on
purpose so an upstream APK change can never silently produce an
unpatched build. New files are written from this script; image assets are
copied from scripts/assets/test-fix-4.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent
ASSETS = REPO / "assets" / "test-fix-4"

SHORTS_LAYOUT = pathlib.Path("res/layout/reel_player_static_header.xml")
CONTROLS_LAYOUT = pathlib.Path("res/layout/youtube_controls_bottom_ui_container.xml")
DOWNLOAD_DIALOG = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/download/DownloadDialog.smali"
)
OVERLAY_WRAPPER = pathlib.Path(
    "smali_classes8/com/google/android/apps/youtube/app/player/overlay/"
    "SizeAdjustableOverlayWrapperLayout.smali"
)
SHORTS_HEADER_PRESENTER = pathlib.Path("smali/aqzl.smali")

BRAND_DIR = pathlib.Path("smali_classes10/com/gold/extension/youtube/brand")
DOWNLOAD_HELPER_DIR = pathlib.Path(
    "smali_classes10/com/gold/extension/youtube/download"
)

# ---------------------------------------------------------------- Shorts ---

OLD_BACK_BUTTON = (
    '    <ImageView android:layout_gravity="start|center|top" android:id="@id/reel_back_button" '
    'android:background="@drawable/reel_circular_button_background" '
    'android:padding="@dimen/reel_header_option_button_padding" android:visibility="gone" '
    'android:layout_width="wrap_content" android:layout_height="wrap_content" '
    'android:src="@drawable/yt_outline_arrow_left_black_24" android:tint="?ytOverlayTextPrimary" '
    'android:layout_alignParentTop="true" '
    'android:contentDescription="@string/reel_accessibility_player_back_button" '
    'android:layout_marginStart="@dimen/reel_header_back_button_margin_start" '
    'android:layout_alignParentStart="true" />'
)

NEW_BACK_BUTTON = (
    '    <ImageView android:id="@id/reel_back_button" '
    'android:background="@drawable/tyt_reel_back_animation" '
    'android:foreground="@drawable/tyt_reel_back_foreground" android:visibility="gone" '
    'android:layout_width="128.0dip" android:layout_height="48.0dip" '
    'android:layout_alignParentTop="true" '
    'android:contentDescription="@string/reel_accessibility_player_back_button" '
    'android:layout_marginStart="@dimen/reel_header_back_button_margin_start" '
    'android:layout_alignParentStart="true" />'
)

# Keep the contextual title where it was (4dp margin + 48dp stock button +
# 13dp title margin = 65dp) even though the tap target is now 128dp wide.
OLD_TITLE_ANCHOR = (
    'android:layout_marginStart="@dimen/reel_player_contextual_header_margin_start" '
    'android:layout_toEndOf="@id/reel_back_button"'
)
NEW_TITLE_ANCHOR = (
    'android:layout_marginStart="65.0dip" android:layout_alignParentStart="true"'
)

ANIMATION_XML = """<?xml version="1.0" encoding="utf-8"?>
<animation-list android:oneshot="false"
  xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@drawable/tyt_brand_00_arrow" android:duration="4800" />
    <item android:drawable="@drawable/tyt_brand_01_fade25" android:duration="75" />
    <item android:drawable="@drawable/tyt_brand_02_fade50" android:duration="75" />
    <item android:drawable="@drawable/tyt_brand_03_fade75" android:duration="75" />
    <item android:drawable="@drawable/tyt_brand_04_text" android:duration="2750" />
    <item android:drawable="@drawable/tyt_brand_05_back25" android:duration="75" />
    <item android:drawable="@drawable/tyt_brand_06_back50" android:duration="75" />
    <item android:drawable="@drawable/tyt_brand_07_back75" android:duration="75" />
</animation-list>
"""

FOREGROUND_XML = """<?xml version="1.0" encoding="utf-8"?>
<layer-list
  xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:gravity="start|center" android:width="48.0dip" android:height="48.0dip"
      android:drawable="@drawable/reel_circular_button_background" />
</layer-list>
"""

# ---------------------------------------------------- Shorts start hook ---

OLD_HEADER_HOOK = """    :cond_10
    const v2, 0x7f0b10c3

    .line 261
    .line 262
    .line 263
    invoke-virtual {p1, v2}, Landroid/view/View;->findViewById(I)Landroid/view/View;

    .line 264
    move-result-object p1

    .line 265
    .line 266
    :goto_4
    if-eqz p1, :cond_12
"""

NEW_HEADER_HOOK = """    :cond_10
    const v2, 0x7f0b10c3

    .line 261
    .line 262
    .line 263
    invoke-virtual {p1, v2}, Landroid/view/View;->findViewById(I)Landroid/view/View;

    .line 264
    move-result-object p1

    .line 265
    .line 266
    :goto_4
    if-eqz p1, :cond_12

    invoke-static {p1}, Lcom/gold/extension/youtube/brand/BrandAnimation;->start(Landroid/view/View;)V
"""

# ------------------------------------------------ Fullscreen watermark ---

OLD_QUICK_ACTIONS = """    <com.google.android.apps.youtube.app.player.overlay.InterceptingFrameLayout android:id="@id/quick_actions_container" android:paddingTop="12.0dip" android:visibility="gone" android:layout_width="fill_parent" android:layout_height="wrap_content" app:layout_constraintBottom_toBottomOf="parent">
        <FrameLayout android:id="@id/quick_actions_element_container" android:layout_width="fill_parent" android:layout_height="fill_parent" />
    </com.google.android.apps.youtube.app.player.overlay.InterceptingFrameLayout>"""

NEW_QUICK_ACTIONS = """    <com.google.android.apps.youtube.app.player.overlay.InterceptingFrameLayout android:id="@id/quick_actions_container" android:paddingTop="12.0dip" android:visibility="gone" android:layout_width="fill_parent" android:layout_height="wrap_content" app:layout_constraintBottom_toBottomOf="parent">
        <FrameLayout android:id="@id/quick_actions_element_container" android:layout_width="fill_parent" android:layout_height="fill_parent" />
        <com.google.android.libraries.youtube.common.ui.YouTubeTextView android:textSize="18.0sp" android:textColor="?ytOverlayTextPrimary" android:gravity="center" android:layout_gravity="center" android:tag="tyt_watermark" android:visibility="gone" android:layout_width="wrap_content" android:layout_height="wrap_content" android:text="T YouTube" android:alpha="0.8" android:importantForAccessibility="no" android:clickable="false" android:focusable="false" app:youTubeSansFont="bold" />
    </com.google.android.apps.youtube.app.player.overlay.InterceptingFrameLayout>"""

OLD_MEASURE_TAIL = (
    "    invoke-virtual {p0, p1, p2}, Lcom/google/android/apps/youtube/app/player/overlay/"
    "SizeAdjustableOverlayWrapperLayout;->setMeasuredDimension(II)V"
)
NEW_MEASURE_TAIL = OLD_MEASURE_TAIL + (
    "\n\n    invoke-static {p0, p1, p2}, Lcom/gold/extension/youtube/brand/"
    "WatermarkTuner;->apply(Landroid/view/View;II)V"
)

# ----------------------------------------------------- Download dialog ---

# 1) A file that exists without a matching mission must ask instead of
#    falling through to createFile()/truncate().
OLD_DOWNLOAD_EXISTS = """    move-result v0

    if-nez v0, :cond_3

    invoke-virtual {v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->create()Z

    move-result v0

    if-nez v0, :cond_3

    invoke-direct {p0, v6}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :cond_3
"""

NEW_DOWNLOAD_EXISTS = """    move-result v0

    if-nez v0, :cond_3

    const-string v6, "msg_exists"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    goto :goto_3

    :cond_3
"""

# 2) A Finished mission whose file was deleted is stale: forget it and
#    download normally instead of claiming the file already exists.
OLD_STALE_MISSION = """    :cond_b
    const-string v6, "overwrite_finished_warning"

    :goto_3
"""

NEW_STALE_MISSION = """    :cond_b
    invoke-virtual {v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v14

    if-eqz v14, :cond_c_missing

    const-string v6, "overwrite_finished_warning"

    goto :goto_3

    :cond_c_missing
    iget-object v14, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->downloadManager:Lus/shandian/giga/service/DownloadManager;

    invoke-virtual {v14, v4}, Lus/shandian/giga/service/DownloadManager;->forgetMission(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    goto/16 :cond_2

    :goto_3
"""

# 3) Positive button is "Generate unique name"; "Overwrite" is a neutral,
#    explicit second action (never offered while a download is running).
OLD_DIALOG_BUTTONS = """    :cond_d
    new-instance v10, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;

    move-object v1, v10

    move-object v2, p0

    move-object/from16 v5, p2

    move-object/from16 v6, p1

    move-object/from16 v7, p3

    move-object/from16 v8, p4

    invoke-direct/range {v1 .. v8}, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;-><init>(Lcom/gold/youtube/om7753/download/DownloadDialog;Lus/shandian/giga/service/MissionState;Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;Landroid/net/Uri;Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v13, v12, v10}, Landroid/app/AlertDialog$Builder;->setPositiveButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
"""

NEW_DIALOG_BUTTONS = """    :cond_d
    new-instance v10, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;

    move-object v1, v10

    move-object v2, p0

    move-object/from16 v5, p2

    move-object/from16 v6, p1

    move-object/from16 v7, p3

    move-object/from16 v8, p4

    invoke-direct/range {v1 .. v8}, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;-><init>(Lcom/gold/youtube/om7753/download/DownloadDialog;Lus/shandian/giga/service/MissionState;Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;Landroid/net/Uri;Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Ljava/lang/String;Ljava/lang/String;)V

    const-string v12, "generate_unique_name"

    invoke-static {v12}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v12

    invoke-virtual {v13, v12, v10}, Landroid/app/AlertDialog$Builder;->setPositiveButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object v12

    sget-object v2, Lcom/gold/youtube/om7753/download/DownloadDialog$3;->$SwitchMap$us$shandian$giga$service$MissionState:[I

    invoke-virtual {v3}, Ljava/lang/Enum;->ordinal()I

    move-result v6

    aget v6, v2, v6

    const/4 v10, 0x2

    if-ne v6, v10, :skip_neutral

    const/4 v10, 0x3

    if-ne v6, v10, :skip_neutral

    new-instance v10, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;

    move-object v1, v10

    move-object v2, p0

    move-object/from16 v5, p2

    move-object/from16 v6, p1

    move-object/from16 v7, p3

    move-object/from16 v8, p4

    invoke-direct/range {v1 .. v8}, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;-><init>(Lcom/gold/youtube/om7753/download/DownloadDialog;Lus/shandian/giga/service/MissionState;Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;Landroid/net/Uri;Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Ljava/lang/String;Ljava/lang/String;)V

    const-string v6, "overwrite"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    invoke-virtual {v12, v6, v10}, Landroid/app/AlertDialog$Builder;->setNeutralButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    :skip_neutral
"""

# 4) The positive (button -1) action always takes the unique-name path; the
#    neutral (-3) action keeps the existing overwrite path.
OLD_LAMBDA9_HEAD = """    invoke-interface {p7}, Landroid/content/DialogInterface;->dismiss()V

    sget-object p7, Lcom/gold/youtube/om7753/download/DownloadDialog$3;->$SwitchMap$us$shandian$giga$service$MissionState:[I
"""

NEW_LAMBDA9_HEAD = """    invoke-interface {p7}, Landroid/content/DialogInterface;->dismiss()V

    const/4 p7, -0x1

    if-ne p8, p7, :not_unique_action

    const-string p8, "error_file_creation"

    invoke-static {p8}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result p8

    goto/16 :cond_0

    :not_unique_action
    sget-object p7, Lcom/gold/youtube/om7753/download/DownloadDialog$3;->$SwitchMap$us$shandian$giga$service$MissionState:[I
"""

# 5) Never let a SAF truncate failure abort an approved overwrite.
OLD_TRUNCATE_CALL = (
    "    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/"
    "StoredFileHelper;->truncate()V"
)
NEW_TRUNCATE_CALL = (
    "    invoke-static/range {p1 .. p1}, Lcom/gold/extension/youtube/download/"
    "SafeTruncate;->run(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V"
)

# ------------------------------------------------------- New smali bits ---

BRAND_ANIMATION_SMALI = """.class public final Lcom/gold/extension/youtube/brand/BrandAnimation;
.super Ljava/lang/Object;


# direct methods
.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static start(Landroid/view/View;)V
    .locals 2

    if-eqz p0, :done

    invoke-virtual {p0}, Landroid/view/View;->getBackground()Landroid/graphics/drawable/Drawable;

    move-result-object v0

    if-eqz v0, :done

    instance-of v1, v0, Landroid/graphics/drawable/AnimationDrawable;

    if-eqz v1, :done

    check-cast v0, Landroid/graphics/drawable/AnimationDrawable;

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/graphics/drawable/AnimationDrawable;->setOneShot(Z)V

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->start()V

    :done
    return-void
.end method
"""

WATERMARK_TUNER_SMALI = """.class public final Lcom/gold/extension/youtube/brand/WatermarkTuner;
.super Ljava/lang/Object;


# direct methods
.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static apply(Landroid/view/View;II)V
    .locals 3

    if-eqz p0, :done

    const-string v0, "tyt_watermark"

    invoke-virtual {p0, v0}, Landroid/view/View;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;

    move-result-object v0

    if-eqz v0, :done

    invoke-virtual {p0}, Landroid/view/View;->getResources()Landroid/content/res/Resources;

    move-result-object v1

    invoke-virtual {v1}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v1

    iget v1, v1, Landroid/util/DisplayMetrics;->heightPixels:I

    mul-int/lit8 v1, v1, 0x3

    div-int/lit8 v1, v1, 0x4

    if-ge p2, v1, :hide

    const/4 v2, 0x0

    goto :set

    :hide
    const/16 v2, 0x8

    :set
    invoke-virtual {v0}, Landroid/view/View;->getVisibility()I

    move-result v1

    if-eq v1, v2, :done

    invoke-virtual {v0, v2}, Landroid/view/View;->setVisibility(I)V

    :done
    return-void
.end method
"""

SAFE_TRUNCATE_SMALI = """.class public final Lcom/gold/extension/youtube/download/SafeTruncate;
.super Ljava/lang/Object;


# direct methods
.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static run(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V
    .locals 1

    if-eqz p0, :done

    :try_start
    invoke-virtual {p0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->truncate()V

    return-void
    :try_end
    .catch Ljava/io/IOException; {:try_start .. :try_end} :fallback

    :fallback
    invoke-virtual {p0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->delete()Z

    move-result v0

    if-eqz v0, :fail

    invoke-virtual {p0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->create()Z

    move-result v0

    if-eqz v0, :fail

    return-void

    :fail
    new-instance v0, Ljava/io/IOException;

    const-string p0, "cannot replace the existing file"

    invoke-direct {v0, p0}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V

    throw v0

    :done
    return-void
.end method
"""


def replace_once(root: pathlib.Path, rel: pathlib.Path, old: str, new: str, label: str) -> bool:
    path = root / rel
    if not path.is_file():
        print(f"FAIL: {label}: missing {path}", file=sys.stderr)
        return False
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        print(f"FAIL: {label}: expected 1 match in {path}, found {count}", file=sys.stderr)
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"OK: {label}")
    return True


def write_new(root: pathlib.Path, rel: pathlib.Path, content: str, label: str) -> bool:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"OK: {label}")
    return True


def copy_brand_frames(root: pathlib.Path) -> bool:
    if not ASSETS.is_dir():
        print(f"FAIL: brand assets missing: {ASSETS}", file=sys.stderr)
        return False
    drawable = root / "res" / "drawable-xxhdpi"
    drawable.mkdir(parents=True, exist_ok=True)
    frames = sorted(ASSETS.glob("tyt_brand_*.png"))
    if len(frames) != 8:
        print(f"FAIL: expected 8 brand frames, found {len(frames)}", file=sys.stderr)
        return False
    for src in frames:
        shutil.copyfile(src, drawable / src.name)
    print(f"OK: copied {len(frames)} Shorts brand frames")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <decoded-dir>", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    steps = [
        (SHORTS_LAYOUT, OLD_BACK_BUTTON, NEW_BACK_BUTTON,
         "Shorts: 128x48 back button hosts the brand loop"),
        (SHORTS_LAYOUT, OLD_TITLE_ANCHOR, NEW_TITLE_ANCHOR,
         "Shorts: contextual title keeps its 65dp position"),
        (SHORTS_HEADER_PRESENTER, OLD_HEADER_HOOK, NEW_HEADER_HOOK,
         "Shorts: start the brand animation when the header binds"),
        (CONTROLS_LAYOUT, OLD_QUICK_ACTIONS, NEW_QUICK_ACTIONS,
         "Fullscreen: add the controls-only T YouTube watermark"),
        (OVERLAY_WRAPPER, OLD_MEASURE_TAIL, NEW_MEASURE_TAIL,
         "Fullscreen: show the watermark only when the player fills the screen"),
        (DOWNLOAD_DIALOG, OLD_DOWNLOAD_EXISTS, NEW_DOWNLOAD_EXISTS,
         "Downloads: ask before replacing an untracked existing file"),
        (DOWNLOAD_DIALOG, OLD_STALE_MISSION, NEW_STALE_MISSION,
         "Downloads: forget stale finished missions"),
        (DOWNLOAD_DIALOG, OLD_DIALOG_BUTTONS, NEW_DIALOG_BUTTONS,
         "Downloads: unique name is the default, overwrite is explicit"),
        (DOWNLOAD_DIALOG, OLD_LAMBDA9_HEAD, NEW_LAMBDA9_HEAD,
         "Downloads: positive button always generates a unique name"),
        (DOWNLOAD_DIALOG, OLD_TRUNCATE_CALL, NEW_TRUNCATE_CALL,
         "Downloads: recover from a failed truncate"),
    ]
    for rel, old, new, label in steps:
        if not replace_once(root, rel, old, new, label):
            return 1

    if not write_new(
        root, pathlib.Path("res/drawable/tyt_reel_back_animation.xml"),
        ANIMATION_XML, "Shorts: write the 8s animation-list"
    ):
        return 1
    if not write_new(
        root, pathlib.Path("res/drawable/tyt_reel_back_foreground.xml"),
        FOREGROUND_XML, "Shorts: write the 48dp ripple foreground"
    ):
        return 1
    if not write_new(root, BRAND_DIR / "BrandAnimation.smali", BRAND_ANIMATION_SMALI,
                     "Shorts: BrandAnimation helper"):
        return 1
    if not write_new(root, BRAND_DIR / "WatermarkTuner.smali", WATERMARK_TUNER_SMALI,
                     "Fullscreen: WatermarkTuner helper"):
        return 1
    if not write_new(root, DOWNLOAD_HELPER_DIR / "SafeTruncate.smali", SAFE_TRUNCATE_SMALI,
                     "Downloads: SafeTruncate helper"):
        return 1
    if not copy_brand_frames(root):
        return 1

    # Post-conditions: assert the new behaviour is really in the tree.
    shorts = (root / SHORTS_LAYOUT).read_text(encoding="utf-8")
    controls = (root / CONTROLS_LAYOUT).read_text(encoding="utf-8")
    dialog = (root / DOWNLOAD_DIALOG).read_text(encoding="utf-8")
    wrapper = (root / OVERLAY_WRAPPER).read_text(encoding="utf-8")
    checks = [
        ('android:layout_width="128.0dip"' in shorts
         and 'android:background="@drawable/tyt_reel_back_animation"' in shorts,
         "Shorts back button is 128x48 with the brand loop"),
        ('android:layout_marginStart="65.0dip"' in shorts,
         "Shorts contextual title keeps its old position"),
        ('BrandAnimation;->start(Landroid/view/View;)V' in
         (root / SHORTS_HEADER_PRESENTER).read_text(encoding="utf-8"),
         "Shorts header binds the animation"),
        ('android:tag="tyt_watermark"' in controls and 'android:alpha="0.8"' in controls,
         "Fullscreen watermark present at 80%"),
        ('WatermarkTuner;->apply(Landroid/view/View;II)V' in wrapper,
         "Fullscreen watermark gated by the overlay size"),
        ('const-string v12, "generate_unique_name"' in dialog
         and 'setNeutralButton' in dialog,
         "Downloads: unique name default + explicit overwrite"),
        (':cond_c_missing' in dialog and 'forgetMission' in dialog,
         "Downloads: stale finished missions are forgotten"),
        ('SafeTruncate;->run(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V' in dialog,
         "Downloads: truncate goes through the recovery helper"),
        ((root / "res/drawable/tyt_reel_back_animation.xml").is_file(),
         "Shorts animation-list resource written"),
        (len(list((root / "res/drawable-xxhdpi").glob("tyt_brand_*.png"))) == 8,
         "Shorts brand frames installed"),
    ]
    for ok, msg in checks:
        if not ok:
            print(f"FAIL: post-condition: {msg}", file=sys.stderr)
            return 1
        print(f"OK: post-condition: {msg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
