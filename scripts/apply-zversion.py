#!/usr/bin/env python3
"""Apply the T YouTube Zversion patches to a decoded v1.0.1 tree.

Usage: python3 scripts/apply-zversion.py <decoded-dir>

Zversion 4 is a separate test build on top of stable v1.0.1. It adds:

  * Shorts back control: an 8-second "T YouTube" brand loop
    (4.8s arrow, 225ms crossfade, 2.75s wordmark, 225ms crossfade),
    hosted by a custom ImageView. BOTH layouts that carry a
    reel_back_button get it: reel_player_static_header.xml and
    reel_player_back_button.xml - the second one still shipped a plain
    white arrow with the same view id, so findViewById() could hand the
    player the arrow instead of the loop. onWindowFocusChanged restarts
    the AnimationDrawable once the view really is attached, so the loop
    can no longer freeze on the opening arrow.
  * Fullscreen-only "T YouTube" watermark in BOTH bottom-control layouts
    the app can inflate at runtime (legacy and video-exploder). It sits
    at the bottom of the control row (below the scrubber line) at 14sp,
    and onVisibilityChanged hides it the moment the controls overlay
    hides - no waiting for the next global layout pass.
  * Downloads: stable v1.0.1's proven checkSelectedDownload is restored
    unchanged (Zversion 3 rewrote it with inverted conditionals, so even
    the first download failed). Two surgical additions on top: an
    existing file with no mission and a finished mission both fall
    through to the app's own createUniqueFile() and start downloading
    immediately, so a duplicate needs no taps and never overwrites.
    Pending and running missions only show a cancel-only dialog and are
    never overwritten. The dialog still starts with the real video
    title.

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
# Shorts has a SECOND view with the same id (a plain white arrow) that is
# <include>d by reel_non_video_page*.xml and reel_watch_survey_page.xml.
# It must carry the brand loop too, otherwise findViewById() can hand the
# plain arrow to the player code and the loop never shows.
BACK_BUTTON_LAYOUT = pathlib.Path("res/layout/reel_player_back_button.xml")
CONTROLS_LAYOUT = pathlib.Path("res/layout/youtube_controls_bottom_ui_container.xml")
EXPLODER_CONTROLS_LAYOUT = pathlib.Path(
    "res/layout/youtube_video_exploder_controls_bottom_ui_container.xml"
)
DOWNLOAD_DIALOG = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/download/DownloadDialog.smali"
)
FILENAME_UTILS = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/util/FilenameUtils.smali"
)
ABOUT_PREFS = pathlib.Path("res/xml/youtube_prefs.xml")
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

    if-nez v0, :done

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

# AnimationDrawable.start() called while the view is still detached can drop
# the first frame callback and freeze the loop on the opening arrow, which is
# exactly the "Shorts still shows <--" symptom. Restarting once we really
# have window focus guarantees the 8s loop is scheduled.
.method public onWindowFocusChanged(Z)V
    .locals 1

    invoke-super {p0, p1}, Landroid/widget/ImageView;->onWindowFocusChanged(Z)V

    if-eqz p1, :no_focus

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :no_focus

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->restartBrandAnimation()V

    :no_focus
    return-void
.end method

.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 1

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->isShown()Z

    move-result v0

    if-nez v0, :draw

    iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionReelBackView;->aggregatedVisible:Z

    if-nez v0, :draw

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
    """Build the controls-only watermark for one bottom-bar variant.

    Anchored to the bottom of the control row (below the scrubber line) and
    kept short so it never pushes the controls around.
    """
    return (
        '<com.gold.extension.youtube.brand.ZVersionWatermark '
        'android:textSize="14.0sp" android:textColor="@android:color/white" '
        'android:gravity="center" android:tag="tyt_watermark" '
        'android:visibility="invisible" android:layout_width="0.0dip" '
        'android:layout_height="32.0dip" android:text="T YouTube" '
        'android:alpha="0.8" android:maxLines="1" android:ellipsize="end" '
        'android:importantForAccessibility="no" android:clickable="false" '
        'android:focusable="false" android:layout_marginBottom="4.0dip" '
        f'{ns}:layout_constraintBottom_toBottomOf="parent" '
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

    if-nez v0, :done

    invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->getViewTreeObserver()Landroid/view/ViewTreeObserver;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/ViewTreeObserver;->addOnGlobalLayoutListener(Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;)V

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->listenerAttached:Z

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->updateVisibility()V

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

# Fires the moment this view or ANY ancestor (the whole controls overlay)
# changes visibility, so the watermark disappears with the controls instead
# of waiting for the next global layout pass.
.method protected onVisibilityChanged(Landroid/view/View;I)V
    .locals 1

    invoke-super {p0, p1, p2}, Lcom/google/android/libraries/youtube/common/ui/YouTubeTextView;->onVisibilityChanged(Landroid/view/View;I)V

    if-nez p2, :ancestor_hidden

    invoke-direct {p0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->updateVisibility()V

    return-void

    :ancestor_hidden
    const/4 v0, 0x4

    invoke-virtual {p0, v0}, Lcom/gold/extension/youtube/brand/ZVersionWatermark;->setVisibility(I)V

    return-void
.end method
"""

