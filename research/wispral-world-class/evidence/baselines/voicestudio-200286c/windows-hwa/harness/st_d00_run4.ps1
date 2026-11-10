# ST-D00 HW-A pytest tests/ run 4: resumable chunks (one JUnit XML each), probe with outcomes,
# TCP watcher, and the 21 tests already proven to hang deselected (listed in hung-tests.txt).
$W = '<HOME>\w'; $OUT = "$W\st-d00-hwa\run4"
$env:PATH = '<HOME>\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe;' + $env:PATH
$env:PYTHONPATH = "$W\probe"; $env:WISPRAL_PROBE_DIR = "$OUT\probe"; $env:WISPRAL_TEST_LIMIT_S = '600'; $env:HF_HUB_OFFLINE = '1'
New-Item -ItemType Directory "$OUT\probe" -Force | Out-Null
Set-Location "$W\vs"
$chunks = Get-Content "$OUT\chunks.json" -Raw | ConvertFrom-Json
$deselect = @(Get-Content "$W\st-d00-hwa\hung-tests.txt" | Where-Object { $_ } | ForEach-Object { '--deselect'; ($_ -split "`t")[0] })
Remove-Item "$OUT\stop" -ErrorAction SilentlyContinue
$watch = Start-Process pwsh -ArgumentList '-NoProfile','-File',"$W\egress_watch.ps1",'-Out',"$OUT\egress-tcp-$(Get-Date -Format yyyyMMddHHmmss).txt",'-StopFile',"$OUT\stop" -PassThru -WindowStyle Hidden
for ($i = 0; $i -lt $chunks.Count; $i++) {
  if (Test-Path "$OUT\junit-$i.xml") { continue }
  "chunk $i start $((Get-Date).ToUniversalTime().ToString('o'))" | Add-Content "$OUT\progress.txt"
  $args = @('run','--no-sync','pytest') + @($chunks[$i]) + @('-q','--tb=short','-n','4','-rfE','-p','wispral_probe','-p','no:cacheprovider','--max-worker-restart=50',"--basetemp=$W\pt-run4-$i","--junitxml=$OUT\junit-$i.partial.xml") + $deselect
  & uv @args *> "$OUT\pytest-$i.log"
  "EXIT=$LASTEXITCODE" | Add-Content "$OUT\pytest-$i.log"
  if (Test-Path "$OUT\junit-$i.partial.xml") { Move-Item "$OUT\junit-$i.partial.xml" "$OUT\junit-$i.xml" -Force }
  "chunk $i end $((Get-Date).ToUniversalTime().ToString('o')) exit=$LASTEXITCODE" | Add-Content "$OUT\progress.txt"
}
New-Item -ItemType File "$OUT\stop" -Force | Out-Null
"ALL_DONE $((Get-Date).ToUniversalTime().ToString('o'))" | Add-Content "$OUT\progress.txt"
