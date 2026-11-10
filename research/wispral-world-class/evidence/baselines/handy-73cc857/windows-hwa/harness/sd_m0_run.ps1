# Wispral 000E SD-M0 HW-A runner. Runs the donor's own suites and builds unmodified at
# TheHalfMoon/wisprside@f83add0 (cjpais/Handy@73cc857 plus one workflow file). Resumable: a step whose
# done-marker exists is skipped. No installer or bundle is produced (cargo build, not tauri build).
# Usage: pwsh -File sd_m0_run.ps1
$ErrorActionPreference = 'Continue'
$Repo = 'REDACTED_HOME\w\hs'
$Out = 'REDACTED_HOME\w\sd-m0-hwa'
New-Item -ItemType Directory -Force $Out, "$Out\done" | Out-Null
# Prefer Visual Studio's bundled CMake over the Strawberry Perl (MinGW) cmake that is first on PATH.
$vsCmake = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin'
$env:PATH = "$vsCmake;$env:PATH"
$env:VULKAN_SDK = 'C:\VulkanSDK\1.4.363.0'

function Log([string]$m) { "$m $(Get-Date -Format o)" | Add-Content "$Out\progress.txt" }

# Resource sampler: every 5 s, system free memory and the summed working set of build/test processes.
$sampler = Start-Job -ArgumentList $Out -ScriptBlock {
    param($Out)
    while (-not (Test-Path "$Out\stop-sampler")) {
        $os = Get-CimInstance Win32_OperatingSystem
        $procs = Get-Process cargo, rustc, cl, link, cmake, msbuild, node, bun, handy, 'handy_app_lib*', glslc, 'vulkan-shaders-gen', chrome -ErrorAction SilentlyContinue
        $ws = ($procs | Measure-Object WorkingSet64 -Sum).Sum
        "{0}`t{1}`t{2}`t{3}" -f (Get-Date -Format o), [math]::Round($os.FreePhysicalMemory / 1MB, 2), [math]::Round($ws / 1GB, 2), ($procs | Measure-Object).Count |
            Add-Content "$Out\resources.tsv"
        Start-Sleep 5
    }
}

function Step([string]$name, [string]$dir, [scriptblock]$body) {
    if (Test-Path "$Out\done\$name") { Log "skip $name"; return }
    Log "start $name"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Push-Location $dir
    $global:LASTEXITCODE = 0
    & $body *>&1 | Out-File -FilePath "$Out\$name.log" -Encoding utf8
    $code = $LASTEXITCODE
    Pop-Location
    "STEP_EXIT=$code SECONDS=$([math]::Round($sw.Elapsed.TotalSeconds))" | Add-Content "$Out\$name.log"
    Log "end $name exit=$code seconds=$([math]::Round($sw.Elapsed.TotalSeconds))"
    New-Item -ItemType File -Force "$Out\done\$name" | Out-Null
}

Log 'RUN_START'
Step 'toolchain' $Repo {
    git rev-parse HEAD; rustc --version; cargo --version; rustup show active-toolchain
    bun --version; node --version; (Get-Command cmake).Source; cmake --version
    "VULKAN_SDK=$env:VULKAN_SDK"; (Get-CimInstance Win32_OperatingSystem).Caption; (Get-CimInstance Win32_OperatingSystem).BuildNumber
    (Get-CimInstance Win32_Processor).Name; [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
}
Step 'bun-install' $Repo { bun install --frozen-lockfile }
Step 'lint' $Repo { bun run lint }
Step 'test-keyboard' $Repo { bun run test:keyboard }
Step 'playwright' $Repo {
    # The Linux baseline ran with CI=true (GitHub sets it): retries 2, workers 1. Match it.
    $env:CI = 'true'
    $env:PLAYWRIGHT_JSON_OUTPUT_NAME = "$Out\playwright-results.json"
    bunx playwright install chromium
    bun run test:playwright -- --reporter=list,json
}
Step 'frontend-build' $Repo { bun run build }
Step 'cargo-test' "$Repo\src-tauri" { cargo test --locked }
Step 'cargo-build-debug' "$Repo\src-tauri" { cargo build --locked }
Step 'cargo-build-release' "$Repo\src-tauri" { cargo build --locked --release }
Step 'artifacts' "$Repo\src-tauri" {
    $dumpbin = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\dumpbin.exe'
    foreach ($p in 'debug', 'release') {
        "=== $p"
        Get-ChildItem "target\$p" -File | Where-Object { $_.Extension -in '.exe', '.dll' } |
            ForEach-Object { "{0}`t{1}" -f $_.Name, $_.Length }
        "--- dumpbin /dependents target\$p\handy.exe"
        & $dumpbin /dependents "target\$p\handy.exe"
        "--- sha256"
        (Get-FileHash "target\$p\handy.exe" -Algorithm SHA256).Hash
    }
    "=== target size GB"
    [math]::Round(((Get-ChildItem target -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1GB, 2)
}
New-Item -ItemType File -Force "$Out\stop-sampler" | Out-Null
Wait-Job $sampler -Timeout 30 | Out-Null
Log 'ALL_DONE'
