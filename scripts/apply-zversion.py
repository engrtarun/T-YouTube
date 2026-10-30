#!/usr/bin/env python3
"""Apply the T YouTube Zversion patches to a decoded v1.0.1 tree.

Usage: python3 scripts/apply-zversion.py <decoded-dir>

Zversion 2 is a separate test build on top of stable v1.0.1. It adds:

  * Shorts back control: an 8-second "T YouTube" brand loop
    (4.8s arrow, 225ms crossfade, 2.75s wordmark, 225ms crossfade),
    hosted by a custom ImageView. The loop restarts when the whole header
    becomes visible (onVisibilityAggregated/onLayout), not only when the
    button's own visibility changes.
  * Fullscreen-only "T YouTube" watermark in BOTH bottom-control layouts
    the app can inflate at runtime (legacy and video-exploder), gated by
    the fullscreen container (with an overlay-height fallback) and hidden
    with the controls.
  * Downloads: duplicate finished names are renamed automatically with
    the app's own createUniqueFile() logic, with no "Generate unique name"
    dialog and no extra tap. Pending/Running missions still show the
    informational dialog and are never overwritten.

Every replacement is checked for an exact single match. The script also
runs post-condition checks and exits non-zero if any anchor is missing, so
an upstream APK change can never silently produce a half-patched build.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent
ASSETS = REPO / "assets" / "test-fix-4"

SHORTS_LAYOUT = pathlib.Path("res/layout/reel_player_static_header.xml")
CONTROLS_LAYOUT = pathlib.Path("res/layout/youtube_controls_bottom_ui_container.xml")
EXPLODER_CONTROLS_LAYOUT = pathlib.Path(
    "res/layout/youtube_video_exploder_controls_bottom_ui_container.xml"
)
DOWNLOAD_DIALOG = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/download/DownloadDialog.smali"
)
BRAND_DIR = pathlib.Path("smali_classes10/com/gold/extension/youtube/brand")
DOWNLOAD_DIR = pathlib.Path("smali_classes10/com/gold/youtube/om7753/download")

CHECK_METHOD = (
    ".method private checkSelectedDownload("
    "Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;"
    "Landroid/net/Uri;Ljava/lang/String;Ljava/lang/String;)V"
)
# ---------------------------------------------------------------- Shorts ---

NEW_BACK_ELEMENT = (
    '<com.gold.extension.youtube.brand.ZVersionReelBackView '
    'android:id="@id/reel_back_button" '
    'android:background="@drawable/tyt_reel_back_animation" '
    'android:foreground="@drawable/tyt_reel_back_foreground" '
    'android:visibility="gone" android:layout_width="128.0dip" '
    'android:layout_height="48.0dip" android:layout_alignParentTop="true" '
    'android:contentDescription="@string/reel_accessibility_player_back_button" '
    'android:layout_marginStart="@dimen/reel_header_back_button_margin_start" '
    'android:layout_alignParentStart="true" />'
)

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

REEL_BACK_SMALI_V2 = """.class public final Lcom/gold/extension/youtube/brand/ZVersionReelBackView;
.super Landroid/widget/ImageView;


# instance fields
.field private aggregatedVisible:Z


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 0

    invoke-direct {p0, p1}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0

    invoke-direct {p0, p1, p2}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 0

    invoke-direct {p0, p1, p2, p3}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V
    .locals 0

    invoke-direct {p0, p1, p2, p3, p4}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V

    return-void
.end method

.method private restartBrandAnimation()V
    .locals 2

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->getVisibility()I

    move-result v0

    if-nez v0, :done

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->getBackground()Landroid/graphics/drawable/Drawable;

    move-result-object v0

    if-eqz v0, :done

    instance-of v1, v0, Landroid/graphics/drawable/AnimationDrawable;

    if-eqz v1, :done

    check-cast v0, Landroid/graphics/drawable/AnimationDrawable;

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->isRunning()Z

    move-result v1

    if-eqz v1, :not_running

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->stop()V

    :not_running
    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/graphics/drawable/AnimationDrawable;->selectDrawable(I)Z

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->start()V

    :done
    return-void
.end method

