param(
    [int]$Port = 8000
)

Write-Host "Shutting down server on port $Port..."

# Find the process ID listening on the specified port
$processInfo = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"

if ($processInfo) {
    $pid = ($processInfo -split '\s+')[-1]
    Write-Host "Found process $pid on port $Port"

    try {
        Stop-Process -Id $pid -Force
        Write-Host "Successfully terminated process $pid"
    }
    catch {
        Write-Host "Failed to terminate process $pid : $($_.Exception.Message)"
    }
}
else {
    Write-Host "No server found running on port $Port"
}

Write-Host "Done."