$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { throw 'Run setup.cmd first.' }
$releaseDirectory = Join-Path $PSScriptRoot '.tmp/cpu-temperature'
$libraryDirectory = Join-Path $PSScriptRoot '.venv/hardware/LibreHardwareMonitor'
New-Item -ItemType Directory -Force $releaseDirectory, $libraryDirectory | Out-Null
$archive = Join-Path $releaseDirectory 'LibreHardwareMonitor.zip'
Invoke-WebRequest 'https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v0.9.6/LibreHardwareMonitor.zip' -OutFile $archive
$expected = '086D9F1B5A99E643EDC2CFAAAC16051685B551E4C5AC0B32A57C58C0E529C001'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
    throw 'LibreHardwareMonitor release hash mismatch.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $libraryDirectory -Force
Write-Output 'CPU sensor library prepared. PawnIO driver installation requires separate administrator approval.'
