# Wispral SD-M0 HW-A: Playwright rerun with a bunx shim (the winget Bun install has no bunx).
# Environment fix only; no donor file changed. The original failing attempt is kept in playwright.log.
$Out = 'REDACTED_HOME\w\sd-m0-hwa'
Set-Location 'REDACTED_HOME\w\hs'
$env:PATH = "REDACTED_HOME\w\bunx-shim;$env:PATH"; $env:CI = 'true'
# The existing %LOCALAPPDATA%\ms-playwright folder is not readable by this user (left untouched),
# so the browser goes into the work directory instead.
$env:PLAYWRIGHT_BROWSERS_PATH = 'REDACTED_HOME\w\pw-browsers'
$env:PLAYWRIGHT_JSON_OUTPUT_NAME = "$Out\playwright-rerun2-results.json"
$sw = [Diagnostics.Stopwatch]::StartNew()
& { "# Rerun with bunx.cmd = 'bun x %*' on PATH."; bunx playwright install chromium; bun run test:playwright -- --reporter=list,json } *>&1 | Out-File "$Out\playwright-rerun2.log" -Encoding utf8
"STEP_EXIT=$LASTEXITCODE SECONDS=$([math]::Round($sw.Elapsed.TotalSeconds))" | Add-Content "$Out\playwright-rerun2.log"
"PLAYWRIGHT_RERUN2_DONE" | Add-Content "$Out\progress.txt"
