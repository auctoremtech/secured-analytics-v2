# Server Shutdown Scripts

Two scripts are provided to shut down the Django development server running on port 8000:

## shutdown_server.bat (Batch Script)
- **Usage**: Double-click the file or run `shutdown_server.bat` from command prompt
- **What it does**: Finds and terminates any process listening on port 8000
- **Platform**: Windows Command Prompt

## shutdown_server.ps1 (PowerShell Script)
- **Usage**: Run `powershell -ExecutionPolicy Bypass -File shutdown_server.ps1` from PowerShell
- **Parameters**: 
  - `-Port`: Specify a different port (default: 8000)
  - Example: `.\shutdown_server.ps1 -Port 8080`
- **What it does**: Finds and terminates any process listening on the specified port
- **Platform**: Windows PowerShell

## How it works
Both scripts use `netstat` to find processes listening on the target port, then use the appropriate kill command (`taskkill` for batch, `Stop-Process` for PowerShell) to terminate them.

## Example Output
```
Shutting down Django development server on port 8000...
Found process 14276 on port 8000
Successfully terminated process 14276
Done.
```