$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Configurator = Join-Path $ScriptDir "slack_app_configurator.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $Configurator --open @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Configurator --open @args
    exit $LASTEXITCODE
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 $Configurator --open @args
    exit $LASTEXITCODE
}

Write-Error "Python 3 was not found. Install Python 3, then run this script again."
exit 1
