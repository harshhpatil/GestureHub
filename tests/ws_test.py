import asyncio
import websockets
import json

async def listen():

    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as ws:

        print("Connected to GestureHub")

        while True:
            msg = await ws.recv()
            print("Received:", msg)

asyncio.run(listen())