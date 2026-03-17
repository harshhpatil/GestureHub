import uvicorn
from networking.command_server import CommandServer

server = CommandServer()

uvicorn.run(
	server.app,
	host="0.0.0.0",
	port=8000,
	log_level="warning",
	access_log=False,
)