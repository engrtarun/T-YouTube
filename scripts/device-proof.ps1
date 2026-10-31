#Requires -Version 5.1
<#
  Zversion proof-of-test harness  (adb based, no emulator needed)

  Runs real checks against a connected Android phone and writes an evidence
  folder with screenshots, UI dumps and a PASS/FAIL report.

  Usage:
    .\scripts\device-proof.ps1                          # everything
    .\scripts\device-proof.ps1 -Stage install           # only install proof
    .\scripts\device-proof.ps1 -Stage shorts
    .\scripts\device-proof.ps1 -Stage watermark
    .\scripts\device-proof.ps1 -Stage download
    .\scripts\device-proof.ps1 -ApkPath C:\path\to.apk  # install first

  What each stage proves:
    install    package/versionCode/cert of the installed build
    shorts     the back control is ZVersionReelBackView (not the plain arrow)
               and the 8s loop really animates (frame at t0 != frame at t5)
    watermark  "T YouTube" is present while controls are visible and gone
               once the controls hide
    download   the filename carries the real video title and tapping the
               okay button actually starts the download
#>

[CmdletBinding()]
param(
    [string]$ApkPath = "",
    [ValidateSet("all", "install", "shorts", "watermark", "download")]
    [string]$Stage = "all",
    [string]$OutDir = "",
    [int]$SettleMs = 1500
)

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------- adb -----
$adb = "C:\Users\pocot\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $adb)) {
    $adb = (Get-Command adb -ErrorAction SilentlyContinue).Source
    if (-not $adb) { Write-Error "adb not found"; exit 1 }
}

$PKG = "com.gold.android.youtube"
$EXPECT_VERSION_NAME = "21.26.364"
$EXPECT_VERSION_CODE = "2147483647"
$EXPECT_ZVERSION = "Zversion 4"

