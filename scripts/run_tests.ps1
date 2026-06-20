param(
    [string[]]$PytestArgs = @("tests")
)

$ErrorActionPreference = "Stop"

$Python = if ($env:PSAIR_PYTHON) {
    $env:PSAIR_PYTHON
} else {
    "$env:USERPROFILE\anaconda3\envs\psair\python.exe"
}

if (-not (Test-Path $Python)) {
    throw "Could not find PSAIR Python at $Python. Set PSAIR_PYTHON to override."
}

& $Python -m pytest @PytestArgs
exit $LASTEXITCODE