# ----------------------------------------------------- Download dialog ---

NEW_CHECK_METHOD = """
.method private checkSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Landroid/net/Uri;Ljava/lang/String;Ljava/lang/String;)V
    .locals 15

    move-object v9, p0

    move-object/from16 v0, p1

    move-object/from16 v5, p2

    move-object/from16 v7, p3

    move-object/from16 v8, p4

    const/4 v1, 0x0

    if-nez v0, :cond_0

    :try_start_0
    new-instance v2, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    iget-object v3, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    const-string v4, ""

    invoke-direct {v2, v3, v1, v5, v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/content/Context;Landroid/net/Uri;Landroid/net/Uri;Ljava/lang/String;)V

    :goto_0
    move-object v4, v2

    goto :goto_1

    :catch_0
    move-exception v0

    goto/16 :goto_5

    :cond_0
    if-nez v5, :cond_1

    new-instance v2, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getUri()Landroid/net/Uri;

    move-result-object v3

    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getTag()Ljava/lang/String;

    move-result-object v4

    invoke-direct {v2, v3, v7, v8, v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/net/Uri;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V

    goto :goto_0

    :cond_1
    new-instance v2, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    iget-object v3, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getUri()Landroid/net/Uri;

    move-result-object v4

    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->getTag()Ljava/lang/String;

    move-result-object v6

    invoke-direct {v2, v3, v4, v5, v6}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;-><init>(Landroid/content/Context;Landroid/net/Uri;Landroid/net/Uri;Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :goto_1
    iget-object v2, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->downloadManager:Lus/shandian/giga/service/DownloadManager;

    invoke-virtual {v2, v4}, Lus/shandian/giga/service/DownloadManager;->checkForExistingMission(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)Lus/shandian/giga/service/MissionState;

    move-result-object v3

    sget-object v2, Lcom/gold/youtube/om7753/download/DownloadDialog$3;->$SwitchMap$us$shandian$giga$service$MissionState:[I

    invoke-virtual {v3}, Ljava/lang/Enum;->ordinal()I

    move-result v6

    aget v6, v2, v6

    const/4 v10, 0x2

    const/4 v11, 0x1

    const-string v12, "overwrite"

    invoke-static {v12}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v12

    if-eq v6, v11, :cond_b

    if-eq v6, v10, :cond_a

    const/4 v13, 0x3

    if-eq v6, v13, :cond_9

    const/4 v13, 0x4

    if-eq v6, v13, :cond_2

    return-void

    :cond_2
    const-string v6, "error_file_creation"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    if-nez v0, :cond_4

    invoke-virtual {v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->existsAsFile()Z

    move-result v0

    if-nez v0, :cond_3

    invoke-virtual {v4}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->create()Z

    move-result v0

    if-nez v0, :cond_3

    invoke-direct {p0, v6}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :cond_3
    invoke-direct {p0, v4}, Lcom/gold/youtube/om7753/download/DownloadDialog;->continueSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    return-void

    :cond_4
    if-nez v5, :cond_8

    invoke-virtual/range {p1 .. p1}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->mkdirs()Z

    move-result v1

    if-nez v1, :cond_5

    const-string v0, "error_path_creation"

    invoke-static {v0}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v0

    invoke-direct {p0, v0}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :cond_5
    invoke-virtual {v0, v7, v8}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->createFile(Ljava/lang/String;Ljava/lang/String;)Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    move-result-object v0

    if-eqz v0, :cond_7

    invoke-virtual {v0}, Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;->canWrite()Z

    move-result v1

    if-nez v1, :cond_6

    goto :goto_2

    :cond_6
    invoke-direct {p0, v0}, Lcom/gold/youtube/om7753/download/DownloadDialog;->continueSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    return-void

    :cond_7
    :goto_2
    invoke-direct {p0, v6}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :cond_8

    :try_start_u1
    invoke-virtual {v0, v7, v8}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->createUniqueFile(Ljava/lang/String;Ljava/lang/String;)Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    move-result-object v13

    :try_end_u1
    .catch Ljava/lang/Exception; {:try_start_u1 .. :try_end_u1} :catch_u1

    if-nez v13, :ok_u1

    const-string v6, "error_file_creation"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    invoke-direct {p0, v6}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :ok_u1
    invoke-direct {p0, v13}, Lcom/gold/youtube/om7753/download/DownloadDialog;->continueSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    return-void

    :catch_u1
    const-string v6, "overwrite_unrelated_warning"

    goto :goto_3



    :cond_9

    const-string v6, "download_already_running"

    goto :info_dialog


    :cond_a

    const-string v6, "download_already_pending"

    goto :info_dialog


    :cond_b

    if-nez v0, :catch_u2
    :try_start_u2
    invoke-virtual {v0, v7, v8}, Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;->createUniqueFile(Ljava/lang/String;Ljava/lang/String;)Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;

    move-result-object v13

    :try_end_u2
    .catch Ljava/lang/Exception; {:try_start_u2 .. :try_end_u2} :catch_u2

    if-nez v13, :ok_u2

    const-string v6, "error_file_creation"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    invoke-direct {p0, v6}, Lcom/gold/youtube/om7753/download/DownloadDialog;->showFailedDialog(I)V

    return-void

    :ok_u2
    invoke-direct {p0, v13}, Lcom/gold/youtube/om7753/download/DownloadDialog;->continueSelectedDownload(Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    return-void

    :catch_u2
    const-string v6, "overwrite_finished_warning"



    :goto_3
    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    new-instance v13, Landroid/app/AlertDialog$Builder;

    iget-object v14, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    invoke-static {v14}, Lcom/gold/youtube/om7753/RouterActivity;->getThemeWrapperContext(Landroid/content/Context;)Landroid/content/Context;

    move-result-object v14

    invoke-direct {v13, v14}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    const-string v14, "download_dialog_title"

    invoke-static {v14}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v14

    invoke-virtual {v13, v14}, Landroid/app/AlertDialog$Builder;->setTitle(I)Landroid/app/AlertDialog$Builder;

    move-result-object v13

    invoke-virtual {v13, v6}, Landroid/app/AlertDialog$Builder;->setMessage(I)Landroid/app/AlertDialog$Builder;

    move-result-object v6

    const/high16 v13, 0x1040000

    invoke-virtual {v6, v13, v1}, Landroid/app/AlertDialog$Builder;->setNegativeButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object v13

    if-nez v0, :cond_d

    invoke-virtual {v3}, Ljava/lang/Enum;->ordinal()I

    move-result v0

    aget v0, v2, v0

    if-eq v0, v11, :cond_c

    if-eq v0, v10, :cond_c

    goto :goto_4

    :cond_c
    new-instance v0, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda12;

    invoke-direct {v0, p0, v4}, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda12;-><init>(Lcom/gold/youtube/om7753/download/DownloadDialog;Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;)V

    invoke-virtual {v13, v12, v0}, Landroid/app/AlertDialog$Builder;->setPositiveButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    :goto_4
    invoke-virtual {v13}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;

    move-result-object v0

    invoke-virtual {v0}, Landroid/app/Dialog;->show()V

    return-void

    :cond_d
    new-instance v10, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;

    move-object v1, v10

    move-object v2, p0

    move-object/from16 v5, p2

    move-object/from16 v6, p1

    move-object/from16 v7, p3

    move-object/from16 v8, p4

    invoke-direct/range {v1 .. v8}, Lcom/gold/youtube/om7753/download/DownloadDialog$$ExternalSyntheticLambda13;-><init>(Lcom/gold/youtube/om7753/download/DownloadDialog;Lus/shandian/giga/service/MissionState;Lcom/gold/youtube/om7753/streams/io/StoredFileHelper;Landroid/net/Uri;Lcom/gold/youtube/om7753/streams/io/StoredDirectoryHelper;Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v13, v12, v10}, Landroid/app/AlertDialog$Builder;->setPositiveButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    invoke-virtual {v13}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;

    move-result-object v0

    invoke-virtual {v0}, Landroid/app/Dialog;->show()V

    return-void

    :info_dialog
    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    new-instance v13, Landroid/app/AlertDialog$Builder;

    iget-object v14, v9, Lcom/gold/youtube/om7753/download/DownloadDialog;->context:Landroid/content/Context;

    invoke-static {v14}, Lcom/gold/youtube/om7753/RouterActivity;->getThemeWrapperContext(Landroid/content/Context;)Landroid/content/Context;

    move-result-object v14

    invoke-direct {v13, v14}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V

    const-string v14, "download_dialog_title"

    invoke-static {v14}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v14

    invoke-virtual {v13, v14}, Landroid/app/AlertDialog$Builder;->setTitle(I)Landroid/app/AlertDialog$Builder;

    move-result-object v13

    invoke-virtual {v13, v6}, Landroid/app/AlertDialog$Builder;->setMessage(I)Landroid/app/AlertDialog$Builder;

    move-result-object v13

    const/high16 v6, 0x1040000

    invoke-virtual {v13, v6, v1}, Landroid/app/AlertDialog$Builder;->setNegativeButton(ILandroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;

    move-result-object v13

    invoke-virtual {v13}, Landroid/app/AlertDialog$Builder;->create()Landroid/app/AlertDialog;

    move-result-object v0

    invoke-virtual {v0}, Landroid/app/Dialog;->show()V

    return-void

    :goto_5
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
    if not replace_line_containing(
        root, BACK_BUTTON_LAYOUT, 'android:id="@id/reel_back_button"',
        "    " + NEW_BACK_ELEMENT,
        "Shorts: replace the second (plain white arrow) back ImageView too",
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

    # v1.0.1 ships an inverted empty-name test here: every non-empty title
    # becomes "download".  Restore the intended fallback so the dialog starts
    # with the video title and createUniqueFile() can add " (1)", " (2)", ...
    if not replace_once(
        root, FILENAME_UTILS,
        '    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z\n'
        '\n'
        '    move-result p1\n'
        '\n'
        '    if-nez p1, :cond_0\n'
        '\n'
        '    const-string p0, "download"',
        '    invoke-virtual {p0}, Ljava/lang/String;->isEmpty()Z\n'
        '\n'
        '    move-result p1\n'
        '\n'
        '    if-eqz p1, :cond_0\n'
        '\n'
        '    const-string p0, "download"',
        "Downloads: use the video title instead of the literal 'download'",
    ):
        return 1

    if not replace_once(
        root, ABOUT_PREFS,
        'android:key="youtube_downloads_package_name" android:summary="21.20.402"',
        'android:key="youtube_downloads_package_name" '
        'android:summary="21.20.402 (v1.1.0)"',
        "About: add a visible v1.1.0 build marker",
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
    if not copy_brand_frames(root):
        return 1

    # ---------------------------------------------------- post-conditions ---
    shorts = (root / SHORTS_LAYOUT).read_text(encoding="utf-8")
    back_button = (root / BACK_BUTTON_LAYOUT).read_text(encoding="utf-8")
    legacy = (root / CONTROLS_LAYOUT).read_text(encoding="utf-8")
    exploder = (root / EXPLODER_CONTROLS_LAYOUT).read_text(encoding="utf-8")
    dialog = (root / DOWNLOAD_DIALOG).read_text(encoding="utf-8")
    filename_utils = (root / FILENAME_UTILS).read_text(encoding="utf-8")
    about_prefs = (root / ABOUT_PREFS).read_text(encoding="utf-8")
    brand_view = (root / BRAND_DIR / "ZVersionReelBackView.smali").read_text(
        encoding="utf-8"
    )
    watermark_view = (root / BRAND_DIR / "ZVersionWatermark.smali").read_text(
        encoding="utf-8"
    )
    dialog_start = dialog.index(CHECK_METHOD)
    dialog_end = dialog.index(".end method", dialog_start)
    check_method = dialog[dialog_start:dialog_end]

    def watermark_el(text: str) -> str:
        i = text.index("com.gold.extension.youtube.brand.ZVersionWatermark")
        return text[i:text.index("/>", i)]

    def has_watermark(text: str, ns: str) -> bool:
        el = watermark_el(text)
        return (
            'android:tag="tyt_watermark"' in el
            and 'android:textSize="14.0sp"' in el
            and 'android:layout_height="32.0dip"' in el
            and 'android:alpha="0.8"' in el
            and 'android:textColor="@android:color/white"' in el
            and f'{ns}:youTubeSansFont="bold"' in el
            and f'{ns}:layout_constraintBottom_toBottomOf="parent"' in el
            and "quick_actions_container" not in el
            and f'{ns}:layout_constraintStart_toEndOf="@id/timestamps_container"' in el
            and f'{ns}:layout_constraintEnd_toStartOf="@id/bottom_end_container"' in el
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
            'com.gold.extension.youtube.brand.ZVersionReelBackView' in back_button
            and 'android:background="@drawable/tyt_reel_back_animation"' in back_button
            and 'quantum_ic_arrow_back_white_24' not in back_button
            and 'android:foreground=' not in back_button
            and 'android:foreground=' not in shorts
            and 'quantum_ic_arrow_back_white_24' not in shorts,
            "Shorts: the second (same-id) back button carries the loop too",
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
            check_method.count("createUniqueFile") == 2
            and ":try_start_u1" in check_method
            and ":try_start_u2" in check_method
            and check_method.count("goto :info_dialog") == 2
            and ":info_dialog" in check_method
            and 'download_already_pending' in check_method
            and 'download_already_running' in check_method
            and 'overwrite_finished_warning' in check_method
            and 'continueSelectedDownload' in check_method
            and 'checkForExistingMission' in check_method
            and 'generate_unique_name' not in check_method
            and 'forgetMission' not in check_method
            and 'ZVersionDownloadUniqueAction' not in check_method
            and 'startUniqueDownload' not in check_method,
            "Downloads: v1.0.1 state machine restored + duplicates auto-rename",
        ),
        (
            'ZVersionDownloadUniqueAction' not in dialog
            and 'startUniqueDownload' not in dialog,
            "Downloads: the broken Generate unique name action is gone",
        ),
        (
            'if-eqz p1, :cond_0' in filename_utils
            and 'if-nez p1, :cond_0' not in filename_utils,
            "Downloads: the filename starts with the video title",
        ),
        (
            'invoke-virtual {p0}, Lcom/gold/extension/youtube/brand/'
            'ZVersionReelBackView;->getVisibility()I\n\n'
            '    move-result v0\n\n'
            '    if-nez v0, :done' in brand_view
            and brand_view.count(
                'iget-boolean v0, p0, Lcom/gold/extension/youtube/brand/'
                'ZVersionReelBackView;->aggregatedVisible:Z\n\n'
                '    if-nez v0'
            ) == 3
            and 'ZVersionReelBackView;->aggregatedVisible:Z\n\n'
                '    if-eqz v0' not in brand_view,
            "Shorts: the brand loop starts on the hidden-to-visible transition",
        ),
        (
            'android:summary="21.20.402 (v1.1.0)"' in about_prefs,
            "About: the v1.1.0 marker is visible",
        ),
        (
            'if-nez v0, :done' in watermark_view
            and 'if-eqz v0, :skip' in watermark_view
            and 'invoke-direct {p0}, Lcom/gold/extension/youtube/brand/'
                'ZVersionWatermark;->updateVisibility()V' in watermark_view
            and '.method protected onVisibilityChanged(Landroid/view/View;I)V'
                in watermark_view
            and '    :ancestor_hidden' in watermark_view,
            "Fullscreen: the watermark hides with the controls, not a layout pass later",
        ),
        (
            '.method public onWindowFocusChanged(Z)V' in brand_view
            and 'restartBrandAnimation()V' in brand_view,
            "Shorts: the loop is restarted once the view really has focus",
        ),
        (
            (root / BRAND_DIR / "ZVersionReelBackView.smali").is_file()
            and (root / BRAND_DIR / "ZVersionWatermark.smali").is_file()
            and not (root / DOWNLOAD_DIR / "ZVersionDownloadUniqueAction.smali").exists(),
            "New Zversion smali classes are installed",
        ),
        (
            (root / "res/drawable/tyt_reel_back_animation.xml").is_file()
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
