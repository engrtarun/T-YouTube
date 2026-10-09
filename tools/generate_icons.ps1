$source = "c:\Users\pocot\Music\T YOUTUBE PRO\T_YouTubeLOGO.jpg"
$outDir = "c:\Users\pocot\Music\T YOUTUBE PRO\app_icons"

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

Add-Type -AssemblyName System.Drawing

$img = [System.Drawing.Image]::FromFile($source)

$sizes = @{
    "mipmap-mdpi" = 48
    "mipmap-hdpi" = 72
    "mipmap-xhdpi" = 96
    "mipmap-xxhdpi" = 144
    "mipmap-xxxhdpi" = 192
    "playstore" = 512
}

foreach ($key in $sizes.Keys) {
    $size = $sizes[$key]
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    
    # Set high quality resizing
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    $g.DrawImage($img, 0, 0, $size, $size)
    
    if ($key -match "mipmap") {
        $folder = Join-Path $outDir $key
        if (-not (Test-Path $folder)) { New-Item -ItemType Directory -Path $folder | Out-Null }
        $outPath = Join-Path $folder "ic_launcher.png"
    } else {
        $outPath = Join-Path $outDir "playstore_icon.png"
    }
    
    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

$img.Dispose()
Write-Host "Icons generated successfully in $outDir"
