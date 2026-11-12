param(
 [string]$Package='D:/Builds/MareAltaUE58_Pessoas_2026-11-04/Windows',
 [string[]]$Variants=@(''),
 [string]$Exec='',
 [int]$Soak=0,
 [string]$NoShadow='',
 [string]$Hide='',
 [switch]$Fullscreen,
 [switch]$Focus,
 [int]$ResX=1920,
 [int]$ResY=1080
)
# Frame-time benchmark of the packaged game (PENDENCIAS P0 "FPS medido no executável"): runs MareAlta.exe -MareBench
# once per variant ('' = full game, 'MareBenchNoPeople', 'MareBenchNoGroom') and prints one row per sector.
# -Soak 7200 = 2-hour session (PENDENCIAS P0): the sectors repeat, sleeping to the next day between rounds.
$ErrorActionPreference='Stop'
$env:TEMP='D:/CodexTemp/ue58-temp'
$env:TMP=$env:TEMP
foreach($variant in $Variants){
 $qa='D:/CodexTemp/ue58-bench-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
 New-Item -ItemType Directory -Force $qa | Out-Null
 $args=@('-MareBench',"-MareSaveRoot=$qa","-UserDir=$qa/Unreal","-abslog=$qa/runtime.log",'-unattended','-nosplash',$(if($Fullscreen){'-fullscreen'}else{'-windowed'}),"-ResX=$ResX","-ResY=$ResY")
 if($variant){$args+="-$variant"}
 if($Exec){$args+="-MareBenchExec=`"$Exec`""}
 if($Soak){$args+="-MareBenchSoak=$Soak"}
 if($NoShadow){$args+="-MareBenchNoShadow=$NoShadow"}
 if($Hide){$args+="-MareBenchHide=$Hide"}
 $p=Start-Process -FilePath "$Package/MareAlta.exe" -WorkingDirectory $Package -ArgumentList $args -PassThru
 # -Focus: DLSS Frame Generation only runs while the game window has focus (StreamlineDLSSG.cpp: FApp::HasFocus), and a
 # window started from a script stays behind the terminal.
 if($Focus){
  # Windows refuses SetForegroundWindow from a background script; attaching to the input queue of the window that has
  # focus now lifts that, then a click inside the game window keeps it focused.
  Add-Type -Namespace MareBench -Name WinFocus -MemberDefinition @'
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,IntPtr p);
[DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
[DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a,uint b,bool f);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,int[] r);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
[DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
'@ -ErrorAction SilentlyContinue
  foreach($wait in 12,10,10){Start-Sleep $wait
   # The package's MareAlta.exe only launches Binaries/Win64/MareAlta.exe, which owns the window.
   $w=Get-Process MareAlta -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1;if(-not $w){continue};$h=$w.MainWindowHandle
   $fg=[MareBench.WinFocus]::GetForegroundWindow();$t1=[MareBench.WinFocus]::GetWindowThreadProcessId($fg,[IntPtr]::Zero);$t2=[MareBench.WinFocus]::GetCurrentThreadId()
   [MareBench.WinFocus]::AttachThreadInput($t2,$t1,$true)|Out-Null;[MareBench.WinFocus]::ShowWindow($h,9)|Out-Null;[MareBench.WinFocus]::BringWindowToTop($h)|Out-Null;[MareBench.WinFocus]::SetForegroundWindow($h)|Out-Null;[MareBench.WinFocus]::AttachThreadInput($t2,$t1,$false)|Out-Null
   Start-Sleep -Milliseconds 400;$r=New-Object int[] 4;[MareBench.WinFocus]::GetWindowRect($h,$r)|Out-Null
   [MareBench.WinFocus]::SetCursorPos([int](($r[0]+$r[2])/2),[int](($r[1]+$r[3])/2))|Out-Null;[MareBench.WinFocus]::mouse_event(2,0,0,0,[UIntPtr]::Zero);[MareBench.WinFocus]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
   Write-Output "  foco: $([MareBench.WinFocus]::GetForegroundWindow() -eq $h)"}
 }
 $start=Get-Date
 while(-not $p.HasExited){if(((Get-Date)-$start).TotalSeconds -gt (420+$Soak*1.2)){Stop-Process -Id $p.Id;throw "Timeout: $qa"};Start-Sleep 3;$p.Refresh()}
 if(-not (Test-Path "$qa/bench.json")){throw "Sem bench.json: $qa"}
 Write-Output "== $(if($variant){$variant}else{'completo'}) $(if($Fullscreen){'[tela cheia]'}) $Exec $(if($NoShadow){"sem sombra: $NoShadow"}) $(if($Hide){"escondido: $Hide"})  ($qa)"
 (Get-Content "$qa/bench.json" -Raw | ConvertFrom-Json).sectors | ForEach-Object {
  "{0,-13} fps {1,5:N1}  p99 {2,5:N1} | jogo {3,5:N1} render {4,5:N1} gpu {5,5:N1} | pessoas {6}/{7} | na tela {8,5:N1}" -f $_.sector,$_.avg_fps,$_.p99_ms,$_.game_ms,$_.render_ms,$_.gpu_ms,$_.people_rendered,$_.people,$_.presented_fps }
 # Shipping writes no log: nothing to scan then.
 $bad=@(if(Test-Path "$qa/runtime.log"){Select-String -LiteralPath "$qa/runtime.log" -Pattern 'Failed to find object|Nanite static mesh|overflow|Error:|Fatal'})
 if($bad.Count){Write-Output "  avisos no log: $($bad.Count)"}
}
