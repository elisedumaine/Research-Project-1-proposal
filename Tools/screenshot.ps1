# Save a picture of the screen (or of one program's window) so Claude can look at it.
#   powershell -File Tools/screenshot.ps1                      -> whole screen
#   powershell -File Tools/screenshot.ps1 -Process UnrealEditor -> that window, brought to the front
#   powershell -File Tools/screenshot.ps1 -Title "Low Poly Studio" -> that window (restored if minimized)
param([string]$Process = "", [string]$Title = "", [string]$Out = "$PSScriptRoot\..\captures\screen.png")

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class LpkWin {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    public delegate bool EnumProc(IntPtr h, IntPtr p);
    public struct RECT { public int Left, Top, Right, Bottom; }
    public static IntPtr Find(string title) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, p) => {
            var s = new System.Text.StringBuilder(256); GetWindowText(h, s, 256);
            if (IsWindowVisible(h) && s.ToString().Contains(title)) { found = h; return false; }
            return true; }, IntPtr.Zero);
        return found;
    }
}
"@
[LpkWin]::SetProcessDPIAware() | Out-Null

$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$handle = [IntPtr]::Zero
if ($Title) {
    $handle = [LpkWin]::Find($Title)
    if ($handle -eq [IntPtr]::Zero) { Write-Output "no window titled $Title"; exit 1 }
} elseif ($Process) {
    $p = Get-Process $Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if (-not $p) { Write-Output "no window for $Process"; exit 1 }
    $handle = $p.MainWindowHandle
}
if ($handle -ne [IntPtr]::Zero) {
    [LpkWin]::ShowWindow($handle, 9) | Out-Null      # restore if minimized
    [LpkWin]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Milliseconds 700
    $r = New-Object LpkWin+RECT
    [LpkWin]::GetWindowRect($handle, [ref]$r) | Out-Null
    $bounds = New-Object System.Drawing.Rectangle($r.Left, $r.Top, ($r.Right - $r.Left), ($r.Bottom - $r.Top))
}
$bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bitmap.Size)
$Out = [System.IO.Path]::GetFullPath($Out)
$bitmap.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output "saved $Out ($($bounds.Width)x$($bounds.Height))"
