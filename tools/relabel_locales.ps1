$res = "C:\Users\pocot\AppData\Local\Temp\opencode\ytpatch\dec59\res"
$changed = 0

Get-ChildItem -Directory -Path $res | Where-Object { $_.Name -like "values*" } | ForEach-Object {
    $f = Join-Path $_.FullName "strings.xml"
    if (-not (Test-Path $f)) { return }

    $text = [System.IO.File]::ReadAllText($f)
    $new  = [regex]::Replace(
        $text,
        '(<string name="application_name">)(.*?)(</string>)',
        { param($m) $m.Groups[1].Value + "T YouTube" + $m.Groups[3].Value }
    )

    if ($new -ne $text) {
        [System.IO.File]::WriteAllText($f, $new, (New-Object System.Text.UTF8Encoding($false)))
        $script:changed++
    }
}

Write-Host "Updated application_name in $changed locale file(s)."