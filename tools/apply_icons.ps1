param(
    [string]$DecodedRes = "C:\Users\pocot\AppData\Local\Temp\opencode\ytpatch\dec59\res",
    [string]$LogoPath   = "C:\Users\pocot\Music\T YOUTUBE PRO\T_YouTubeLOGO.jpg",
    [string]$IconsDir   = "C:\Users\pocot\Music\T YOUTUBE PRO\app_icons"
)

Add-Type -AssemblyName System.Drawing

$srcImage = [System.Drawing.Image]::FromFile($LogoPath)

# adaptive-icon canvas is 108dp per bucket; legacy launcher bitmap is 48dp
$buckets = @(
    @{ Name = "mipmap-mdpi";    Adaptive = 108; Legacy = 48  },
    @{ Name = "mipmap-hdpi";    Adaptive = 162; Legacy = 72  },
    @{ Name = "mipmap-xhdpi";   Adaptive = 216; Legacy = 96  },
    @{ Name = "mipmap-xxhdpi";  Adaptive = 324; Legacy = 144 },
    @{ Name = "mipmap-xxxhdpi"; Adaptive = 432; Legacy = 192 }
)

function New-Canvas([int]$size, [double]$scale) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $bmp.SetResolution(96, 96)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode  = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode      = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode    = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.Clear([System.Drawing.Color]::Black)

    $w = [Math]::Min([int]($size * $scale), $size)
    $x = [int](($size - $w) / 2)
    $g.DrawImage($script:srcImage, $x, $x, $w, $w)
    $g.Dispose()
    return $bmp
}

function Save-Png($bitmap, [string]$path) {
    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose()
}

foreach ($b in $buckets) {
    $dir = Join-Path $DecodedRes $b.Name
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    $a = $b.Adaptive
    $l = $b.Legacy

    # background layer: solid black (logo art sits on black already)
    Save-Png (New-Canvas $a 0.0) (Join-Path $dir "adaptiveproduct_youtube_2024_q4_background_color_108.png")
    Save-Png (New-Canvas $a 0.0) (Join-Path $dir "adaptiveproduct_youtube_background_color_108.png")

    # foreground layer: logo at 76% so circular/squircle masks never clip it
    Save-Png (New-Canvas $a 0.76) (Join-Path $dir "adaptiveproduct_youtube_2024_q4_foreground_color_108.png")
    Save-Png (New-Canvas $a 0.76) (Join-Path $dir "adaptiveproduct_youtube_foreground_color_108.png")

    # legacy square icon for pre-adaptive launchers
    $legacyPath = Join-Path $dir "ic_launcher.png"
    Save-Png (New-Canvas $l 1.0) $legacyPath

    # mirror into the user's app_icons folder
    $mirror = Join-Path $IconsDir $b.Name
    if (-not (Test-Path $mirror)) { New-Item -ItemType Directory -Path $mirror | Out-Null }
    Copy-Item $legacyPath (Join-Path $mirror "ic_launcher.png") -Force

    Write-Host ("{0,-16} adaptive {1}px   legacy {2}px   fg {3} bytes" -f $b.Name, $a, $l, (Get-Item (Join-Path $dir "adaptiveproduct_youtube_2024_q4_foreground_color_108.png")).Length)
}

$srcImage.Dispose()
Write-Host "Done. Icons written under $DecodedRes"