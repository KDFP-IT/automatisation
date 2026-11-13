param(
    [string]$BindAddress = '127.0.0.1',
    [int]$Port = 8080
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Сначала создайте .venv и установите зависимости по инструкции webapp/README.md.'
}
& $pythonPath (Join-Path $PSScriptRoot 'app.py') --host $BindAddress --port $Port
exit $LASTEXITCODE
