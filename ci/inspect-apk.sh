#!/usr/bin/env bash
# Read-only inspection of a decoded T YouTube APK tree.
# Usage: bash ci/inspect-apk.sh <decoded-dir> <output-dir>
set -euo pipefail

ROOT="${1:?decoded dir required}"
OUT="${2:?output dir required}"

mkdir -p "$OUT"
cd "$ROOT"

MANIFEST="AndroidManifest.xml"
[ -f "$MANIFEST" ] || { echo "AndroidManifest.xml not found in $ROOT" >&2; exit 1; }

{
  echo "# T YouTube APK inspection"
  echo
  echo "- Generated: $(date -u +%FT%TZ)"
  echo "- Base APK SHA-256: ${BASE_APK_SHA256:-unknown}"
  echo "- Decoded with: apktool ${APKTOOL_VERSION:-unknown}"
  echo

  echo "## Launcher activities"
  grep -n -B 10 -A 5 'android.intent.category.LAUNCHER' "$MANIFEST" || true
  echo

  echo "## Application element"
  grep -n -A 18 '<application' "$MANIFEST" || true
  echo

  echo "## Declared permissions"
  grep -n 'uses-permission' "$MANIFEST" || true
  echo

  echo "## Package visibility queries"
  grep -n -A 30 '<queries' "$MANIFEST" || true
  echo

  echo "## microG / GMS / Vanced references in smali"
  grep -Ril -E 'microg|gmscore|revanced|vanced' smali* 2>/dev/null | sort | head -200 || true
  echo

  echo "## microG / GMS / Vanced strings in resources"
  grep -Rin -E 'microg|gmscore|revanced|vanced' res/values*/strings.xml 2>/dev/null | head -300 || true
  echo

  echo "## app.revanced.android.gms / com.google.android.gms references in smali"
  grep -Rin -E 'app\.revanced\.android\.gms|com\.google\.android\.gms' smali* 2>/dev/null | head -300 || true
  echo

  echo "## Files whose names look related to setup/install/update/microg/gms"
  find smali* -type f \
    \( -iname '*setup*' -o -iname '*install*' -o -iname '*update*' \
       -o -iname '*microg*' -o -iname '*gms*' -o -iname '*permission*' \) \
    2>/dev/null | sort | head -500 || true
  echo

  echo "## Extension tree (com/gold/extension)"
  find smali_classes10/com/gold/extension -type f 2>/dev/null | sort | head -600 || true
  echo

  echo "## Router / Shell / MainActivity classes"
  find smali* -type f \
    \( -name 'RouterActivity.smali' -o -name 'Shell*.smali' \
       -o -name '*MainActivity*.smali' -o -name '*Launcher*.smali' \) \
    2>/dev/null | sort | head -200 || true
  echo

  echo "## Manifest components containing com.gold"
  grep -n -B 3 -A 10 'com\.gold' "$MANIFEST" | head -600 || true
  echo

  echo "## Full microG-related smali snippets (first 60 files)"
  count=0
  while IFS= read -r f; do
    count=$((count + 1))
    [ "$count" -le 60 ] || break
    echo
    echo "### $f"
    grep -n -i -B 8 -A 30 -E 'microg|gmscore|revanced|vanced' "$f" | head -260 || true
  done < <(grep -Ril -E 'microg|gmscore|revanced|vanced' smali* 2>/dev/null | sort)
  echo

  echo "## The app's current microG-not-installed text (all resources)"
  grep -Rin -E 'MicroG Not Installed|microg_not|not installed|install microg' res 2>/dev/null | head -200 || true
  echo
} > "$OUT/inspect-report.txt"

cp "$MANIFEST" "$OUT/AndroidManifest.xml"
cp apktool.yml "$OUT/apktool.yml" 2>/dev/null || true
cp res/values/strings.xml "$OUT/strings.xml" 2>/dev/null || true
find smali* -type f -name '*.smali' | wc -l > "$OUT/smali-file-count.txt"

echo "Wrote inspection report to $OUT/inspect-report.txt"
wc -l "$OUT/inspect-report.txt"
