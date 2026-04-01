# code in pi5 : stream_server.py
import asyncio
import websockets
import ssl

publishers = set()
subscribers = {}

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("server.crt", "server.key")

async def publish(websocket, channel):
    print(f"[PUBLISH] {channel}")
    publishers.add(websocket)
    try:
        async for message in websocket:
            if channel in subscribers and subscribers[channel]:
                subs = list(subscribers[channel])
                results = await asyncio.gather(
                    *[ws.send(message) for ws in subs],
                    return_exceptions=True
                )
                # clean up dead subscribers
                for ws, result in zip(subs, results):
                    if isinstance(result, Exception):
                        print(f"[PUBLISH] removing dead subscriber from {channel}")
                        subscribers[channel].discard(ws)
            await asyncio.sleep(0.01)
    except Exception as e:
        print("Publish error:", e)
    finally:
        publishers.discard(websocket)
        print(f"[PUBLISH CLOSED] {channel}")

async def subscribe(websocket, channel):
    print(f"[SUBSCRIBE] {channel}")
    subscribers.setdefault(channel, set()).add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        subscribers[channel].discard(websocket)
        print(f"[SUBSCRIBE CLOSED] {channel}")

async def handler(websocket):
    path = websocket.path 
    parts = path.split("/")

    if len(parts) < 3:
        await websocket.close()
        return

    if parts[1] == "publish":
        await publish(websocket, parts[2])
    elif parts[1] == "subscribe":
        await subscribe(websocket, parts[2])
    else:
        await websocket.close()

async def main():
    async with websockets.serve(
        handler,
        "0.0.0.0",
        443,
        ssl=ssl_context,
        ping_interval=20,
        ping_timeout=20,
    ):
        print("WSS stream server running on :443")
        await asyncio.Future()

asyncio.run(main())