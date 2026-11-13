param(
    [Parameter(Mandatory = $true, Position = 0)] [string] $Config
)

$ErrorActionPreference = 'Stop'
$configPath = (Resolve-Path -LiteralPath $Config).Path
$version = '45.2.3'
$arch = switch ($env:PROCESSOR_ARCHITECTURE) {
    'ARM64' { 'arm64' }
    'AMD64' { 'x64' }
    default { throw 'Requires Windows x64 or ARM64.' }
}
$runtime = Join-Path $PSScriptRoot ".electron\$version-$arch"
$exe = Join-Path $runtime 'electron.exe'
$marker = Join-Path $runtime '.ready'
if (!(Test-Path -LiteralPath $marker) -or !(Test-Path -LiteralPath $exe)) {
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    $file = "electron-v$version-win32-$arch.zip"
    $source = "https://github.com/electron/electron/releases/download/v$version"
    $zip = Join-Path $runtime $file
    Write-Host "Downloading Electron $version ($arch)..."
    $checksums = & curl.exe -fsSL --retry 2 "$source/SHASUMS256.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Could not download the Electron checksum list.' }
    $pattern = '^([a-fA-F0-9]{64})\s+\*?' + [regex]::Escape($file) + '$'
    $match = [regex]::Match(($checksums -join "`n"), $pattern, 'Multiline')
    if (!$match.Success) { throw "No checksum for $file." }
    & curl.exe -fSL --retry 2 "$source/$file" -o $zip
    if ($LASTEXITCODE -ne 0) { throw 'Could not download the Electron runtime.' }
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $match.Groups[1].Value) {
        throw 'Electron checksum did not match.'
    }
    Expand-Archive -LiteralPath $zip -DestinationPath $runtime -Force
    Remove-Item -LiteralPath $zip
    New-Item -ItemType File -Path $marker -Force | Out-Null
}

& $exe (Join-Path $PSScriptRoot 'desktop') $configPath
