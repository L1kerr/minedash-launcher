# Launches the packaged-dev app and screenshots its window.
param([string]$Out = "screen\shot.png", [int]$Wait = 10)
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinApi {
  public delegate bool CB(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(CB cb, IntPtr l);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  public static IntPtr Find(uint[] pids, string title) {
    IntPtr found = IntPtr.Zero;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint pid; GetWindowThreadProcessId(h, out pid);
      var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
      foreach (var p in pids) if (p == pid && sb.ToString() == title && IsWindowVisible(h)) found = h;
      return true;
    }, IntPtr.Zero);
    return found;
  }
}
"@
$p = Start-Process -FilePath "npx.cmd" -ArgumentList "electron ." -PassThru -WindowStyle Hidden
$deadline = (Get-Date).AddSeconds($Wait)
$h = [IntPtr]::Zero
while ((Get-Date) -lt $deadline) {
  $procs = @(Get-Process -Name electron -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
  if ($procs.Count) { $h = [WinApi]::Find($procs, "MineDash Launcher"); if ($h -ne [IntPtr]::Zero) { break } }
  Start-Sleep -Milliseconds 500
}
if ($h -eq [IntPtr]::Zero) { "window not found"; Stop-Process -Name electron -Force -ErrorAction SilentlyContinue; exit 1 }
[WinApi]::ShowWindow($h, 9) | Out-Null
[WinApi]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 900
$r = New-Object WinApi+RECT
[WinApi]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.R - $r.L; $ht = $r.B - $r.T
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $w, $ht
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
[WinApi]::PrintWindow($h, $hdc, 2) | Out-Null
$g.ReleaseHdc($hdc)
$bmp.Save($Out)
$g.Dispose(); $bmp.Dispose()
"captured $w x $ht -> $Out"
Stop-Process -Name electron -Force -ErrorAction SilentlyContinue