.method private stopBrandAnimation()V
    .locals 2

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->getBackground()Landroid/graphics/drawable/Drawable;

    move-result-object v0

    if-eqz v0, :done

    instance-of v1, v0, Landroid/graphics/drawable/AnimationDrawable;

    if-eqz v1, :done

    check-cast v0, Landroid/graphics/drawable/AnimationDrawable;

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->isRunning()Z

    move-result v1

    if-nez v1, :done

    invoke-virtual {v0}, Landroid/graphics/drawable/AnimationDrawable;->stop()V

    :done
    return-void
.end method

.method protected onAttachedToWindow()V
    .locals 1

    invoke-super {p0}, Landroid/widget/ImageView;->onAttachedToWindow()V

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :done

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    :done
    return-void
.end method

.method protected onDetachedFromWindow()V
    .locals 1

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->stopBrandAnimation()V

    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-super {p0}, Landroid/widget/ImageView;->onDetachedFromWindow()V

    return-void
.end method

.method protected onVisibilityChanged(Landroid/view/View;I)V
    .locals 1

    invoke-super {p0, p1, p2}, Landroid/widget/ImageView;->onVisibilityChanged(Landroid/view/View;I)V

    if-nez p2, :hidden

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :done

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    return-void

    :hidden
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->stopBrandAnimation()V

    :done
    return-void
.end method

.method public onVisibilityAggregated(Z)V
    .locals 1

    invoke-super {p0, p1}, Landroid/widget/ImageView;->onVisibilityAggregated(Z)V

    if-eqz p1, :hidden

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    if-eqz v0, :done

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    return-void

    :hidden
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->stopBrandAnimation()V

    :done
    return-void
.end method

.method protected onWindowVisibilityChanged(I)V
    .locals 1

    invoke-super {p0, p1}, Landroid/widget/ImageView;->onWindowVisibilityChanged(I)V

    if-nez p1, :hidden

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :done

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    return-void

    :hidden
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->stopBrandAnimation()V

    :done
    return-void
.end method

.method protected onLayout(ZIIII)V
    .locals 1

    invoke-super/range {p0 .. p5}, Landroid/widget/ImageView;->onLayout(ZIIII)V

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :not_shown

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    if-eqz v0, :done

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    return-void

    :not_shown
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->stopBrandAnimation()V

    :done
    return-void
.end method

.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 1

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :draw

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    if-eqz v0, :draw

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    :draw
    invoke-super {p0, p1}, Landroid/widget/ImageView;->onDraw(Landroid/graphics/Canvas;)V

    return-void
.end method
"""


# ------------------------------------------------ Fullscreen watermark ---

CONTROLS_CLOSING_TAG = "</androidx.constraintlayout.widget.ConstraintLayout>"


def watermark_element(ns: str, end_anchor: str) -> str:
    """Build the controls-only watermark for one bottom-bar variant."""
    return (
        '<com.gold.extension.youtube.brand.ZVersionWatermark '
        'android:textSize="18.0sp" android:textColor="@android:color/white" '
        'android:gravity="center" android:tag="tyt_watermark" '
        'android:visibility="invisible" android:layout_width="0.0dip" '
        'android:layout_height="60.0dip" android:text="T YouTube" '
        'android:alpha="0.8" android:maxLines="1" android:ellipsize="end" '
        'android:importantForAccessibility="no" android:clickable="false" '
        'android:focusable="false" '
        f'{ns}:layout_constraintBottom_toTopOf="@id/quick_actions_container" '
        f'{ns}:layout_constraintEnd_toStartOf="{end_anchor}" '
        f'{ns}:layout_constraintStart_toEndOf="@id/timestamps_container" '
        f'{ns}:youTubeSansFont="bold" />'
    )

WATERMARK_SMALI = """.class public final Lcom/gold/extension/youtube/brand/ZVersionWatermark;
.super Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;
.implements Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;