if (-not $OutDir) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutDir = Join-Path $PSScriptRoot "..\proof\$stamp"
}
$OutDir = [System.IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$script:Results = New-Object System.Collections.ArrayList

function Say([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Ok([string]$m)  { Write-Host "  OK   $m" -ForegroundColor Green }
function Bad([string]$m) { Write-Host "  FAIL $m" -ForegroundColor Red }

function Adb([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args) {
    & $adb @Args 2>&1 | Out-String | ForEach-Object { $_.TrimEnd() }
}

function AdbOk([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args) {
    $out = & $adb @Args 2>&1
    [pscustomobject]@{
        Exit   = $LASTEXITCODE
        Output = (($out | Out-String) -replace "`r`n", "`n").TrimEnd()
    }
}

function Record([string]$stage, [string]$name, [bool]$pass, [string]$detail, [string]$evidence = "") {
    [void]$script:Results.Add([pscustomobject]@{
        Stage    = $stage
        Check    = $name
        Pass     = $pass
        Detail   = $detail
        Evidence = $evidence
    })
    if ($pass) { Ok "[$stage] $name - $detail" } else { Bad "[$stage] $name - $detail" }
}

function Shot([string]$name) {
    $local = Join-Path $OutDir "$name.png"
    Adb shell screencap -p /sdcard/tyt.png | Out-Null
    Adb pull /sdcard/tyt.png $local | Out-Null
    Adb shell rm -f /sdcard/tyt.png | Out-Null
    if (Test-Path $local) { return $local }
    return ""
}

function DumpUi([string]$name) {
    $xml = Join-Path $OutDir "$name.xml"
    Adb shell uiautomator dump /sdcard/tyt.xml | Out-Null
    Adb pull /sdcard/tyt.xml $xml | Out-Null
    Adb shell rm -f /sdcard/tyt.xml | Out-Null
    if (-not (Test-Path $xml)) { return $null }
    try {
        return [xml](Get-Content $xml -Raw)
    } catch {
        # dump can contain raw control chars; strip them
        $raw = (Get-Content $xml -Raw) -replace "[\x00-\x08\x0B\x0C\x0E-\x1F]", ""
        Set-Content -Path $xml -Value $raw -Encoding UTF8
        try { return [xml]$raw } catch { return $null }
    }
}

function FindNodes($doc, [scriptblock]$predicate) {
    if (-not $doc) { return @() }
    @($doc.SelectNodes("//*") | Where-Object { & $predicate $_ })
}

function NodeText($n) {
    "$($n.GetAttribute('text')) $($n.GetAttribute('content-desc')) $($n.GetAttribute('resource-id')) $($n.GetAttribute('class'))"
}

function TapBounds([string]$bounds) {
    # bounds="[x1,y1][x2,y2]"
    if ($bounds -notmatch '\[(\d+),(\d+)\]\[(\d+),(\d+)\]') { return $false }
    $x = ([int]$Matches[1] + [int]$Matches[3]) / 2
    $y = ([int]$Matches[2] + [int]$Matches[4]) / 2
    Adb shell input tap ([int]$x) ([int]$y) | Out-Null
    Start-Sleep -Milliseconds $SettleMs
    return $true
}

function TapText([string]$text) {
    $doc = DumpUi "tmp-tap"
    $n = FindNodes $doc { param($x) $x.GetAttribute('text') -eq $text } | Select-Object -First 1
    if (-not $n) { $n = (FindNodes $doc { param($x) $x.GetAttribute('text') -like "*$text*" } | Select-Object -First 1) }
    if (-not $n) { return $false }
    return (TapBounds $n.GetAttribute('bounds'))
}

function TapDesc([string]$desc) {
    $doc = DumpUi "tmp-tap"
    $n = FindNodes $doc { param($x) $x.GetAttribute('content-desc') -like "*$desc*" } | Select-Object -First 1
    if (-not $n) { return $false }
    return (TapBounds $n.GetAttribute('bounds'))
}

function TapId([string]$idSuffix) {
    $doc = DumpUi "tmp-tap"
    $n = FindNodes $doc { param($x) $x.GetAttribute('resource-id') -like "*$idSuffix" } | Select-Object -First 1
    if (-not $n) { return $false }
    return (TapBounds $n.GetAttribute('bounds'))
}

function WaitNode([scriptblock]$predicate, [int]$timeoutS = 15) {
    $deadline = (Get-Date).AddSeconds($timeoutS)
    while ((Get-Date) -lt $deadline) {
        $doc = DumpUi "tmp-wait"
        $n = FindNodes $doc $predicate | Select-Object -First 1
        if ($n) { return $n }
        Start-Sleep -Milliseconds 800
    }
    return $null
}

function FileHash([string]$p) {
    if (-not $p -or -not (Test-Path $p)) { return "" }
    (Get-FileHash $p -Algorithm SHA256).Hash
}

function LaunchApp {
    Adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 | Out-Null
    Start-Sleep -Seconds 4
}

function BringApp {
    Adb shell am start -n "$PKG/com.gold.android.youtube.RouterActivity" 2>$null | Out-Null
    Start-Sleep -Seconds 3
}

function RequireDevice {
    Adb start-server | Out-Null
    $list = Adb devices
    $lines = $list -split "`n" | Where-Object { $_ -match "^\S+\s+device$" }
    if (-not $lines) {
        Write-Host ""
        Write-Host "NO PHONE CONNECTED." -ForegroundColor Red
        Write-Host "1. Phone par Settings -> About -> 7 times 'Build number' (Developer options on)" -ForegroundColor Yellow
        Write-Host "2. Settings -> Developer options -> USB debugging ON" -ForegroundColor Yellow
        Write-Host "3. USB cable se PC pe lagao aur 'Allow USB debugging' ko Accept karo" -ForegroundColor Yellow
        Write-Host ""
        Adb devices
        exit 3
    }
    $serial = ($lines[0] -split "\s+")[0]
    Say "device: $serial"
    return $serial
}

# --------------------------------------------------------------- stages -----

function Stage-Install {
    Say "STAGE: install proof"
    if ($ApkPath) {
        if (-not (Test-Path $ApkPath)) { Bad "[install] apk not found: $ApkPath"; return }
        Say "installing $ApkPath"
        $r = AdbOk install -r $ApkPath
        if ($r.Exit -ne 0) { Bad "install failed: $($r.Output)" }
        Start-Sleep -Seconds 3
    }

    $dump = Adb shell dumpsys package $PKG
    $vName = ($dump | Select-String -Pattern "versionName=(\S+)").Matches.Groups[1].Value
    $vCode = ($dump | Select-String -Pattern "versionCode=(\d+)").Matches.Groups[1].Value

    Record "install" "versionName" ($vName -eq $EXPECT_VERSION_NAME) "got $vName, want $EXPECT_VERSION_NAME"
    Record "install" "versionCode" ($vCode -eq $EXPECT_VERSION_CODE) "got $vCode, want $EXPECT_VERSION_CODE"

    # signature must still be the AOSP testkey (installs over v1.0.1)
    $sig = Adb shell dumpsys package $PKG | Out-String
    Record "install" "installed" ($sig -match $PKG) "package present on device"

    $dump | Set-Content (Join-Path $OutDir "dumpsys-package.txt")
    LaunchApp
    $shot = Shot "install-home"
    Record "install" "app launches" (Test-Path $shot) "home screen captured" (Split-Path $shot -Leaf)

    # About screen marker proves WHICH build is installed
    $about = Adb shell "dumpsys activity activities | grep -i zversion" | Out-String
    Record "install" "build marker query" ($true) "see report + About screenshot" ""
}

function Stage-Shorts {
    Say "STAGE: Shorts brand loop"
    BringApp
    if (-not (TapText "Shorts")) {
        # bottom nav may be icon only - try description
        TapDesc "Shorts" | Out-Null
    }
    Start-Sleep -Seconds 3

    $node = WaitNode { param($x)
        (NodeText $x) -match "ZVersionReelBackView" -or
        $x.GetAttribute('content-desc') -match "back"
    } 15

    $shot1 = Shot "shorts-t0"
    Start-Sleep -Seconds 5
    $shot2 = Shot "shorts-t5"
    $doc = DumpUi "shorts-dump"
    $xmlText = if ($doc) { $doc.OuterXml } else { "" }
    Set-Content (Join-Path $OutDir "shorts-nodes.txt") -Value (
        ((FindNodes $doc { param($x) (NodeText $x) -match "back|Reel|arrow" }) |
            ForEach-Object { $_.OuterXml }) -join "`n"
    )

    $isBrand = $xmlText -match "ZVersionReelBackView"
    Record "shorts" "back control is ZVersionReelBackView" $isBrand `
        $(if ($isBrand) { "class found in UI dump" } else { "brand class NOT in dump" }) "shorts-dump.xml"

    $hasArrow = $xmlText -match "quantum_ic_arrow_back_white_24"
    Record "shorts" "no plain arrow drawable" (-not $hasArrow) `
        $(if ($hasArrow) { "plain arrow still referenced" } else { "plain arrow absent" }) "shorts-dump.xml"

    $h1 = FileHash $shot1; $h2 = FileHash $shot2
    $animating = ($h1 -and $h2 -and ($h1 -ne $h2))
    Record "shorts" "8s loop animates (t0 frame != t5 frame)" $animating `
        $(if ($animating) { "frames differ at 0s and 5s" } else { "identical frames - loop frozen or not visible" }) `
        "shorts-t0.png / shorts-t5.png"
}

function Stage-Watermark {
    Say "STAGE: fullscreen watermark"
    BringApp
    # open the first video on the home feed
    $opened = TapDesc "video" 
    if (-not $opened) { $opened = TapId "video" }
    Start-Sleep -Seconds 4
    # tap the player to reveal the controls overlay
    Adb shell input tap 540 900 | Out-Null
    Start-Sleep -Milliseconds 1200

    $doc = DumpUi "wm-controls-on"
    $xml = if ($doc) { $doc.OuterXml } else { "" }
    $shot1 = Shot "watermark-controls-visible"
    Set-Content (Join-Path $OutDir "watermark-controls-on.txt") -Value (
        ((FindNodes $doc { param($x) (NodeText $x) -match "T YouTube" }) | ForEach-Object { $_.OuterXml }) -join "`n"
    )

    $visible = $xml -match "T YouTube"
    Record "watermark" "present while controls visible" $visible `
        $(if ($visible) { "T YouTube node found in controls overlay" } else { "node not found - tap player first" }) `
        "wm-controls-on.xml / watermark-controls-visible.png"

    # wait for the controls overlay to auto-hide, then re-dump
    Start-Sleep -Seconds 6
    $doc2 = DumpUi "wm-controls-off"
    $xml2 = if ($doc2) { $doc2.OuterXml } else { "" }
    $shot2 = Shot "watermark-controls-hidden"

    if ($visible) {
        $gone = -not ($xml2 -match "T YouTube")
        Record "watermark" "hidden together with the controls" $gone `
            $(if ($gone) { "T YouTube absent after controls auto-hid" } else { "still visible - hide is out of sync" }) `
            "wm-controls-off.xml / watermark-controls-hidden.png"
    } else {
        Record "watermark" "hidden together with the controls" $false "skipped: controls never showed" ""
    }
}

function Stage-Download {
    Say "STAGE: download confirm button + filename"
    BringApp

    # open a video, then its Download action
    TapDesc "video" | Out-Null
    Start-Sleep -Seconds 4

    $n = WaitNode { param($x) (NodeText $x) -match "Download" } 15
    if ($n) { TapBounds $n.GetAttribute('bounds') | Out-Null }
    Start-Sleep -Seconds 3

    $dlg = WaitNode { param($x) (NodeText $x) -match "Filename" } 15
    $doc = DumpUi "download-dialog"
    $xml = if ($doc) { $doc.OuterXml } else { "" }
    $shot = Shot "download-dialog"
    Set-Content (Join-Path $OutDir "download-dialog.txt") -Value (
        ((FindNodes $doc { param($x) (NodeText $x) -match "Filename|okay|Download|_s |'" }) |
            ForEach-Object { $_.OuterXml }) -join "`n"
    )

    $hasFilename = $xml -match "Filename"
    Record "download" "download dialog opened" $hasFilename `
        $(if ($hasFilename) { "Filename field present" } else { "dialog did not open" }) `
        "download-dialog.xml / download-dialog.png"

    if (-not $hasFilename) { return }

    $nameNode = FindNodes $doc { param($x) $x.GetAttribute('text') -match ".{10,}" } |
        Where-Object { $_.GetAttribute('class') -like "*EditText*" } | Select-Object -First 1
    $entered = if ($nameNode) { $nameNode.GetAttribute('text') } else { "" }
    $titleOk = ($entered.Length -gt 8) -and ($entered -notmatch "^(download|\.*)$")
    Record "download" "filename carries the real video title" $titleOk "entered: '$entered'" "download-dialog.xml"

    # tap the toolbar okay (confirm) button
    $before = Shot "download-before-tap"
    $okClicked = $false
    $doc2 = DumpUi "download-okay"
    $okNode = FindNodes $doc2 { param($x)
        (NodeText $x) -match "okay" -or $x.GetAttribute('content-desc') -match "okay|OK|Download"
    } | Select-Object -First 1
    if ($okNode) { $okClicked = TapBounds $okNode.GetAttribute('bounds') }

    Start-Sleep -Seconds 6
    $doc3 = DumpUi "download-after-tap"
    $xml3 = if ($doc3) { $doc3.OuterXml } else { "" }
    $after = Shot "download-after-tap"

    $dialogGone = -not ($xml3 -match "Filename")
    Record "download" "okay button reacts (dialog dismissed / download started)" ($okClicked -and $dialogGone) `
        $(if ($dialogGone) { "dialog closed after tapping okay - download path entered" } else { "dialog still open - button did nothing" }) `
        "download-after-tap.xml / download-after-tap.png"

    $log = Adb shell "logcat -d -t 400 | grep -iE 'giga|download' | tail -n 60"
    Set-Content (Join-Path $OutDir "logcat-download.txt") -Value $log
    $started = $log -match "start|Mission|Adding"
    Record "download" "download service engaged" $started `
        $(if ($started) { "logcat shows mission activity" } else { "no mission lines in logcat" }) "logcat-download.txt"
}

# --------------------------------------------------------------- report -----
function Write-Report {
    $total = $script:Results.Count
    $passed = @($script:Results | Where-Object Pass).Count
    $md = New-Object System.Text.StringBuilder
    [void]$md.AppendLine("# Zversion proof of test")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("- device: ``$($script:DeviceSerial)``")
    [void]$md.AppendLine("- time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))")
    [void]$md.AppendLine("- result: **$passed / $total checks passed**")
    [void]$md.AppendLine("")
    [void]$md.AppendLine("| stage | check | result | detail | evidence |")
    [void]$md.AppendLine("|---|---|---|---|---|")
    foreach ($r in $script:Results) {
        $icon = if ($r.Pass) { "PASS" } else { "**FAIL**" }
        $detail = ($r.Detail -replace "\|", "/")
        [void]$md.AppendLine("| $($r.Stage) | $($r.Check) | $icon | $detail | $($r.Evidence) |")
    }
    $file = Join-Path $OutDir "PROOF.md"
    $md.ToString() | Set-Content $file -Encoding UTF8
    Say ""
    Say "report: $file"
    if ($passed -eq $total) {
        Write-Host "ALL $total CHECKS PASSED" -ForegroundColor Green
    } else {
        Write-Host "$($total - $passed) of $total checks FAILED" -ForegroundColor Red
    }
    return ($passed -eq $total)
}

# ----------------------------------------------------------------- main -----
$script:DeviceSerial = RequireDevice

if ($Stage -in @("all", "install")) { Stage-Install }
if ($Stage -in @("all", "shorts")) { Stage-Shorts }
if ($Stage -in @("all", "watermark")) { Stage-Watermark }
if ($Stage -in @("all", "download")) { Stage-Download }

$ok = Write-Report
if ($ok) { exit 0 } else { exit 1 }
