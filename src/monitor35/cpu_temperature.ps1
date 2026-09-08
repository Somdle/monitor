param([Parameter(Mandatory=$true)][string]$LibraryPath)
$ErrorActionPreference = 'Stop'
$computer = $null
try {
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
    [Reflection.Assembly]::LoadFrom($LibraryPath) | Out-Null
    $computer = New-Object LibreHardwareMonitor.Hardware.Computer
    $computer.IsCpuEnabled = $true
    $computer.Open()
    while ($true) {
        $temperatures = @()
        foreach ($hardware in $computer.Hardware) {
            if ($hardware.HardwareType.ToString() -ne 'Cpu') { continue }
            $hardware.Update()
            $temperatures += @($hardware.Sensors | Where-Object {
                $_.SensorType.ToString() -eq 'Temperature' -and $null -ne $_.Value
            })
        }
        # Package/Tctl is the processor temperature; do not substitute a board/ACPI sensor.
        $sensor = $temperatures | Where-Object {
            $_.Name -in @('CPU (Tctl/Tdie)', 'CPU Package', 'Core Max')
        } | Sort-Object @{Expression={
            @('CPU (Tctl/Tdie)', 'CPU Package', 'Core Max').IndexOf($_.Name)
        }} | Select-Object -First 1
        $temperature = if ($null -ne $sensor) { [double]$sensor.Value } else { $null }
        @{temperature=$temperature} | ConvertTo-Json -Compress
        [Console]::Out.Flush()
        Start-Sleep -Milliseconds 1000
    }
} catch {
    @{temperature=$null; error=$_.Exception.Message} | ConvertTo-Json -Compress
    exit 1
} finally {
    if ($null -ne $computer) { $computer.Close() }
}