# instance fields
.field private listenerAttached:Z


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 0

    invoke-direct {p0, p1}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;-><init>(Landroid/content/Context;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0

    invoke-direct {p0, p1, p2}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 0

    invoke-direct {p0, p1, p2, p3}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V
    .locals 0

    invoke-direct {p0, p1, p2, p3, p4}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V

    return-void
.end method

.method private isFullscreen()Z
    .locals 4

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getRootView()Landroid/view/View;

    move-result-object v0

    if-eqz v0, :height_check

    const v1, 0x7f0b0867

    invoke-virtual {v0, v1}, Landroid/view/View;->findViewById(I)Landroid/view/View;

    move-result-object v1

    if-eqz v1, :height_check

    move-object v2, p0

    :ancestor_loop
    if-ne v2, v1, :fullscreen

    invoke-virtual {v2}, Landroid/view/View;->getParent()Landroid/view/ViewParent;

    move-result-object v2

    if-eqz v2, :height_check

    instance-of v0, v2, Landroid/view/View;

    if-eqz v0, :height_check

    check-cast v2, Landroid/view/View;

    goto :ancestor_loop

    :fullscreen
    const/4 v0, 0x1

    return v0

    :height_check
    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getRootView()Landroid/view/View;

    move-result-object v0

    if-eqz v0, :not_fullscreen

    const v1, 0x7f0b18a0

    invoke-virtual {v0, v1}, Landroid/view/View;->findViewById(I)Landroid/view/View;

    move-result-object v1

    if-eqz v1, :not_fullscreen

    invoke-virtual {v1}, Landroid/view/View;->getVisibility()I

    move-result v2

    if-eqz v2, :not_fullscreen

    invoke-virtual {v1}, Landroid/view/View;->getHeight()I

    move-result v2

    mul-int/lit8 v2, v2, 0x4

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getResources()Landroid/content/res/Resources;

    move-result-object v3

    invoke-virtual {v3}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v3

    iget v3, v3, Landroid/util/DisplayMetrics;->heightPixels:I

    mul-int/lit8 v3, v3, 0x3

    if-lt v2, v3, :fullscreen

    :not_fullscreen
    const/4 v0, 0x0

    return v0
.end method

.method private updateVisibility()V
    .locals 2

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->isFullscreen()Z

    move-result v0

    if-eqz v0, :hide

    const/4 v0, 0x0

    goto :set

    :hide
    const/4 v0, 0x4

    :set
    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getVisibility()I

    move-result v1

    if-eq v1, v0, :done

    invoke-virtual {p0, v0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->setVisibility(I)V

    :done
    return-void
.end method

.method protected onAttachedToWindow()V
    .locals 1

    invoke-super {p0}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;->onAttachedToWindow()V

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->listenerAttached:Z

    if-eqz v0, :done

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getViewTreeObserver()Landroid/view/ViewTreeObserver;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/ViewTreeObserver;->addOnGlobalLayoutListener(Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;)V

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->listenerAttached:Z

    :done
    return-void
.end method

.method protected onDetachedFromWindow()V
    .locals 1

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->listenerAttached:Z

    if-eqz v0, :skip

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getViewTreeObserver()Landroid/view/ViewTreeObserver;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/ViewTreeObserver;->removeOnGlobalLayoutListener(Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;)V

    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->listenerAttached:Z

    :skip
    invoke-super {p0}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;->onDetachedFromWindow()V

    return-void
.end method

.method public onGlobalLayout()V
    .locals 0

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->updateVisibility()V

    return-void
.end method
"""

# ----------------------------------------------------- Download dialog ---

NEW_CHECK_METHOD = """.method private checkSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Landroid/net/Uri;Ljava/lang/String;Ljava/lang/String;)V
    .locals 10

    :try_start_0
    if-nez p1, :dir_null

    if-nez p2, :dir_uri

    new-instance v0, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    iget-object v1, p0, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    invoke-virtual {p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getUri()Landroid/net/Uri;

    move-result-object v2

    invoke-virtual {p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getTag()Ljava/lang/String;

    move-result-object v3

    invoke-direct {v0, v1, v2, p2, v3}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/content/Context;Landroid/net/Uri;Landroid/net/Uri;Ljava/lang/String;)V

    goto :target_ready

    :dir_null
    new-instance v0, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    iget-object v1, p0, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    const-string v2, ""

    const/4 v3, 0x0

    invoke-direct {v0, v1, v3, p2, v2}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/content/Context;Landroid/net/Uri;Landroid/net/Uri;Ljava/lang/String;)V

    goto :target_ready

    :dir_uri
    new-instance v0, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    invoke-virtual {p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getUri()Landroid/net/Uri;

    move-result-object v1

    invoke-virtual {p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getTag()Ljava/lang/String;

    move-result-object v2

    invoke-direct {v0, v1, p3, p4, v2}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/net/Uri;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V

    :target_ready
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_target

    goto :check_state

    :catch_target
    return-void

    :check_state
    iget-object v1, p0, Lcom/gold/youtube/om7753/download/DownloadDialog;->downloadManager:Lus/shandian/giga/service/DownloadManager;

    invoke-virtual {v1, v0}, Lus/shandian/giga/service/DownloadManager;->checkForExistingMission(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)Lus/shandian/giga/service/MissionState;

    move-result-object v1

    sget-object v2, Lcom/gold/youtube/om7753/download/DownloadDialog$3;->$SwitchMap$us$shandian$giga$service$MissionState:[I

    invoke-virtual {v1}, Ljava/lang/Enum;->ordinal()I

    move-result v3

    aget v2, v2, v3

    const/4 v3, 0x2

    if-ne v2, v3, :not_pending

    const-string v3, "download_already_pending"

    goto :show_info

    :not_pending
    const/4 v3, 0x3

    if-ne v2, v3, :not_running

    const-string v3, "download_already_running"

    goto :show_info

    :not_running
    const/4 v3, 0x1

    if-ne v2, v3, :not_finished

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v3

    if-nez v3, :finished_missing

    if-eqz p1, :create_target

    goto :make_unique

    :finished_missing
    iget-object v3, p0, Lcom/gold/youtube/om7753/download/DownloadDialog;->downloadManager:Lus/shandian/giga/service/DownloadManager;

    invoke-virtual {v3, v0}, Lus/shandian/giga/service/DownloadManager;->forgetMission(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    goto :create_target

    :not_finished
    if-eqz p1, :create_target

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v3

    if-nez v3, :create_target

    goto :make_unique

    :show_info
    new-instance v4, Landroid/app/AlertDialog$Builder;

    iget-object v5, p0, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    invoke-static {v5}, Lcom/gold/youtube/om7753/RouterActivity;->getThemeWrapperContext(Landroid/content/Context;)Landroid/content/Context;

    move-result-object v5

    invoke-direct {v4, v5}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    const-string v5, "download_dialog_title"

    invoke-static {v5}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v5

    invoke-virtual {v4, v5}, Landroid/app/AlertDialog$Builder;->setTitle(I)Landroid/app/AlertDialog$Builder;

    move-result-object v4

    invoke-static {v3}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v3

    invoke-virtual {v4, v3}, Landroid/app/AlertDialog$Builder;->setMessage(I)Landroid/app/AlertDialog$Builder;

    move-result-object v4

    const/high16 v5, 0x1040000

    const/4 v6, 0x0

    invoke-virtual {v4, v5, v6}, Landroid/app/AlertDialog$Builder;->setNegativeButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object v4

    invoke-virtual {v4}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;

    move-result-object v4

    invoke-virtual {v4}, Landroid/app/AlertDialog;->show()V

    return-void

    :make_unique
    :try_start_unique
    invoke-virtual {p1, p3, p4}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->createUniqueFile(Ljava/lang/String;Ljava/lang/String;)Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    move-result-object v0
    :try_end_unique
    .catch Ljava/lang/Exception; {:try_start_unique .. :try_end_unique} :catch_unique

    if-eqz v0, :have_target

    goto :file_creation_failed

    :catch_unique
    move-exception v0

    goto :file_creation_failed

    :create_target
    if-eqz p1, :create_save_as

    if-nez p2, :create_folder

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v1

    if-eqz v1, :have_target

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->create()Z

    move-result v1

    if-eqz v1, :have_target

    goto :file_creation_failed

    :create_folder
    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v1

    if-eqz v1, :have_target

    invoke-virtual {p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->mkdirs()Z

    move-result v1

    if-eqz v1, :folder_ready

    const-string v1, "error_path_creation"

    invoke-static {v1}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v1

    invoke-direct {p0, v1}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :folder_ready
    invoke-virtual {p1, p3, p4}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->createFile(Ljava/lang/String;Ljava/lang/String;)Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    move-result-object v0

    if-eqz v0, :have_target

    goto :file_creation_failed

    :create_save_as
    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v1

    if-eqz v1, :have_target

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->create()Z

    move-result v1

    if-eqz v1, :have_target

    :file_creation_failed
    const-string v1, "error_file_creation"

    invoke-static {v1}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v1

    invoke-direct {p0, v1}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :have_target
    invoke-direct {p0, v0}, Lcom/gold/youtube/om7753/download/DownloadDialog;->continueSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    return-void
.end method
"""

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


def replace_line_containing(root: pathlib.Path, rel: pathlib.Path, needle: str,
                            new_line: str, label: str) -> bool:
    path = root / rel
    if not path.is_file():
        print(f"FAIL: {label}: missing {path}", file=sys.stderr)
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if needle in line]
    if len(hits) != 1:
        print(f"FAIL: {label}: expected 1 line containing {needle!r} in "
              f"{path}, found {len(hits)}", file=sys.stderr)
        return False
    old = lines[hits[0]]
    ending = "\n" if old.endswith("\n") else ""
    lines[hits[0]] = new_line + ending
    path.write_text("".join(lines), encoding="utf-8")
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
    end = text.index(".end method", start)
    end += len(".end method")
    old_method = text[start:end]
    for needle in required:
        if needle not in old_method:
            print(f"FAIL: {label}: old method is missing {needle!r}",
                  file=sys.stderr)
            return False
    path.write_text(text[:start] + new_method + text[end:], encoding="utf-8")
    print(f"OK: {label}")
    return True


def write_new(root: pathlib.Path, rel: pathlib.Path, content: str,
              label: str) -> bool:
    path = root / rel
    if path.exists():
        print(f"FAIL: {label}: refusing to overwrite existing {path}",
              file=sys.stderr)
        return False
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
        print(f"FAIL: expected 8 brand frames, found {len(frames)}",
              file=sys.stderr)
        return False
    for src in frames:
        dst = drawable / src.name
        if dst.exists():
            print(f"FAIL: brand frame already exists: {dst}", file=sys.stderr)
            return False
        shutil.copyfile(src, dst)
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

    if not replace_line_containing(
        root, SHORTS_LAYOUT, 'android:id="@id/reel_back_button"',
        "    " + NEW_BACK_ELEMENT,
        "Shorts: replace the back ImageView with the brand-loop view",
    ):
        return 1
    if not replace_once(
        root, SHORTS_LAYOUT, OLD_TITLE_ANCHOR, NEW_TITLE_ANCHOR,
        "Shorts: pin the contextual title at its old 65dp position",
    ):
        return 1
    if not replace_once(
        root, CONTROLS_LAYOUT, CONTROLS_CLOSING_TAG,
        "    " + watermark_element("app", "@id/bottom_end_container") + "\n"
        + CONTROLS_CLOSING_TAG,
        "Fullscreen: add the watermark to the legacy bottom control row",
    ):
        return 1
    if not replace_once(
        root, EXPLODER_CONTROLS_LAYOUT, CONTROLS_CLOSING_TAG,
        "    " + watermark_element("yt", "@id/bottom_end_container") + "\n"
        + CONTROLS_CLOSING_TAG,
        "Fullscreen: add the watermark to the exploder bottom control row",
    ):
        return 1

    if not replace_method(
        root, DOWNLOAD_DIALOG, CHECK_METHOD, NEW_CHECK_METHOD,
        (
            "checkForExistingMission",
            "overwrite_finished_warning",
            "overwrite_unrelated_warning",
            "continueSelectedDownload",
        ),
        "Downloads: replace the duplicate-name state machine",
    ):
        return 1

    if not write_new(root, BRAND_DIR / "ZVersionReelBackView.smali",
                     REEL_BACK_SMALI_V2, "Shorts: custom brand-loop view"):
        return 1
    if not write_new(root, BRAND_DIR / "ZVersionWatermark.smali",
                     WATERMARK_SMALI, "Fullscreen: custom watermark view"):
        return 1
    if not write_new(root, pathlib.Path("res/drawable/tyt_reel_back_animation.xml"),
                     ANIMATION_XML, "Shorts: write the 8s animation-list"):
        return 1
    if not write_new(root, pathlib.Path("res/drawable/tyt_reel_back_foreground.xml"),
                     FOREGROUND_XML, "Shorts: write the 48dp ripple foreground"):
        return 1
    if not copy_brand_frames(root):
        return 1

    # ---------------------------------------------------- post-conditions ---
    shorts = (root / SHORTS_LAYOUT).read_text(encoding="utf-8")
    legacy = (root / CONTROLS_LAYOUT).read_text(encoding="utf-8")
    exploder = (root / EXPLODER_CONTROLS_LAYOUT).read_text(encoding="utf-8")
    dialog = (root / DOWNLOAD_DIALOG).read_text(encoding="utf-8")
    dialog_start = dialog.index(CHECK_METHOD)
    dialog_end = dialog.index(".end method", dialog_start)
    check_method = dialog[dialog_start:dialog_end]

    def has_watermark(text: str, ns: str) -> bool:
        return (
            'com.gold.extension.youtube.brand.ZVersionWatermark' in text
            and 'android:tag="tyt_watermark"' in text
            and 'android:textSize="18.0sp"' in text
            and 'android:alpha="0.8"' in text
            and 'android:textColor="@android:color/white"' in text
            and f'{ns}:youTubeSansFont="bold"' in text
            and f'{ns}:layout_constraintStart_toEndOf="@id/timestamps_container"' in text
            and f'{ns}:layout_constraintEnd_toStartOf="@id/bottom_end_container"' in text
        )

    checks = [
        (
            'com.gold.extension.youtube.brand.ZVersionReelBackView' in shorts
            and 'android:layout_width="128.0dip"' in shorts
            and 'android:layout_height="48.0dip"' in shorts
            and 'android:background="@drawable/tyt_reel_back_animation"' in shorts
            and 'android:contentDescription="@string/reel_accessibility_player_back_button"' in shorts,
            "Shorts back control is a 128x48 brand-loop target",
        ),
        (
            'android:layout_marginStart="65.0dip"' in shorts
            and 'android:layout_toEndOf="@id/reel_back_button"' not in shorts,
            "Shorts title is pinned at its old position",
        ),
        (
            has_watermark(legacy, "app"),
            "Fullscreen watermark is in the legacy bottom control row",
        ),
        (
            has_watermark(exploder, "yt"),
            "Fullscreen watermark is in the exploder bottom control row",
        ),
        (
            'createUniqueFile' in check_method
            and 'download_already_pending' in check_method
            and 'download_already_running' in check_method
            and 'forgetMission' in check_method
            and 'continueSelectedDownload' in check_method
            and 'generate_unique_name' not in check_method
            and 'overwrite' not in check_method
            and 'ZVersionDownloadUniqueAction' not in check_method
            and 'startUniqueDownload' not in check_method,
            "Downloads: finished duplicates auto-rename; active missions are guarded",
        ),
        (
            'ZVersionDownloadUniqueAction' not in dialog
            and 'startUniqueDownload' not in dialog,
            "Downloads: the broken Generate unique name action is gone",
        ),
        (
            (root / BRAND_DIR / "ZVersionReelBackView.smali").is_file()
            and (root / BRAND_DIR / "ZVersionWatermark.smali").is_file()
            and not (root / DOWNLOAD_DIR / "ZVersionDownloadUniqueAction.smali").exists(),
            "New Zversion smali classes are installed",
        ),
        (
            (root / "res/drawable/tyt_reel_back_animation.xml").is_file()
            and (root / "res/drawable/tyt_reel_back_foreground.xml").is_file()
            and len(list((root / "res/drawable-xxhdpi").glob("tyt_brand_*.png"))) == 8,
            "Shorts animation resources and 8 brand frames are installed",
        ),
    ]
    for ok, msg in checks:
        if not ok:
            print(f"FAIL: post-condition: {msg}", file=sys.stderr)
            return 1
        print(f"OK: post-condition: {msg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
