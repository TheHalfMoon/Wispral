# Wispral 000E HW-A egress observer (non-admin). Polls TCP connections every second and records
# every non-loopback remote endpoint with its owning process. Weaker than a packet capture: a
# connection that opens and closes within one polling interval can be missed.
# Usage: pwsh -File egress_watch.ps1 -Out <file> -StopFile <file>
param([string]$Out, [string]$StopFile)
$seen = @{}
"# started $(Get-Date -Format o)" | Set-Content -Path $Out -Encoding utf8
while (-not (Test-Path $StopFile)) {
    try {
        Get-NetTCPConnection -ErrorAction Stop |
            Where-Object { $_.RemoteAddress -notmatch '^(127\.|::1|0\.0\.0\.0|::$)' -and $_.RemotePort -ne 0 } |
            ForEach-Object {
                $key = "$($_.RemoteAddress):$($_.RemotePort)|$($_.OwningProcess)"
                if (-not $seen.ContainsKey($key)) {
                    $seen[$key] = $true
                    $p = (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName
                    "$(Get-Date -Format o) $($_.State) $($_.RemoteAddress):$($_.RemotePort) pid=$($_.OwningProcess) proc=$p" | Add-Content -Path $Out -Encoding utf8
                }
            }
    } catch {}
    Start-Sleep -Milliseconds 1000
}
"# stopped $(Get-Date -Format o)" | Add-Content -Path $Out -Encoding utf8
