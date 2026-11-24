# Save the image in the clipboard (after Win+Shift+S, Print Screen, or "Copy image") so Claude can look at it.
#   powershell -STA -File Tools/clipboard_image.ps1
# Also picks up an image file copied in the Explorer.  Saves to captures/from_user/<time>.png.
param([string]$Folder = "$PSScriptRoot\..\captures\from_user")

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$Folder = [System.IO.Path]::GetFullPath($Folder)
New-Item -ItemType Directory -Force $Folder | Out-Null
$out = Join-Path $Folder ("capture_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".png")

$image = [System.Windows.Forms.Clipboard]::GetImage()
if ($image) {
    $image.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "saved $out ($($image.Width)x$($image.Height))"
    exit 0
}
$files = [System.Windows.Forms.Clipboard]::GetFileDropList()
$picture = $files | Where-Object { $_ -match '\.(png|jpe?g|bmp|gif|webp)$' } | Select-Object -First 1
if ($picture) {
    Copy-Item $picture $out
    Write-Output "saved $out (copied from $picture)"
    exit 0
}
Write-Output "no image in the clipboard"
exit 1
