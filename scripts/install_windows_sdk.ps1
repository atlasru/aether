# SPDX-License-Identifier: GPL-3.0-only
# Chromium 155 pins SDK folder 10.0.28000.0; the hosted image has only 26100.
$ErrorActionPreference = 'Stop'
$evidence = Join-Path $PSScriptRoot '../dist/hosted'
New-Item -ItemType Directory -Force $evidence | Out-Null
$sdkRoot = 'C:\Program Files (x86)\Windows Kits\10'
$sdkVersion = '10.0.28000.0'
# Servicing release >= Chromium's documented minimum 10.0.28000.2270.
# Hash/URL: microsoft/winget-pkgs WindowsSDK 10.0.28000.2526 installer manifest.
$uri = 'https://download.microsoft.com/download/06fc99ac-527e-451e-a536-8866695a2e7e/KIT_BUNDLE_WINDOWSSDK_MEDIACREATION/winsdksetup.exe'
$expectedHash = '02988EA51EAB2A2DB53E19735E51C97A6D221ADA74B9174FA0868870B9403BA0'
$installer = Join-Path $env:RUNNER_TEMP 'aether-winsdk-28000.2526.exe'
$report = @{ sdk_version = $sdkVersion; installer_url = $uri; expected_sha256 = $expectedHash }
try {
    Invoke-WebRequest -Uri $uri -OutFile $installer -TimeoutSec 180
    $report.sha256 = (Get-FileHash $installer -Algorithm SHA256).Hash
    if ($report.sha256 -ne $expectedHash) { throw 'Microsoft SDK installer hash mismatch' }
    $signature = Get-AuthenticodeSignature $installer
    $report.signature_status = [string]$signature.Status
    $report.signer = $signature.SignerCertificate.Subject
    if ($signature.Status -ne 'Valid' -or $report.signer -notmatch 'CN=Microsoft Corporation') {
        throw 'Microsoft SDK installer signature is not valid'
    }
    $log = Join-Path (Resolve-Path $evidence) 'sdk-install.log'
    # '+' requests all SDK components, including desktop/UWP/ARM64 libs and
    # Debugging Tools required by Chromium. No browser security flags change.
    $process = Start-Process -FilePath $installer -ArgumentList "/features + /q /norestart /ceip off /log `"$log`"" -PassThru -Wait
    $report.exit_code = $process.ExitCode
    if ($process.ExitCode -notin @(0, 3010)) { throw "SDK installer exited $($process.ExitCode)" }
    $required = @(
        "Include/$sdkVersion/um/Windows.h",
        "Lib/$sdkVersion/um/x64/kernel32.lib",
        "bin/$sdkVersion/x64/midl.exe",
        'Debuggers/x64/dbghelp.dll',
        'Debuggers/x64/dbgcore.dll'
    )
    foreach ($relative in $required) {
        $file = Join-Path $sdkRoot $relative
        if (-not (Test-Path $file -PathType Leaf)) { throw "Required SDK file missing: $file" }
    }
    $report.debugger_version = (Get-Item (Join-Path $sdkRoot 'Debuggers/x64/dbghelp.dll')).VersionInfo.FileVersion
    $report.installed_include_versions = @(Get-ChildItem "$sdkRoot/Include" | Select-Object -ExpandProperty Name)
    $report.result = 'installed and required files verified'
} catch {
    $report.result = 'failed'
    $report.error = $_.Exception.Message
    throw
} finally {
    $report | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $evidence 'sdk-install.json')
    $report | ConvertTo-Json -Depth 5 | Write-Host
}
