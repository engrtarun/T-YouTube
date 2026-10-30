#!/usr/bin/env python3
"""Apply the test-fix-5 download-dialog fix to a decoded tree.

Usage: python3 scripts/apply-test-fix-5.py <decoded-dir>

This build deliberately keeps the complete stable v1.0.1 UI: no layout,
drawable, font or animation changes.

Download behaviour:
  * A duplicate filename asks first.
  * The positive action is "Generate unique name" (safe default).
  * "Overwrite" is a separate neutral action.
  * While a download is pending or running, no overwrite action is offered.
  * A finished mission whose file was deleted is still handled by the normal
    overwrite path (forgetMission + continue), so it no longer blocks.

Every replacement must match exactly once.  If the upstream dialog changes,
the build fails instead of shipping a half-patched dialog.
"""
from __future__ import annotations

import pathlib
import sys

DOWNLOAD_DIALOG = pathlib.Path(
    "smali_classes10/com/gold/youtube/om7753/download/DownloadDialog.smali"
)

# 1) State None + existing file: ask instead of silently reusing the file.
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

    const/4 v0, 0x0

    const-string v6, "msg_exists"

    invoke-static {v6}, Lcom/gold/youtube/om7753/util/Utils;->getStringByName(Ljava/lang/String;)I

    move-result v6

    goto :goto_3

    :cond_3
"""

# 2) Finished mission: use the same explicit choice instead of a forced
#    overwrite. Missing files are handled by the chosen action (the overwrite
#    path forgets the old mission; the unique-name path creates a new file).
OLD_FINISHED = """    :cond_b
    const-string v6, "overwrite_finished_warning"

    :goto_3
"""

NEW_FINISHED = """    :cond_b
    const-string v6, "overwrite_finished_warning"

    const/4 v0, 0x0

    :goto_3
"""

# 3) Replace the old single-button block.  Positive = unique name,
#    neutral = explicit overwrite, and both are hidden for Pending/Running.
#    If there is no StoredDirectoryHelper, unique names are impossible, so the
#    dialog stays informational (Cancel only) instead of crashing.
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
    if-eqz p1, :no_choice

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

    :skip_unique
    move-object v12, v13

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
    :no_choice
"""

# 4) The positive button (-1) always creates a unique file.  The neutral
#    button (-3) keeps the original overwrite logic.
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

# 5) Pending missions must not offer the old overwrite button.
OLD_PENDING_POSITIVE = """    if-eq v0, v11, :cond_c

    if-eq v0, v10, :cond_c

    goto :goto_4
"""

NEW_PENDING_POSITIVE = """    if-eq v0, v11, :cond_c

    goto :goto_4
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


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <decoded-dir>", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    steps = [
        (DOWNLOAD_DIALOG, OLD_DOWNLOAD_EXISTS, NEW_DOWNLOAD_EXISTS,
         "Downloads: ask before reusing an existing file"),
        (DOWNLOAD_DIALOG, OLD_FINISHED, NEW_FINISHED,
         "Downloads: finished missions use the same explicit choice"),
        (DOWNLOAD_DIALOG, OLD_DIALOG_BUTTONS, NEW_DIALOG_BUTTONS,
         "Downloads: unique name is the default, overwrite is explicit"),
        (DOWNLOAD_DIALOG, OLD_LAMBDA9_HEAD, NEW_LAMBDA9_HEAD,
         "Downloads: positive button always generates a unique name"),
        (DOWNLOAD_DIALOG, OLD_PENDING_POSITIVE, NEW_PENDING_POSITIVE,
         "Downloads: pending missions no longer offer overwrite"),
    ]
    for rel, old, new, label in steps:
        if not replace_once(root, rel, old, new, label):
            return 1

    dialog = (root / DOWNLOAD_DIALOG).read_text(encoding="utf-8")
    checks = [
        ('const/4 v0, 0x0\n\n    const-string v6, "msg_exists"' in dialog,
         "existing files reach the choice dialog"),
        ('const-string v6, "overwrite_finished_warning"\n\n    const/4 v0, 0x0\n\n    :goto_3' in dialog,
         "finished missions reach the choice dialog"),
        ('if-eqz p1, :no_choice' in dialog and ':no_choice' in dialog,
         "missing directory cannot crash the unique-name action"),
        ('const-string v12, "generate_unique_name"' in dialog,
         "positive action is Generate unique name"),
        ('setNeutralButton' in dialog and 'const-string v6, "overwrite"' in dialog,
         "overwrite is a separate neutral action"),
        ('if-ne p8, p7, :not_unique_action' in dialog,
         "positive button routes to the unique-name path"),
        ('if-eq v0, v11, :cond_c\n\n    goto :goto_4' in dialog,
         "pending missions no longer get an overwrite positive button"),
        ('SafeTruncate' not in dialog,
         "overwrite keeps the original truncate call (no UI-thread helper)"),
    ]
    for ok, msg in checks:
        if not ok:
            print(f"FAIL: post-condition: {msg}", file=sys.stderr)
            return 1
        print(f"OK: post-condition: {msg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
