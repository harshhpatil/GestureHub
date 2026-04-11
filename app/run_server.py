import uvicorn
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from networking.command_server import CommandServer

try:
    server = CommandServer()
    print("Starting server on http://0.0.0.0:8000...")
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        access_log=False,
    )
except Exception as e:
    print(f"\n[ERROR] Server failed to start: {e}")
    if "address already in use" in str(e).lower():
        print("FIX: Something is already running on port 8000. Run 'Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force' in PowerShell.")
    sys.exit(1)
