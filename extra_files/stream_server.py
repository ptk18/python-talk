import asyncio
import websockets

publishers = set()
subscribers = {} #set()

async def publish(websocket, sub_path = ''):
    publishers.add(websocket)
    try:
        async for message in websocket:
            print(f"Received message for {sub_path}, size: {len(message)} bytes")
            if sub_path in subscribers:
                print(f"Broadcasting to {len(subscribers[sub_path])} subscribers")
                websockets_list = [s.send(message) for s in subscribers[sub_path]]
                if websockets_list:
                    results = await asyncio.gather(*websockets_list, return_exceptions=True)
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            print(f"Error sending to subscriber {i}: {result}")
            else:
                print(f"No subscribers for {sub_path}")
    except websockets.ConnectionClosed as e:
        print(f"Publisher connection closed: {e}")
    except Exception as e:
        print(f"Error in publish: {e}")
    finally:
        publishers.remove(websocket)

async def subscribe(websocket, sub_path = ''):
    if sub_path not in subscribers:
        subscribers[sub_path] = set()
    subscribers[sub_path].add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        subscribers[sub_path].remove(websocket)

# async def handler(websocket, path):
async def handler(websocket):
    path = websocket.request.path
    path_S = path.split("/")
    print("got ", path_S)
    if path_S[1] == "publish":
        await publish(websocket, path_S[2])
    elif path_S[1] == "subscribe":
        await subscribe(websocket, path_S[2])
    else:
        await websocket.close()

async def main():
    async with websockets.serve(handler, "0.0.0.0", 5050):
        await asyncio.Future()  # run forever

asyncio.run(main())
